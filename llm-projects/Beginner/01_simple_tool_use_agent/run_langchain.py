"""
一个有记忆、带有搜索工具并完成调用的简单 Agent

INSTALLATION:
    %pip install -U langchain-tavily
"""
from dotenv import load_dotenv
import os

load_dotenv()
base_url = os.getenv("OPENAI_BASE_URL")
api_key = os.getenv("OPENAI_API_KEY")

from langchain.chat_models import init_chat_model
from langchain_tavily import TavilySearch
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

# 定义 llm
memory = MemorySaver()
model = init_chat_model(
    "openai:gpt-4.1-nano-2025-04-14",
    temperature=1.0,
    base_url=base_url,
    api_key=api_key
)

# 配置 tools
search = TavilySearch(max_results=5) # 该工具已在 langchain_tavily 中内置实现。不过，你也可以自己实现一个工具，其实就是写一个 function，然后将其添加进来即可。
tools = [search]
model_with_tools = model.bind_tools(tools)

# 创建 agent
agent_executor = create_react_agent(model_with_tools, tools, checkpointer=memory)

# 使用 agent
config = {"configurable": {"thread_id": "abc123"}}


"""流式传回完整消息"""
# -------------------------------------------
input_message = {
    "role": "user",
    "content": "Hi, I'm Bob and I life in SF."
}

for step in agent_executor.stream(
    {"messages": [input_message]}, config, stream_mode="values"
):
    step["messages"][-1].pretty_print()
"""
================================ Human Message =================================

Hi, I'm Bob and I life in SF.
================================== Ai Message ==================================

Hello Bob! Nice to meet you. How can I assist you today?
"""

# -------------------------------------------
input_message = {
    "role": "user",
    "content": "What's the weather where I live?",
}

for step in agent_executor.stream(
    {"messages": [input_message]}, config, stream_mode="values"
):
    step["messages"][-1].pretty_print()
"""
================================ Human Message =================================

What's the weather where I live?
================================== Ai Message ==================================
Tool Calls:
  tavily_search (call_kw3R0nsdkc5KnYdMD7VzWItI)
 Call ID: call_kw3R0nsdkc5KnYdMD7VzWItI
  Args:
    query: current weather in San Francisco
    search_depth: basic
================================= Tool Message =================================
Name: tavily_search

{"query": "current weather in San Francisco", "follow_up_questions": null, "answer": null, "images": [], "results": [{"title": "Weather in San Francisco", "url": "https://www.weatherapi.com/", "content": "{'location': {'name': 'San Francisco', 'region': 'California', 'country': 'United States of America', 'lat': 37.775, 'lon': -122.4183, 'tz_id': 'America/Los_Angeles', 'localtime_epoch': 1752218686, 'localtime': '2025-07-11 00:24'}, 'current': {'last_updated_epoch': 1752218100, 'last_updated': '2025-07-11 00:15', 'temp_c': 13.9, 'temp_f': 57.0, 'is_day': 0, 'condition': {'text': 'Mist', 'icon': '//cdn.weatherapi.com/weather/64x64/night/143.png', 'code': 1030}, 'wind_mph': 8.1, 'wind_kph': 13.0, 'wind_degree': 221, 'wind_dir': 'SW', 'pressure_mb': 1013.0, 'pressure_in': 29.92, 'precip_mm': 0.0, 'precip_in': 0.0, 'humidity': 93, 'cloud': 25, 'feelslike_c': 12.9, 'feelslike_f': 55.3, 'windchill_c': 10.9, 'windchill_f': 51.6, 'heatindex_c': 12.1, 'heatindex_f': 53.8, 'dewpoint_c': 11.5, 'dewpoint_f': 52.8, 'vis_km': 16.0, 'vis_miles': 9.0, 'uv': 0.0, 'gust_mph': 12.8, 'gust_kph': 20.7}}", "score": 0.5461233, "raw_content": null}, {"url": "https://weather.com/weather/5day/l/6ceaa33cf03fa585f14f1049c4114203a0689d0c82546b1ca35e76197a1731d3", "title": "10 Day Weather-San Francisco, CA", "content": "Some clouds. Low 51F. Winds W at 10 to 20 mph. Humidity87%.", "score": 0.4811862, "raw_content": null}, {"url": "https://wu-next-prod-us-west-2-aws.wunderground.com/history/monthly/us/ca/san-francisco/KCASANFR1771/date/2025-6", "title": "San Francisco, CA Weather History", "content": "Temperature (°F), Max, Average, Min. Max Temperature, 71, 65.25, 59. Avg Temperature, 61.19, 58.33, 55. Min Temperature, 57, 53.8, 49. Dew Point (°F), Max", "score": 0.41023695, "raw_content": null}, {"url": "https://wu-next-prod-us-east-2-aws.wunderground.com/history/daily/us/ca/san-francisco/KCASANFR1753/date/2025-3-7", "title": "San Francisco, CA Weather History", "content": "Temperature (°F), Actual, Historic Avg. Record. High Temp, 64, 64.3, 84. Low Temp, 41, 43.9, 29. Day Average Temp, 51.42, 54.1, -", "score": 0.33024487, "raw_content": null}, {"url": "https://www.weather25.com/north-america/usa/california/san-francisco?page=month&month=July", "title": "San Francisco weather in July 2025 | Weather25.com", "content": "The temperatures in San Francisco in July are comfortable with low of 57°F and and high up to 77°F. There is little to no rain in San Francisco during July,", "score": 0.27016348, "raw_content": null}], "response_time": 1.6}
================================== Ai Message ==================================

The current weather in San Francisco is misty with a temperature of approximately 58°F (14°C). It is quite humid with 93% humidity, and there is light wind coming from the southwest at about 8.1 mph. Would you like to know the forecast for the coming days or any other specific weather details?
"""


# """流式传回 tokens"""
# # -------------------------------------------
# input_message = {
#     "role": "user",
#     "content": "Hi, I'm Bob and I life in SF."
# }

# for step, metadata in agent_executor.stream(
#     {"messages": [input_message]}, config, stream_mode="messages"
# ):
#     if metadata["langgraph_node"] == "agent" and (text := step.text()):
#         print(text, end='|')


# # -------------------------------------------
# input_message = {
#     "role": "user",
#     "content": "What's the weather where I live?",
# }

# for step, metadata in agent_executor.stream(
#     {"messages": [input_message]}, config, stream_mode="messages"
# ):
#     if metadata["langgraph_node"] == "agent" and (text := step.text()):
#         print(text, end='|')