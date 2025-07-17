"""
INSTALLATION:
    %pip install -U langchain langgraph
    %pip install -qU "langchain[openai]"
    %pip install -q python-dotenv
"""
# 用于加载环境变量的库导入（.env文件）
from dotenv import load_dotenv
import os

load_dotenv()
base_url = os.getenv("OPENAI_BASE_URL")
api_key = os.getenv("OPENAI_API_KEY")

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage

model = init_chat_model(
    "openai:gpt-4.1-nano-2025-04-14", # 当然，你可以在冒号后面替换为任何你想测试的模型（嗯哼，你在学习这段代码的时候，最具性价比的模型变成哪个了呢？）
    temperature=1.0,
    base_url=base_url,
    api_key=api_key
)

# 定义一个新的 Graph
workflow = StateGraph(state_schema=MessagesState)

# 定义一个模型调用的方法
def call_moel(state: MessagesState):
    response = model.invoke(state["messages"])
    return {"messages": response}

# 在 Graph 中定义节点
workflow.add_edge(START, "model")
workflow.add_node("model", call_moel)

# 添加 Memory
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

# 创建一个 `config`，每次传递给可运行对象时都需要使用它。例如，我们想要包含一个 `thread_id`。
# 这使我们能够通过单个应用程序支持多个对话线程。
config = {"configurable": {"thread_id": "abc123"}}

# 调用
query = "Hi! I'm Rocky."
input_messages = [HumanMessage(query)]
output = app.invoke({"messages": input_messages}, config)
print(f"output: {output}")
"""
output: {'messages': [HumanMessage(content="Hi! I'm Rocky.", additional_kwargs={}, response_metadata={}, id='4e821e17-3644-43b4-922c-ced78da4085d'), AIMessage(content='Hi Rocky! Nice to meet you. How can I assist you today?', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 16, 'prompt_tokens': 12, 'total_tokens': 28, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 0}}, 'model_name': 'gpt-4.1-nano-2025-04-14', 'system_fingerprint': 'fp_68472df8fd', 'id': 'chatcmpl-Bs2Oc5KYYfXu1g8KQjte1TdqOBEm9', 'service_tier': None, 'finish_reason': 'stop', 'logprobs': None}, id='run--bfec1c94-8f05-4dbc-9eca-61e3e86b5e3d-0', usage_metadata={'input_tokens': 12, 'output_tokens': 16, 'total_tokens': 28, 'input_token_details': {'audio': 0, 'cache_read': 0}, 'output_token_details': {'audio': 0, 'reasoning': 0}})]}
"""
print(f"{output['messages'][-1].pretty_print()}")
"""
================================== Ai Message ==================================

Hi Rocky! Nice to meet you. How can I assist you today?
None
"""

query = "What is my name?"
input_messages = [HumanMessage(query)]
output = app.invoke({"messages": input_messages}, config)
print(f"output: {output}")
"""
output: {'messages': [HumanMessage(content="Hi! I'm Rocky.", additional_kwargs={}, response_metadata={}, id='4e821e17-3644-43b4-922c-ced78da4085d'), AIMessage(content='Hi Rocky! Nice to meet you. How can I assist you today?', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 16, 'prompt_tokens': 12, 'total_tokens': 28, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 0}}, 'model_name': 'gpt-4.1-nano-2025-04-14', 'system_fingerprint': 'fp_68472df8fd', 'id': 'chatcmpl-Bs2Oc5KYYfXu1g8KQjte1TdqOBEm9', 'service_tier': None, 'finish_reason': 'stop', 'logprobs': None}, id='run--bfec1c94-8f05-4dbc-9eca-61e3e86b5e3d-0', usage_metadata={'input_tokens': 12, 'output_tokens': 16, 'total_tokens': 28, 'input_token_details': {'audio': 0, 'cache_read': 0}, 'output_token_details': {'audio': 0, 'reasoning': 0}}), HumanMessage(content='What is my name?', additional_kwargs={}, response_metadata={}, id='4f7beed6-974e-444c-b9b4-52bfd1a1a90d'), AIMessage(content='Your name is Rocky.', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 6, 'prompt_tokens': 40, 'total_tokens': 46, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 0}}, 'model_name': 'gpt-4.1-nano-2025-04-14', 'system_fingerprint': 'fp_68472df8fd', 'id': 'chatcmpl-Bs2OdxzDx1vt58EMMJqHjqvO0w5dA', 'service_tier': None, 'finish_reason': 'stop', 'logprobs': None}, id='run--268d0d1c-d795-45f3-ba9c-95fed7c1851e-0', usage_metadata={'input_tokens': 40, 'output_tokens': 6, 'total_tokens': 46, 'input_token_details': {'audio': 0, 'cache_read': 0}, 'output_token_details': {'audio': 0, 'reasoning': 0}})]}
"""
print(f"{output['messages'][-1].pretty_print()}")
"""
================================== Ai Message ==================================

Your name is Rocky.
None
"""