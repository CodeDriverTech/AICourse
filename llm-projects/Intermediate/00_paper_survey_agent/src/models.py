"""
数据模型定义
"""

from enum import Enum
from typing import Optional, Sequence, Annotated
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class SearchPapersInput(BaseModel):
    """搜索论文的输入模型"""
    query: str = Field(description="在选定档案中搜索的查询")
    max_papers: int = Field(
        description="返回的最大论文数量。默认为1，但如果需要更全面的搜索，可以增加到100",
        default=1, ge=1, le=100
    )


class TypeEnum(str, Enum):
    """用户查询类型"""
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
