"""
INSTALLATION:
    %pip install -U langchain-tavily
"""

from dotenv import load_dotenv
import os

load_dotenv()
base_url = os.getenv("OPENAI_BASE_URL")
api_key = os.getenv("OPENAI_API_KEY")
tavily_api_key = os.getenv("TAVILY_API_KEY")

from typing import Annotated

from langchain_tavily import TavilySearch
from langchain_core.messages import BaseMessage
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain.chat_models import init_chat_model

class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

tool = TavilySearch(max_results=2)
tools = [tool]
llm = init_chat_model(
    "openai:gpt-4.1-nano-2025-04-14",
    configurable_fields="any",
    config_prefix="foo",
    temperature=0.7
)
llm_with_tools = llm.bind_tools(tools)

config = {"configurable": {"thread_id": "a2", "foo_base_url": base_url, "foo_api_key": api_key}}

def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"], config=config)]}

graph_builder.add_node("chatbot", chatbot)

tool_node = ToolNode(tools=[tool])
graph_builder.add_node("tools", tool_node)

graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
)

graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")
graph = graph_builder.compile()