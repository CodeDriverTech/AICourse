"""
工具模块

包含所有Agent使用的工具函数。
"""

from .search_tools import search_papers
from .download_tools import download_paper
from .feedback_tools import ask_human_feedback

# 工具注册
tools = [search_papers, download_paper, ask_human_feedback]
tools_dict = {tool.name: tool for tool in tools}

__all__ = [
    "search_papers",
    "download_paper", 
    "ask_human_feedback",
    "tools",
    "tools_dict",
]
