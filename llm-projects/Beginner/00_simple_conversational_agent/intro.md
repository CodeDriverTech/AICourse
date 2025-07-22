# 具有上下文感知（记忆）的对话 Agent

## 背景
“记忆” 是人类出身就必备的一项技能，对现如今的 LLM 来说，同样如此。从 23 年大多数 LLM 仅具备 4K~8K 的上下文窗口，而如今（2025年），1M、2M 的上下文窗口已不是什么新鲜事。在 2024 年，智谱推出的 GLM-Long 模型，通过增量预训练的方法将上下文窗口外推至 1M；诸如此类，Gemini、Qwen 等多家模型也在不断扩展着自身的上下文窗口。甚至近期，大量上下文管理、压缩、摘要等工作在社区内爆火，他们期望着 LLM 应用可以接收更多、更长的信息。

大部分时候，你和 AI 的一轮对话，可能连 4K Tokens 都用不到（4K≈7000个汉字）。**为什么大家对超长上下文窗口如此痴迷？甚至不满足于 1M、2M ...**

这是因为如今的 LLM 不同于 23 年的简单问答，大家追求于将 LLM 应用到更广阔的场景中，让其产生更大的价值。而这其中，就包含着**代码生成**、**文档问答**、**数据/文本挖掘**等极其消耗 Tokens 的场景。再举个例子，24 年让我对**长上下文外推**产生浓厚兴趣是源自智谱的一篇 LongWriter 论文，它们期望通过一次生成就能得到一篇高质量的长文章，这不仅对长上下文**理解**有着极为严苛的要求，还必须能够**生成**超长上下文。

**那么后面的上下文管理、压缩、摘要的工作呢？1M Tokens ≈ 200万汉字，谁家好人有 200 万汉字需要 LLM 一次性理解并生成啊？**

这来源于两方面：一方面，AI Agents/Workflow 的发展，绝大多数的 LLM 应用通常需要多步骤的交互和工具调用来更好地完成一项任务，每一次历史交互都意味着上下文窗口的扩增；另一方面，大家在实际应用落地时发现，尽管厂商们宣称他们模型具有极高的上下文窗口，但随着上下文窗口在交互中不断扩增，LLM 的性能也会急剧下降，导致最终任务失败或效果不佳。（Context Engineer 是2025年年中左右兴起的一种工程化方法，作为Prompt Engineer的延申，这意味着 LLM 应用是否有效不再大量取决于提示词的设计，而更多地转变为依赖上下文窗口管理的设计上。）

**继续外推能不能解决？**

很遗憾，就目前常见的 LLM 模型架构而言，无论旋转位置编码还是增量预训练，应用于极长文本时，由于 $(O(n^2))$ 的计算复杂度，它们不仅会导致性能下降，处理速度也会变得极慢。也有的工作尝试利用稀疏注意力和线性注意力机制来降低注意力的复杂度，从而更高效地处理较长的序列。然而，这意味着需要从新开始训练。并且这种方法也存在着固有缺点，例如线性注意力在并行训练中面临困难，稀疏注意力依赖于人类定义的模式，这会增加计算开销。此外，还有的工作尝试利用不同的架构，比如 RNNs、SSMs 来实现 $(O(n))$ 的计算复杂度。然而，这种架构可能因为训练成本增加、效果不佳等多种原因并不是如今的 LLM 架构主流。

所以，与其花费极大的精力、成本通过训练、变换架构来解决这个问题。大多数应用开发者们不如选择一些更具“工程化”化的方法来从侧面缓解极长上下文不足或导致性能下降的问题。

