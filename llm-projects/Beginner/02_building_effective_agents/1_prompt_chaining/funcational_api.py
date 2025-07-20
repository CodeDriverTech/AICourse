"""
在提示链中，每个 LLM 调用都会处理前一个调用的输出。

提示链将任务分解为一系列步骤，其中每个 LLM 调用都会处理前一个步骤的输出。您可以在任何中间步骤上添加程序化检查，以确保流程仍在正常进行。
何时使用此工作流程：此工作流程非常适合任务可以轻松清晰地分解为固定子任务的情况。其主要目标是通过简化每次 LLM 调用，以降低延迟并提高准确率。
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

# Tasks
@task
def generate_joke(topic: str):
    """First LLM call to generate initial joke"""

    msg = llm.invoke(f"Write a short joke about {topic}")
    return msg.content

def check_punchline(joke: str):
    """Gate function to check if the joke has a punchline"""

    # Simple check - does the joke contain "?" or "!"
    if "?" in joke or "!" in joke:
        return "Pass"
    return "Fail"

@task
def improve_joke(joke: str):
    """Second LLM call to improve the joke"""

    msg = llm.invoke(f"Make this joke funnier by adding wordplay: {joke}")
    return msg.content

@task
def polish_joke(joke: str):
    """Third LLM call for final polish"""

    msg = llm.invoke(f"Add a surprising twist to this joke: {joke}")
    return msg.content

@entrypoint()
def prompt_chaining_workflow(topic: str):
    original_joke = generate_joke(topic).result()
    if check_punchline(original_joke) == "Pass":
        return original_joke
    improved_joke = improve_joke(original_joke).result()
    final_joke = polish_joke(improved_joke).result()
    return final_joke

# Invoke
for step in prompt_chaining_workflow.stream("cats", stream_mode="updates"):
    print(step)
    print("\n--- --- ---\n")
# Output:
"""
{'generate_joke': 'Why did the cat sit on the computer?  \n\nBecause it wanted to keep an eye on the mouse!'}

--- --- ---

{'prompt_chaining_workflow': 'Why did the cat sit on the computer?  \n\nBecause it wanted to keep an eye on the mouse!'}

--- --- ---

"""