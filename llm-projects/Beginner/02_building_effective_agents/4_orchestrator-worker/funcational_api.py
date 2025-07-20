"""
使用 Orchestrator-Worker，Orchestrator 会将任务分解，并将每个子任务委托给 Worker。

在协调器-工作者工作流中，中央 LLM 动态分解任务，将其委托给工作者 LLM，并综合其结果。
何时使用此工作流程：此工作流程非常适合无法预测所需子任务的复杂任务（例如，在编码过程中，需要更改的文件数量以及每个文件的更改性质可能取决于任务本身）。虽然它在拓扑结构上与并行化类似，但其与并行化的关键区别在于灵活性——子任务并非预先定义，而是由编排器根据具体输入确定。
"""
from dotenv import load_dotenv
import os

load_dotenv()
base_url = os.getenv("OPENAI_BASE_URL")
api_key = os.getenv("OPENAI_API_KEY")

from langchain.chat_models import init_chat_model

llm = init_chat_model(
    "openai:gpt-4.1-nano-2025-04-14",
    # configurable_fields="any",
    # config_prefix="foo",
    temperature=1.0,
    base_url=base_url,
    api_key=api_key
)

from typing import List
from pydantic import BaseModel, Field
from langgraph.func import entrypoint, task
from langchain_core.messages import HumanMessage, SystemMessage

# Schema for structured output to use in planning
class Section(BaseModel):
    name: str = Field(
        description="Name for this section of the report.",
    )
    description: str = Field(
        description="Brief overview of the main topics and concepts to be covered in this section.",
    )

class Sections(BaseModel):
    sections: List[Section] = Field(
        description="Sections of the report.",
    )

# Augment the LLM with schema for structured output
planner = llm.with_structured_output(Sections)

@task
def orchestrator(topic: str):
    """Orchestrator that generates a plan for the report"""

    # Generate queries
    report_sections = planner.invoke(
        [
            SystemMessage(content="Generate a plan for the report."),
            HumanMessage(content=f"Here is the report topic: {topic}"),
        ]
    )

    return report_sections.sections

@task
def llm_call(section: Section):
    """Worker writes a section of the report"""

    # Generate section
    section = llm.invoke(
        [
            SystemMessage(
                content="Write a report section following the provided name and description. Include no preamble for each section. Use markdown formatting."
            ),
            HumanMessage(
                content=f"Here is the section name: {section.name} and description: {section.description}"
            ),
        ]
    )

    return section.content

@task
def synthesizer(completed_sections: list[str]):
    """Synthesize full report from sections"""

    # List of completed sections
    completed_report_sections = "\n\n---\n\n".join(completed_sections)

    return completed_report_sections

@entrypoint()
def orchestrator_worker(topic: str):
    sections = orchestrator(topic).result()
    section_futures = [llm_call(section) for section in sections]
    final_report = synthesizer(
        [section_fut.result() for section_fut in section_futures]
    ).result()
    return final_report

# Invoke
report = orchestrator_worker.invoke("Create a report on LLM scaling laws")
print(report)
# from IPython.display import Markdown
# Markdown(report)