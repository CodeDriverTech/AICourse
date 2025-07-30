"""
工作流定义
"""

from langgraph.graph import StateGraph, END

from ..models import AgentState
from .nodes import (
    decision_making_node,
    router,
    planning_node,
    tools_node,
    agent_node,
    should_continue,
    generate_survey_agent,
    judge_node,
    final_answer_router
)


def create_workflow() -> StateGraph:
    """创建并配置工作流图"""
    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("decision_making", decision_making_node)
    workflow.add_node("planning", planning_node)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tools_node)
    workflow.add_node("judge", judge_node)
    workflow.add_node("generate_survey", generate_survey_agent)

    # 添加边
    workflow.add_conditional_edges(
        "decision_making",
        router,
        {"planning": "planning", "end": END}
    )

    workflow.add_edge("planning", "agent")

    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {"continue": "tools", "end": "judge"}
    )

    workflow.add_edge("tools", "agent")

    workflow.add_conditional_edges(
        "judge",
        final_answer_router,
        {"planning": "planning", "end": END, "generate_survey": "generate_survey"}
    )

    workflow.add_edge("generate_survey", END)

    # 设置入口点
    workflow.set_entry_point("decision_making")

    return workflow


# 编译工作流应用
app = create_workflow().compile()
