"""
搜索工具模块
"""

from langchain_core.tools import tool
from ..models import SearchPapersInput


@tool("search-papers", args_schema=SearchPapersInput)
def search_papers(query: str, max_papers: int = 1) -> str:
    """使用CORE API搜索科学论文
    
    示例：
    {"query": "Attention is all you need", "max_papers": 1}
    
    返回：
        找到的相关论文列表及对应的相关信息
    """
    try:
        from ..services.core_api import CoreAPIWrapper
        print(f"🔍 正在搜索论文: {query} (最多 {max_papers} 篇)")
        return CoreAPIWrapper(top_k_results=max_papers).search(query)
    except Exception as e:
        return f"执行论文搜索时出错: {e}"
