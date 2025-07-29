#!/usr/bin/env python3
"""
科学论文调研智能助手 - 单文件可运行版本

基于LangGraph构建的科学论文调研和分析工具，支持通过CORE API搜索论文、
下载PDF文件、提取内容并生成智能分析报告。

使用方法：
    python run.py
    python run.py --L cn    # 使用中文提示词
    python run.py --Language en  # 使用英文提示词

环境要求：
    - OPENAI_API_KEY: OpenAI API密钥
    - OPENAI_BASE_URL: OpenAI API基础URL
    - DEFAULT_MODEL: 默认模型
    - CORE_API_KEY: CORE API密钥 (可在 https://core.ac.uk/services/api#form 申请)
    - TEMPERATURE: 温度参数
"""

from enum import Enum
import os
import io
import time
import urllib3
import argparse
from datetime import datetime
from typing import Optional, Sequence, Annotated, ClassVar, Literal, Dict, Any
from typing_extensions import TypedDict
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import pdfplumber
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool, BaseTool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

load_dotenv()

def parse_args():
    parser = argparse.ArgumentParser(description='科学论文调研智能助手')
    parser.add_argument('-L', '--Language', 
                       choices=['cn', 'en'], 
                       default='cn',
                       help='提示词语言 (cn: 中文, en: 英文)')
    return parser.parse_args()

args = parse_args()
LANGUAGE = args.Language

# 动态导入提示词
def load_prompts(language='cn'):
    """根据语言动态加载提示词"""
    if language == 'en':
        from src.prompt.prompt_en import (
            decision_making_prompt, planning_prompt, 
            agent_prompt, judge_prompt,
            paper_analysis_prompt, survey_outline_prompt,
            survey_section_prompt, survey_title_abstract_prompt
        )
    else:
        from src.prompt.prompt_cn import (
            decision_making_prompt, planning_prompt, 
            agent_prompt, judge_prompt,
            paper_analysis_prompt, survey_outline_prompt,
            survey_section_prompt, survey_title_abstract_prompt
        )
    return (decision_making_prompt, planning_prompt, agent_prompt, judge_prompt,
            paper_analysis_prompt, survey_outline_prompt,
            survey_section_prompt, survey_title_abstract_prompt)

(decision_making_prompt, planning_prompt, agent_prompt, judge_prompt,
 paper_analysis_prompt, survey_outline_prompt,
 survey_section_prompt, survey_title_abstract_prompt) = load_prompts(LANGUAGE)

# 全局配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
CORE_API_KEY = os.getenv("CORE_API_KEY")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL")
TEMPERATURE = os.getenv("TEMPERATURE")
MAX_SURVEY_REFERENCE = os.getenv("MAX_SURVEY_REFERENCE")
SAVE_DIR = os.getenv("SAVE_DIR")

if not OPENAI_API_KEY:
    raise ValueError("请设置OPENAI_API_KEY环境变量")
if not CORE_API_KEY:
    raise ValueError("请设置CORE_API_KEY环境变量")

# 初始化LLM
llm = init_chat_model(
    f"openai:{DEFAULT_MODEL}",
    temperature=TEMPERATURE,
    base_url=OPENAI_BASE_URL,
    api_key=OPENAI_API_KEY
)

# ========================= 数据模型定义 =========================

class SearchPapersInput(BaseModel):
    """搜索论文的输入模型"""
    query: str = Field(description="在选定档案中搜索的查询")
    max_papers: int = Field(
        description="返回的最大论文数量。默认为1，但如果需要更全面的搜索，可以增加到100",
        default=1, ge=1, le=100
    )

class TypeEnum(str, Enum):
    usual = "usual"         # 日常问答
    search = "search"       # 搜索论文
    download = "download"   # 下载论文
    analyze = "analyze"     # 分析论文
    report = "report"       # 生成综述 / 报告

class DecisionMakingOutput(BaseModel):
    """决策节点的输出模型"""
    requires_research: bool = Field(description="用户查询是否需要研究")
    type: TypeEnum = Field(description="用户查询类型")
    answer: Optional[str] = Field(
        default=None, 
        description="用户查询的答案。如果需要研究则为None，否则为直接答案"
    )

class JudgeOutput(BaseModel):
    """判断节点的输出模型"""
    is_good_answer: bool = Field(description="答案是否良好")
    feedback: Optional[str] = Field(
        default=None, 
        description="关于答案不好的详细反馈。如果答案良好则为None"
    )

