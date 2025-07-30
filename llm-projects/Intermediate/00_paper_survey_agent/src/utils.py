"""
辅助函数
"""

from langchain_core.tools import BaseTool


def format_tools_description(tools: list[BaseTool]) -> str:
    """格式化工具描述"""
    return "\n\n".join([f"- {tool.name}: {tool.description}\n输入参数: {tool.args}" for tool in tools])