> 在本课程的设计与搭建中，该篇作为实际搭建的第一篇代码和文档，稍显啰嗦了些。所以上述名词不太理解的，也没有关系。你可以通过如今最强大的 LLM 帮你答疑解惑，也可以选择暂时跳过。如果你对此很感兴趣，推荐最近（2025.7）的一篇实验性文章：[上下文衰减：增加输入Tokens如何影响LLM性能](https://research.trychroma.com/context-rot)

## 快速开始
### 1. 安装依赖
```bash
$ pip install -U langchain langgraph
$ pip install -qU "langchain[openai]"
$ pip install -q python-dotenv
$ pip install -q ipython
```

### 2. 设置环境变量
```bash
$ cp .env.example .env
```
在 `.env` 文件中设置 `OPENAI_API_KEY` 和 `OPENAI_BASE_URL`。

### 3. 运行代码
```bash
$ python basic_run.py # 无交互
$ python interactive.py # 终端交互
```

## 基本方法解析
> **提示：**<br>
> **以下示例代码不等同于教程代码（`basic_run.py`,`interactive.py`），仅作为示例代码。你可能需要稍作修改以作运行。不过，理解代码是最重要的。**<br>
> **例如：对于核心点一，如果不配置官方 API 无法运行。如要尝试运行建议参考教程代码（使用中转 API），额外配置 `base_url`&`api_key`，并统一将`model_provider`设置为`openai`，否则会报错。**
### 核心点一：初始化模型和模型调用
> **（建议）**API文档：[init_chat_model.md](../../../docs/api/init_chat_model.md)；<br>
> **（可选择）**底层实现：参考 LangChain 源代码中的初始化模型方法 [base.py](https://github.com/langchain-ai/langchain/blob/master/libs/langchain/langchain/chat_models/base.py).<br>
#### （1）基本示例代码:
```python
import getpass
import os

if not os.environ.get("OPENAI_API_KEY"):
  os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter API key for OpenAI: ")

from langchain.chat_models import init_chat_model

model = init_chat_model("gpt-4o-mini", model_provider="openai")

model.invoke("Hello, world!")
```
#### （2）初始化 `non-configurable` 模型器:
```python
# pip install langchain langchain-openai langchain-anthropic langchain-google-vertexai
from langchain.chat_models import init_chat_model

o3_mini = init_chat_model("openai:o3-mini", temperature=0)
claude_sonnet = init_chat_model("anthropic:claude-3-5-sonnet-latest", temperature=0)
gemini_2_flash = init_chat_model("google_vertexai:gemini-2.0-flash", temperature=0)

o3_mini.invoke("what's your name")
claude_sonnet.invoke("what's your name")
gemini_2_flash.invoke("what's your name")
```
#### （3）初始化 `partially-configurable` 模型器:
```python
# pip install langchain langchain-openai langchain-anthropic
from langchain.chat_models import init_chat_model

# 如果没有指定模型名称，则不需要额外设置 `configurable=True`
configurable_model = init_chat_model(temperature=0)

configurable_model.invoke(
    "what's your name",
    config={"configurable": {"model": "gpt-4o"}} # 这里没有指定提供商，但 LangChain 会根据模型名称自动解析。例如关键词`gpt`指向`openai`家，`claude`指向`anthropic`家 ...
) # GPT-4o response

configurable_model.invoke(
    "what's your name",
    config={"configurable": {"model": "claude-3-5-sonnet-latest"}}
) # claude-3.5 sonnet response
```
#### （4）初始化 `fully-configurable` 模型器:
```python
# pip install langchain langchain-openai langchain-anthropic
from langchain.chat_models import init_chat_model

configurable_model_with_default = init_chat_model(
    "openai:gpt-4o",
    configuable_fields="any", # 该配置允许我们可以在运行时修改任何参数，如 temperature、max_tokens
    config_prefix="foo", # 该配置规定了如果要修改参数，需要加上什么**前缀**
    temperature=0
)

configuable_model_with_default.invoke("what's your name")

configurable_model_with_default.invoke(
    "what's your name",
    config={
        "configurable": {
            "foo_model": "anthropic:claude-3-5-sonnet-20240620",
            "foo_temperature": 0.6
        }
    }
) # Claude-3.5 sonnet response with temperature 0.6
```


### 核心点二：创建 `MemorySaver` 检查点
在生产环境中，可能会将该方法更改为使用 `SqliteSaver()` 或 `PostgresSaver()` 以连接数据库（具体可查阅 LangChain 文档 or 源码）。
```python
from langgraph.checkpoint.memory import MemorySaver
memory = MemorySaver()
```


### 核心点三：编译图（Graph）
使用提供的 `checkpoint` 编译 Graph，当 Graph 通过每个节点时，它会检查 `State`。
```python
# 请确保你已经定义了一个新的 Graph，即: graph_builder = StateGraph(State)
graph = graph_builder.compile(checkpointer=memory)
```
额外: 你可以选择可视化编译后的 Graph：
```python
from IPython.display import display, Image

try:
    display(Image(graph.get_graph().draw_mermaid_png()))
except Exception:
    pass
```

## 常见错误
### 1. `OPENAI_API_KEY` 环境变量未设置
报错信息：
```bash
openai.OpenAIError: The api_key client option must be set either by passing api_key to the client or by setting the OPENAI_API_KEY environment variable
```
解决方法：
```bash
(1) 请检查是否已将 `.env.example` 复制/重命名为 `.env`；
(2) 如果已复制/重命名，请检查 `.env` 文件中是否包含 `OPENAI_API_KEY` 变量；
(3) 如果未复制/重命名，请复制 `.env.example` 文件并重命名为 `.env`，然后添加 `OPENAI_API_KEY` 变量。
```

## 备注
如果你的代码运行不通，请按照 `依赖 -> 环境（base_url、api_key） -> 模型提供商设置 -> 中转网站日志查看是否有请求进来` 的顺序检查代码。<br>
如若还是没办法解决，欢迎在 [CodeDriver/AICourse](https://github.com/CodeDriverTech/AICourse) 内提交 Issue，或联系作者邮箱: JHxu77@gmail.com。如果你是牧码南山成员应该可以在飞书群或通过学长学姐联系到我，期待你的来信！<br>

**当然，你成功的解决了某个 Bug，或觉得文档有误 or 需要补充。欢迎你进行 Contribution，一起完善课程，让更多的同学受益！！**
