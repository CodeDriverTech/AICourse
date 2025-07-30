"""
节点定义
"""

from typing import Dict, Any, Literal
from datetime import datetime
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage, HumanMessage

from ..config import (
    llm, decision_making_prompt, planning_prompt, agent_prompt, judge_prompt,
    survey_outline_prompt, survey_title_abstract_prompt, MAX_SURVEY_REFERENCE, SAVE_DIR
)
from ..models import AgentState, DecisionMakingOutput, JudgeOutput, TypeEnum, SurveySections
from ..tools import tools, tools_dict
from ..utils import format_tools_description
from ..services.paper_service import PaperService
from ..services.survey_service import SurveyService

decision_making_llm = llm.with_structured_output(DecisionMakingOutput)
agent_llm = llm.bind_tools(tools)
judge_llm = llm.with_structured_output(JudgeOutput)

# 初始化服务
paper_service = PaperService()
survey_service = SurveyService()


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
        return "end"


def generate_survey_agent(state: AgentState) -> Dict[str, Any]:
    """生成论文综述节点：基于协调者-工作者模式生成高质量综述报告（基本实现思路可以参考 `./llm-projects/Beginner/02_building_effective_agents/4_orchestrator-worker/graph_api.py`）"""
    try:
        # 1. 提取原始用户查询（综述主题）
        original_query = state["messages"][0].content
        print(f"🎯 开始生成综述报告，主题：{original_query}")
        
        # 2. 从保存目录中提取已下载的论文信息
        papers_info = paper_service.extract_paper_content_from_save_dir()
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
            summary = paper_service.summarize_paper_content(paper['content'], original_query)
            paper_summaries.append(summary)
        
        # 4. 生成综述大纲
        planner_llm = llm.with_structured_output(SurveySections)
        outline_prompt_text = survey_outline_prompt.format(
            topic=original_query,
            paper_summaries=chr(10).join([f"论文{i+1}: {summary.title} - {summary.abstract[:200]}..." for i, summary in enumerate(paper_summaries)])
        )
        
        survey_outline = planner_llm.invoke([HumanMessage(content=outline_prompt_text)])
        print(f"📋 生成了 {len(survey_outline.sections)} 个综述章节:")
        for i, section in enumerate(survey_outline.sections):
            print(f"  {i+1}. {section.title}")

        print("✍️ 工作者阶段：并行生成各章节详细内容...")
        
        # 并行生成章节内容
        completed_sections = survey_service.parallel_generate_sections(
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
{full_survey[:10000]}...

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
        if state["type"] == TypeEnum.report:
            state["messages"][0].content = f"{state['messages'][0].content}".replace(f"查询 {MAX_SURVEY_REFERENCE} 篇能够辅助论文主题", "").replace("的相关可引用论文。\n无论论文主题是什么，你的任务仅有查询。", "")
            return "generate_survey"
        return "end"
    else:
        return "planning"