class AgentState(TypedDict):
    """状态图"""
    requires_research: bool
    type: TypeEnum
    num_feedback_requests: int
    is_good_answer: bool
    messages: Annotated[Sequence[BaseMessage], add_messages]

# ========================= CORE API封装 =========================

class CoreAPIWrapper(BaseModel):
    """CORE API的简单封装"""
    base_url: ClassVar[str] = "https://api.core.ac.uk/v3"
    api_key: ClassVar[str] = CORE_API_KEY
    top_k_results: int = 1

    def _get_search_response(self, query: str) -> Dict[str, Any]:
        """获取搜索响应"""
        url = f"{self.base_url}/search/works"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "q": query,
            "limit": self.top_k_results,
            "offset": 0,
            "scroll": False
        }
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(url, json=data, headers=headers, timeout=30)
                response.raise_for_status()
                original_output = response.json()
                
                # 并行下载论文
                download_urls = [result.get("downloadUrl") for result in original_output.get("results", []) if result.get("downloadUrl")]
                if download_urls:
                    print(f"🚀 开始并行下载 {len(download_urls)} 篇论文...")
                    self._parallel_download_papers(download_urls)
                
                return original_output
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise Exception(f"CORE API请求失败: {e}")
    
    def _parallel_download_papers(self, download_urls: list[str], max_workers: int = 3) -> None:
        """
        并行下载多篇论文
        
        Args:
            download_urls: 下载链接列表
            max_workers: 最大并发工作线程数，默认为3
        """
        def download_single_paper(url: str) -> tuple[str, bool, str]:
            """下载单篇论文的包装函数"""
            try:
                result = download_paper(url)
                return url, True, result
            except Exception as e:
                return url, False, str(e)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(download_single_paper, url): url for url in download_urls}
            
            completed_count = 0
            failed_count = 0
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    original_url, success, result = future.result()
                    if success:
                        completed_count += 1
                        print(f"  ✅ 下载完成 ({completed_count}/{len(download_urls)}): {os.path.basename(original_url)}")
                    else:
                        failed_count += 1
                        print(f"  ❌ 下载失败 ({failed_count}/{len(download_urls)}): {result}")
                except Exception as e:
                    failed_count += 1
                    print(f"  ❌ 下载异常 ({failed_count}/{len(download_urls)}): {e}")
            
            print(f"📊 下载统计: 成功 {completed_count} 篇, 失败 {failed_count} 篇")

    def search(self, query: str) -> str:
        """搜索论文"""
        response = self._get_search_response(query)
        results = response.get("results", [])
        if not results:
            return "未找到相关结果"

        # 格式化结果
        docs = []
        for result in results:
            published_date_str = result.get('publishedDate') or result.get('yearPublished', '')
            authors_str = ' and '.join([item['name'] for item in result.get('authors', [])])
            docs.append((
                f"* ID: {result.get('id', '')}\n"
                f"* 标题: {result.get('title', '')}\n"
                f"* 发表日期: {published_date_str}\n"
                f"* 作者: {authors_str}\n"
                f"* 摘要: {result.get('abstract', '')}\n"
                f"* 论文下载链接: {result.get('downloadUrl') or result.get('sourceFulltextUrls', '')}"
            ))
        return "\n-----\n".join(docs)

# ========================= 工具定义 =========================

@tool("search-papers", args_schema=SearchPapersInput)
def search_papers(query: str, max_papers: int = 1) -> str:
    """使用CORE API搜索科学论文
    
    示例：
    {"query": "Attention is all you need", "max_papers": 1}
    
    返回：
        找到的相关论文列表及对应的相关信息
    """
    try:
        print(f"🔍 正在搜索论文: {query} (最多 {max_papers} 篇)")
        return CoreAPIWrapper(top_k_results=max_papers).search(query)
    except Exception as e:
        return f"执行论文搜索时出错: {e}"

