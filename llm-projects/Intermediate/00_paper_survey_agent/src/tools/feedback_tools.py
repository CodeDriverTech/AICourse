"""
反馈工具模块
"""

from langchain_core.tools import tool


@tool("ask-human-feedback")
def ask_human_feedback(question: str) -> str:
    """询问人类反馈。遇到意外错误时应调用此工具"""
    return input(f"[人类反馈请求] {question}: ")
