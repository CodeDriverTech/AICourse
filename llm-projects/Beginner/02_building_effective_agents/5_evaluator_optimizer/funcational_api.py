"""
在评估器-优化器工作流中，一个 LLM 调用生成响应，而另一个调用在循环中提供评估和反馈：

何时使用此工作流程：当我们拥有清晰的评估标准，并且迭代改进能够提供可衡量的价值时，此工作流程尤其有效。良好契合的两个标志是：首先，当人类清晰地表达反馈时，LLM 的答案可以得到显著的改进；其次，LLM 能够提供这样的反馈。这类似于人类作家在撰写一篇精良文档时可能经历的迭代写作过程。
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

from typing_extensions import Literal
from pydantic import BaseModel, Field
from langgraph.func import entrypoint, task

# Schema for structured output to use in evaluation
class Feedback(BaseModel):
    grade: Literal["funny", "not funny"] = Field(
        description="Decide if the joke is funny or not.",
    )
    feedback: str = Field(
        description="If the joke is not funny, provide feedback on how to improve it.",
    )


# Augment the LLM with schema for structured output
evaluator = llm.with_structured_output(Feedback)


# Nodes
@task
def llm_call_generator(topic: str, feedback: Feedback):
    """LLM generates a joke"""
    if feedback:
        msg = llm.invoke(
            f"Write a joke about {topic} but take into account the feedback: {feedback}"
        )
    else:
        msg = llm.invoke(f"Write a joke about {topic}")
    return msg.content


@task
def llm_call_evaluator(joke: str):
    """LLM evaluates the joke"""
    feedback = evaluator.invoke(f"Grade the joke {joke}")
    return feedback


@entrypoint()
def optimizer_workflow(topic: str):
    feedback = None
    while True:
        joke = llm_call_generator(topic, feedback).result()
        feedback = llm_call_evaluator(joke).result()
        if feedback.grade == "funny":
            break

    return joke

# Invoke
for step in optimizer_workflow.stream("Cats", stream_mode="updates"):
    print(step)
    print("\n--- --- ---\n")
# Output:
"""
{'llm_call_generator': 'Why did the cat sit on the computer?  \n\nBecause it wanted to keep an eye on the mouse!'}

--- --- ---

{'llm_call_evaluator': Feedback(grade='funny', feedback="The joke plays on the double meaning of 'mouse' as both a computer device and a small animal, which is clever. To make it even funnier, consider adding a bit more context or a punchline that surprises the listener. For example: 'Because it wanted to catch the mouse, literally and figuratively!'")}

--- --- ---

{'optimizer_workflow': 'Why did the cat sit on the computer?  \n\nBecause it wanted to keep an eye on the mouse!'}

--- --- ---

"""