@tool("download-paper")
def download_paper(url: str) -> str:
    """从给定URL下载特定科学论文（若只给定论文标题，请先使用 `search_papers` 工具进行查询论文，获取下载URL）
    
    示例：
    {"url": "https://sample.pdf"}
    
    返回：
        论文内容
    """
    try:
        http = urllib3.PoolManager(cert_reqs='CERT_NONE')
        
        # 模拟浏览器请求头避免403错误
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        
        max_retries = 5
        for attempt in range(max_retries):
            response = http.request('GET', url, headers=headers)
            if 200 <= response.status < 300:
                pdf_file = io.BytesIO(response.data)

                save_dir = SAVE_DIR
                os.makedirs(save_dir, exist_ok=True)

                import re
                from urllib.parse import urlparse

                parsed_url = urlparse(url)
                filename = os.path.basename(parsed_url.path)
                if not filename.endswith('.pdf'):
                    # 如果无法从URL获取文件名，使用时间戳
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"paper_{timestamp}.pdf"
                
                # 移除不安全字符
                filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
                filepath = os.path.join(save_dir, filename)

                # 保存至本地
                with open(filepath, 'wb') as f:
                    f.write(response.data)
                print(f"📄 PDF文件已保存到: {filepath}")
                
                with pdfplumber.open(pdf_file) as pdf:
                    text = ""
                    for page in pdf.pages:
                        text += page.extract_text() + "\n"
                return f"📄 PDF文件已保存到: {filepath}\n论文内容: {text}"
            elif attempt < max_retries - 1:
                time.sleep(2 ** (attempt + 2))
            else:
                raise Exception(f"下载论文时收到非2xx状态码: {response.status}")
    except Exception as e:
        return f"下载论文时出错: {e}"

@tool("ask-human-feedback")
def ask_human_feedback(question: str) -> str:
    """询问人类反馈。遇到意外错误时应调用此工具"""
    return input(f"[人类反馈请求] {question}: ")

tools = [search_papers, download_paper, ask_human_feedback]
tools_dict = {tool.name: tool for tool in tools}

# ========================= 辅助函数 =========================

def format_tools_description(tools: list[BaseTool]) -> str:
    """格式化工具描述"""
    return "\n\n".join([f"- {tool.name}: {tool.description}\n输入参数: {tool.args}" for tool in tools])

# ========================= 节点定义 =========================

# 初始化LLM实例
decision_making_llm = llm.with_structured_output(DecisionMakingOutput)
agent_llm = llm.bind_tools(tools)
judge_llm = llm.with_structured_output(JudgeOutput)

def decision_making_node(state: AgentState) -> Dict[str, Any]:
    """决策节点：根据用户查询决定是否需要研究"""
    system_prompt = SystemMessage(content=decision_making_prompt)
    response: DecisionMakingOutput = decision_making_llm.invoke([system_prompt] + state["messages"])
    
    output = {"requires_research": response.requires_research, "type": response.type}
    if response.answer:
        output["messages"] = [AIMessage(content=response.answer)]
    return output

def router(state: AgentState) -> Literal["planning", "end"]:
    """路由器：将用户查询引导到适当的工作流分支"""
    if state["requires_research"]:
        # print(state["type"]) # TypeEnum.search
        if state["type"] == TypeEnum.report:
            state["messages"][-1].content = f"查询 {MAX_SURVEY_REFERENCE} 篇能够辅助论文主题 {state['messages'][-1].content} 的相关可引用论文。\n无论论文主题是什么，你的任务仅有查询。"
        return "planning"
    else:
        return "end"

def planning_node(state: AgentState) -> Dict[str, Any]:
    """规划节点：创建逐步计划来回答用户查询"""
    system_prompt = SystemMessage(content=planning_prompt.format(tools=format_tools_description(tools)))
    response = llm.invoke([system_prompt] + state["messages"])
    return {"messages": [response]}

def tools_node(state: AgentState) -> Dict[str, Any]:
    """工具节点：基于计划执行工具"""
    outputs = []
    for tool_call in state["messages"][-1].tool_calls:
        tool_result = tools_dict[tool_call["name"]].invoke(tool_call["args"])
        outputs.append(
            ToolMessage(
                content=str(tool_result),
                name=tool_call["name"],
                tool_call_id=tool_call["id"],
            )
        )
    return {"messages": outputs}

def agent_node(state: AgentState) -> Dict[str, Any]:
    """智能助手节点：使用带工具的LLM回答用户查询"""
    system_prompt = SystemMessage(content=agent_prompt)
    response = agent_llm.invoke([system_prompt] + state["messages"])
    return {"messages": [response]}

def should_continue(state: AgentState) -> Literal["continue", "end"]:
    """检查智能助手是否应该继续或结束"""
    messages = state["messages"]
    last_message = messages[-1]
    
    # 如果没有工具调用，结束执行
    if last_message.tool_calls:
        return "continue"
    else:
        if state["type"] == TypeEnum.report:
            state["messages"][0].content = f"{state['messages'][0].content}".replace(f"查询 {MAX_SURVEY_REFERENCE} 篇能够辅助论文主题", "").replace("的相关可引用论文。\n无论论文主题是什么，你的任务仅有查询。", "")
            return "generate_survey"
        return "end"

