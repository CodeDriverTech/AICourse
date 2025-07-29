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
from typing import Optional, Sequence, Annotated, ClassVar, Literal, Dict, Any
from typing_extensions import TypedDict
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import pdfplumber
import requests

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
            agent_prompt, judge_prompt
        )
    else:
        from src.prompt.prompt_cn import (
            decision_making_prompt, planning_prompt, 
            agent_prompt, judge_prompt
        )
    return decision_making_prompt, planning_prompt, agent_prompt, judge_prompt

decision_making_prompt, planning_prompt, agent_prompt, judge_prompt = load_prompts(LANGUAGE)

# 全局配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
CORE_API_KEY = os.getenv("CORE_API_KEY")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL")
TEMPERATURE = os.getenv("TEMPERATURE")
MAX_RESEARCH_PAPERS = os.getenv("MAX_RESEARCH_PAPERS")

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
                return response.json()
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise Exception(f"CORE API请求失败: {e}")

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
                f"* 论文链接: {result.get('sourceFulltextUrls') or result.get('downloadUrl', '')}"
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
                # TODO：保存PDF文件到运行目录
                with pdfplumber.open(pdf_file) as pdf:
                    text = ""
                    for page in pdf.pages:
                        text += page.extract_text() + "\n"
                return text
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
            state["messages"][-1].content = f"查询 {MAX_RESEARCH_PAPERS} 篇能够辅助论文主题 {state['messages'][-1].content} 的相关可引用论文。\n无论论文主题是什么，你的任务仅有查询。"
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
        # if state["type"] == TypeEnum.report:
        #     return "generate_survey"
        return "end"

# def generate_survey_node(state: AgentState) -> Dict[str, Any]:
#     """生成综述节点：根据工具调用结果生成综述"""
#     pass

def judge_node(state: AgentState) -> Dict[str, Any]:
    """判断节点：让LLM评估自己最终答案的质量"""
    num_feedback_requests = state.get("num_feedback_requests", 0)
    
    # 如果LLM两次未能提供良好答案，则结束执行
    if num_feedback_requests >= 2:
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
# workflow.add_node("generate_survey", generate_survey_node)

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
workflow.add_edge("generate_survey", "judge")
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue": "tools",
        # "generate_survey": "generate_survey",
        "end": "judge",
    },
)
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
