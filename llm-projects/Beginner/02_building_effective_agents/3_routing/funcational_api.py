"""
路由会对输入进行分类，并将其定向到后续任务。

路由会对输入进行分类，并将其定向到专门的后续任务。此工作流程允许分离关注点，并构建更专业的提示。如果没有此工作流程，针对一种输入进行优化可能会损害其他输入的性能。
何时使用此工作流程：路由非常适合复杂任务，其中存在不同的类别，最好分别处理，并且可以通过 LLM 或更传统的分类模型/算法准确处理分类。
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

from langgraph.func import entrypoint, task
from typing_extensions import Literal
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage

# Schema for structured output to use as routing logic
class Route(BaseModel):
    step: Literal["poem", "story", "joke"] = Field(
        None, description="The next step in the routing process"
    )

# Augment the LLM with schema for structured output
router = llm.with_structured_output(Route)


@task
def llm_call_1(input_: str):
    """Write a story"""

    result = llm.invoke(input_)
    return result.content

@task
def llm_call_2(input_: str):
    """Write a joke"""

    result = llm.invoke(input_)
    return result.content

@task
def llm_call_3(input_: str):
    """Write a poem"""

    result = llm.invoke(input_)
    return result.content

def llm_call_router(input_: str):
    """Route the input to the appropriate node"""

    # Run the augmented LLM with structured output to serve as routing logic
    decision = router.invoke(
        [
            SystemMessage(
                content="Route the input to story, joke, or poem based on the user's request."
            ),
            HumanMessage(content=input_),
        ]
    )

    return decision.step

# Create workflow
@entrypoint()
def routing_workflow(input_: str):
    next_step = llm_call_router(input_)
    if next_step == "story":
        llm_call = llm_call_1
    elif next_step == "joke":
        llm_call = llm_call_2
    elif next_step == "poem":
        llm_call = llm_call_3
    
    return llm_call(input_).result()

# Invoke
for step in routing_workflow.stream("Write me a joke about cats", stream_mode="updates"):
    print(step)
    print("\n--- --- ---\n")
# Output
"""
{'llm_call_2': 'Why did the cat sit on the computer?  \n\nBecause it wanted to keep an eye on the mouse!'}

--- --- ---

{'routing_workflow': 'Why did the cat sit on the computer?  \n\nBecause it wanted to keep an eye on the mouse!'}

--- --- ---

"""