# ========================= 综述生成相关模型 =========================

class SurveySection(BaseModel):
    """综述章节模型"""
    title: str = Field(description="章节标题")
    description: str = Field(description="章节描述和要覆盖的主要内容")
    priority: int = Field(description="章节优先级 (1-5, 5为最高)", default=3)

class SurveySections(BaseModel):
    """综述章节列表模型"""
    sections: list[SurveySection] = Field(description="综述的所有章节")

class PaperSummary(BaseModel):
    """论文摘要模型"""
    title: str = Field(description="论文标题")
    abstract: str = Field(description="论文摘要")
    key_contributions: list[str] = Field(description="论文的关键贡献点")
    methodology: str = Field(description="研究方法")
    limitations: str = Field(description="研究局限性")
    relevance_score: int = Field(description="与综述主题的相关性评分 (1-10)", default=5)

# ========================= PDF批量读取工具 =========================

def extract_paper_content_from_save_dir() -> list[dict]:
    """从保存目录中提取已下载的论文信息"""
    papers_info = []

    if not SAVE_DIR or not os.path.exists(SAVE_DIR):
        print(f"⚠️ 保存目录 {SAVE_DIR} 不存在")
        return papers_info

    try:
        for filename in os.listdir(SAVE_DIR):
            if filename.lower().endswith('.pdf'):
                filepath = os.path.join(SAVE_DIR, filename)
                print(f"📄 读取PDF文件: {filename}")
                
                try:
                    with pdfplumber.open(filepath) as pdf:
                        text_content = ""
                        for page in pdf.pages:
                            page_text = page.extract_text()
                            if page_text:
                                text_content += page_text + "\n"
                        
                        if text_content.strip():
                            papers_info.append({
                                'filepath': filepath,
                                'filename': filename,
                                'content': text_content.strip()
                            })
                            print(f"  ✅ 成功读取，内容长度: {len(text_content)} 字符")
                        else:
                            print(f"  ⚠️ PDF文件 {filename} 内容为空")
                            
                except Exception as e:
                    print(f"  ❌ 读取PDF文件 {filename} 失败: {e}")
                    
    except Exception as e:
        print(f"❌ 遍历保存目录失败: {e}")
    
    return papers_info

def summarize_paper_content(paper_content: str, topic: str) -> PaperSummary:
    """使用LLM总结论文内容"""
    summarize_llm = llm.with_structured_output(PaperSummary)

    prompt = paper_analysis_prompt.format(
        topic=topic,
        paper_content=paper_content[:4000]
    )
    
    try:
        summary = summarize_llm.invoke([HumanMessage(content=prompt)])
        return summary
    except Exception as e:
        # 如果结构化输出失败，返回基本信息
        return PaperSummary(
            title="未能提取标题",
            abstract="论文内容解析失败",
            key_contributions=["解析失败"],
            methodology="未知",
            limitations="未知",
            relevance_score=1
        )

# ========================= 综述生成核心逻辑 =========================

def _parallel_generate_sections(sections: list, topic: str, paper_summaries: list, max_workers: int = 2) -> list[str]:
    """
    并行生成综述章节内容，保证章节顺序
    
    Args:
        sections: 章节列表
        topic: 综述主题
        paper_summaries: 论文摘要列表
        max_workers: 最大并发工作线程数，默认为2（避免API限制）
    
    Returns:
        按原始顺序排列的完整章节内容列表
    """
    def generate_single_section(section_data: tuple) -> tuple[int, str]:
        """生成单个章节内容的包装函数"""
        index, section = section_data
        try:
            print(f"  📝 开始生成第 {index+1} 章：{section.title}")
            
            section_prompt_text = survey_section_prompt.format(
                section_title=section.title,
                section_description=section.description,
                topic=topic,
                paper_info=chr(10).join([f"论文{j+1}: {summary.title}\n关键贡献: {', '.join(summary.key_contributions)}\n方法: {summary.methodology}\n" for j, summary in enumerate(paper_summaries)])
            )
            
            section_content = llm.invoke([HumanMessage(content=section_prompt_text)])
            completed_section = f"## {section.title}\n\n{section_content.content}"
            
            print(f"  ✅ 完成第 {index+1} 章：{section.title}")
            return index, completed_section
            
        except Exception as e:
            print(f"  ❌ 生成第 {index+1} 章失败：{e}")
            return index, f"## {section.title}\n\n生成失败：{str(e)}"
    
    # 创建带索引的章节列表
    indexed_sections = [(i, section) for i, section in enumerate(sections)]
    completed_sections = [None] * len(sections)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_index = {executor.submit(generate_single_section, section_data): section_data[0] 
                          for section_data in indexed_sections}
        
        completed_count = 0

        for future in as_completed(future_to_index):
            index = future_to_index[future]
            try:
                section_index, section_content = future.result()
                completed_sections[section_index] = section_content
                completed_count += 1
                print(f"    🎯 章节生成进度: {completed_count}/{len(sections)}")
            except Exception as e:
                print(f"    ❌ 处理第 {index+1} 章结果时出错：{e}")
                completed_sections[index] = f"## 第{index+1}章\n\n生成异常：{str(e)}"
    
    print(f"📊 章节生成统计: 完成 {len([s for s in completed_sections if s])} / {len(sections)} 章")

    return [section for section in completed_sections if section]

