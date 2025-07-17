"""
INSTALLATION:
    %pip install -q ipython
"""
from dotenv import load_dotenv
import os

load_dotenv()
base_url = os.getenv("OPENAI_BASE_URL")
api_key = os.getenv("OPENAI_API_KEY")

# 1. 定义 LLM
from langchain.chat_models import init_chat_model

llm = init_chat_model(
    "openai:gpt-4.1-nano-2025-04-14",
    temperature=1.0,
    base_url=base_url,
    api_key=api_key
)
config = {"configurable": {"thread_id": "a1"}}

# 2. 创建 StateGraph
from typing import Annotated
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
# 额外: 添加了 memory
from langgraph.checkpoint.memory import MemorySaver
memory = MemorySaver()

class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)


# 3. 添加节点
def chatbot(state: State):
    return {"messages": llm.invoke(state["messages"], config=config)}

graph_builder.add_node("chatbot", chatbot)

# 4. 添加 `entry` 和 `exit`
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

# 5. 编译
# 额外: 如果添加memory的话，在编译的时候需要提供检查点
graph = graph_builder.compile(checkpointer=memory)

# 6. 可视化 Graph
from IPython.display import Image, display
display(Image(graph.get_graph().draw_mermaid_png()))
mermaid_code = graph.get_graph().draw_mermaid()
with open("simple_conversational_agent.mmd", "w") as f:
    f.write(mermaid_code)
print("Mermaid code saved as simple_conversational_agent.mmd")

# 7. 调用
# 额外: 如果添加memory的话，stream的时候需要提供config作为第二个参数
def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}, config):
        for value in event.values():
            print(value)
            print("Assistant:", value["messages"].content)

# 交互
while True:
    try:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        stream_graph_updates(user_input)
    except KeyboardInterrupt:
        user_input = "What do you know about LangGraph?"
        print("User: " + user_input)
        stream_graph_updates(user_input)
        break
