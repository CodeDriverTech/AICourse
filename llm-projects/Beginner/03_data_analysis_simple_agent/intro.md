# 数据分析 Agent

## 背景
“数据”与“大模型”是紧密联系的。大模型基于超大规模的数据训练而来，23 年初，LLaMA-1，在超过 1T tokien 的语料上进行的预训练；23 年中的 LLaMA-2 扩充到了 2T， 而在 24 年的 LLaMA-3 系列，超过了 15T Tokens。在 2025 年的 Qwen3 系列，更在 30T 的语料上完成了预训练，支持 119 种语言和方言。<br>
> 注：基础你必须知道，T 是 Trillion 的缩写，万亿。
<br>
而在大模型的使用中，Text2SQL（自然语言转SQL指令）以查询数据库，从超长文本（“草堆”）中提取关键信息（通常称为“文本挖掘，Text Mining”），甚至结构化数据、数据分析、多模态数据识别与提取，都是一个 AI 研发/应用者绕不开的应用场景。<br>
<br>
总之，数据不仅是大模型的“粮食”，更是众多人手中的利器。例如传统的数据分析通常需要一定的专业知识，但通过大模型，任何人几乎可以从任何垂类领域的数据中获取到许多关键信息和趋势，从而加速自身决策和创造出更大价值。<br>
<br>
在本教程中，将指导你创建一个由 AI 驱动的数据分析 Agent，它能够使用自然语言解释和回答有关数据集的问题。它结合了 LLM 和数据操作工具，以实现直观的数据探索。


## 快速开始
### 1. 安装依赖
```bash
$ pip install -U langchain_experimental
$ pip install -U pandas numpy tabulate
```

### 2. 设置环境变量
```bash
$ cp .env.example .env
```
在 `.env` 文件中设置 `OPENAI_API_KEY` 和 `OPENAI_BASE_URL`。

### 3. 运行代码
```bash
$ python basic_run.py
```


## 基本方法解析
该份代码就一个`create_pandas_dataframe_agent`方法，其它方法要么是 Python 基础，要么在前文有讲过，不在赘述。<br>
而`create_pandas_dataframe_agent`是一个 LangChain 内置的 API，可以直接查看包括它在内的相关内置 agents 文档：<br>
- [create_pandas_dataframe_agent](https://python.langchain.com/api_reference/experimental/agents/langchain_experimental.agents.agent_toolkits.pandas.base.create_pandas_dataframe_agent.html)
- [create_csv_agent](https://python.langchain.com/api_reference/experimental/agents/langchain_experimental.agents.agent_toolkits.csv.base.create_csv_agent.html)
- [create_python_agent](https://python.langchain.com/api_reference/experimental/agents/langchain_experimental.agents.agent_toolkits.python.base.create_python_agent.html)
- [create_spark_dataframe_agent](https://python.langchain.com/api_reference/experimental/agents/langchain_experimental.agents.agent_toolkits.spark.base.create_spark_dataframe_agent.html)
- [create_xorbits_agent](https://python.langchain.com/api_reference/experimental/agents/langchain_experimental.agents.agent_toolkits.xorbits.base.create_xorbits_agent.html)



## 备注
如果你的代码运行不通，请按照 `依赖 -> 环境（base_url、api_key） -> 模型提供商设置 -> 中转网站日志查看是否有请求进来` 的顺序检查代码。<br>
如若还是没办法解决，欢迎在 [CodeDriver/AICourse](https://github.com/CodeDriverTech/AICourse) 内提交 Issue，或联系作者邮箱: JHxu77@gmail.com。如果你是牧码南山成员应该可以在飞书群或通过学长学姐联系到我，期待你的来信！<br>

**当然，你成功的解决了某个 Bug，或觉得文档有误 or 需要补充。欢迎你进行 Contribution，一起完善课程，让更多的同学受益！！**