def generate_survey_agent(state: AgentState) -> Dict[str, Any]:
    """生成论文综述节点：基于协调者-工作者模式生成高质量综述报告（基本实现思路可以参考 `./llm-projects/Beginner/02_building_effective_agents/4_orchestrator-worker/graph_api.py`）"""
    try:
        # 1. 提取原始用户查询（综述主题）
        original_query = state["messages"][0].content
        print(f"🎯 开始生成综述报告，主题：{original_query}")
        
        # 2. 从保存目录中提取已下载的论文信息
        papers_info = extract_paper_content_from_save_dir()
        print(f"📚 从 {SAVE_DIR} 目录发现 {len(papers_info)} 篇已下载的论文")
        
        if not papers_info:
            return {
                "messages": [AIMessage(content="⚠️ 未找到已下载的论文，无法生成综述报告。请先搜索和下载相关论文。")]
            }
        
        # 3. 协调者阶段：分析论文并规划综述结构
        print("🧠 协调者阶段：分析论文内容并规划综述结构...")
        paper_summaries = []
        for i, paper in enumerate(papers_info):
            print(f"  📄 分析第 {i+1} 篇论文...")
            summary = summarize_paper_content(paper['content'], original_query)
            paper_summaries.append(summary)
        
        # 4. 生成综述大纲
        planner_llm = llm.with_structured_output(SurveySections)
        outline_prompt_text = survey_outline_prompt.format(
            topic=original_query,
            paper_summaries=chr(10).join([f"论文{i+1}: {summary.title} - {summary.abstract[:200]}..." for i, summary in enumerate(paper_summaries)])
        )
        
        survey_outline = planner_llm.invoke([HumanMessage(content=outline_prompt_text)])
        print(f"📋 生成了 {len(survey_outline.sections)} 个综述章节")

        print("✍️ 工作者阶段：并行生成各章节详细内容...")
        
        # 并行生成章节内容
        completed_sections = _parallel_generate_sections(
            survey_outline.sections, 
            original_query, 
            paper_summaries
        )
        
        # 6. 合成器阶段：整合所有章节生成完整综述
        print("🔗 合成器阶段：整合完整综述报告...")
        
        title_abstract_prompt_text = survey_title_abstract_prompt.format(
            topic=original_query,
            paper_count=len(paper_summaries)
        )
        
        title_abstract = llm.invoke([HumanMessage(content=title_abstract_prompt_text)])
        
        # 整合完整综述
        full_survey = f"""
{title_abstract.content}

---

{chr(10).join(completed_sections)}

---

## 参考文献

{chr(10).join([f"{i+1}. {summary.title}" for i, summary in enumerate(paper_summaries)])}

---

*本综述基于 {len(paper_summaries)} 篇相关论文生成，生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
        """
        
        # 7. 保存综述报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        survey_filename = f"survey_report_{timestamp}.md"
        
        try:
            with open(survey_filename, 'w', encoding='utf-8') as f:
                f.write(full_survey)
            print(f"💾 综述报告已保存到：{survey_filename}")
        except Exception as e:
            print(f"⚠️ 保存综述报告时出错：{e}")
        
        # 8. 返回结果
        success_message = f"""
✅ **综述报告生成完成！**

📊 **统计信息：**
- 分析论文数量：{len(paper_summaries)} 篇
- 综述章节数量：{len(survey_outline.sections)} 个
- 报告保存位置：{survey_filename}

📝 **综述预览：**
{full_survey[:1000]}...

💡 完整综述报告已保存到本地文件，您可以进一步编辑和完善。
        """
        
        return {
            "messages": [AIMessage(content=success_message)]
        }
        
    except Exception as e:
        error_message = f"❌ 综述生成过程中发生错误：{str(e)}\n\n请检查论文下载状态和网络连接。"
        return {
            "messages": [AIMessage(content=error_message)]
        }

def judge_node(state: AgentState) -> Dict[str, Any]:
    """判断节点：让LLM评估自己最终答案的质量"""
    num_feedback_requests = state.get("num_feedback_requests", 0)
    
    # 如果LLM三次未能提供良好答案，则结束执行
    if num_feedback_requests >= 3:
        return {"is_good_answer": True}
    
    system_prompt = SystemMessage(content=judge_prompt)
    response: JudgeOutput = judge_llm.invoke([system_prompt] + state["messages"])
    
    output = {
        "is_good_answer": response.is_good_answer,
        "num_feedback_requests": num_feedback_requests + 1
    }
    if response.feedback:
        output["messages"] = [AIMessage(content=response.feedback)]
    return output

def final_answer_router(state: AgentState) -> Literal["planning", "end"]:
    """最终答案路由器：结束工作流或改进答案"""
    if state["is_good_answer"]:
        return "end"
    else:
        return "planning"

# ========================= 工作流定义 =========================
# 状态图
workflow = StateGraph(AgentState)

# 节点
workflow.add_node("decision_making", decision_making_node)
workflow.add_node("planning", planning_node)
workflow.add_node("tools", tools_node)
workflow.add_node("agent", agent_node)
workflow.add_node("judge", judge_node)
# 将 Agent 作为一个独立的节点
workflow.add_node("generate_survey", generate_survey_agent)

# 边
workflow.add_edge(START, "decision_making")

# 条件边
workflow.add_conditional_edges(
    "decision_making",
    router,
    {
        "planning": "planning",
        "end": END,
    }
)
workflow.add_edge("planning", "agent")
workflow.add_edge("tools", "agent")
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue": "tools",
        "generate_survey": "generate_survey",
        "end": "judge",
    },
)
workflow.add_edge("generate_survey", "judge")
workflow.add_conditional_edges(
    "judge",
    final_answer_router,
    {
        "planning": "planning",
        "end": END,
    }
)

# 编译
app = workflow.compile()
mermaid_code = app.get_graph(xray=True).draw_mermaid()
with open("graph_visualization.mmd", "w") as f:
    f.write(mermaid_code)
print("Mermaid code saved as graph_visualization.mmd")

# ========================= 主函数 =========================

def print_stream(user_input: str):
    """打印流式输出"""
    print("=" * 50)
    print("🔬 科学论文调研助手")
    print("=" * 50)
    print(f"📝 用户输入: {user_input}")
    print("-" * 50)
    
    # 初始化状态
    initial_state = {
        "requires_research": False,
        "num_feedback_requests": 0,
        "is_good_answer": False,
        "messages": [HumanMessage(content=user_input)]
    }
    
    # 流式执行
    final_message = None
    for step in app.stream(initial_state):
        for node_name, node_output in step.items():
            print(f"🔄 执行节点: {node_name}")
            if "messages" in node_output:
                for message in node_output["messages"]:
                    if isinstance(message, AIMessage):
                        print(f"🤖 AI回答: {message.content}")
                        final_message = message
                    elif isinstance(message, ToolMessage):
                        print(f"🛠️ 工具结果: {message.name}")
                        content = message.content
                        print(f"   结果: {content}")
            print("-" * 30)
    
    print("=" * 50)
    print("✅ 处理完成")
    print("=" * 50)
    
    return final_message

def main():
    """主函数"""
    print("🎉 欢迎使用科学论文调研智能助手!")
    print("输入 'quit' 或 'exit' 退出程序")
    print("=" * 50)
    
    while True:
        try:
            user_input = input("\n请输入您的查询: ").strip()
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("👋 感谢使用！再见！")
                break
            
            if not user_input:
                print("❌ 请输入有效的查询")
                continue
            
            print_stream(user_input)
            
        except KeyboardInterrupt:
            print("\n👋 程序已中断，感谢使用！")
            break
        except Exception as e:
            print(f"❌ 发生错误: {e}")
            print("请重试或联系管理员")

if __name__ == "__main__":
    main()
