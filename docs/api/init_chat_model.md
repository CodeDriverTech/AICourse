# 初始化聊天模型 API：`init_chat_model`
> API 文档主要介绍重点功能的相关参数、返回值、异常等基本信息。
> 源码参考：[init_chat_model](https://github.com/langchain-ai/langchain/blob/master/libs/langchain/langchain/chat_models/base.py)

## 使用示例：
```python
import getpass
import os

if not os.environ.get("OPENAI_API_KEY"):
  os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter API key for OpenAI: ")

from langchain.chat_models import init_chat_model

model = init_chat_model("gpt-4o-mini", model_provider="openai")

model.invoke("Hello, world!")
```

## 相关参数：
### `model`: Optional[str]=None
- 模型名称，例如"o3-mini", "claude-3-7-sonnet"；
- 也可以将模型提供商指定在该单字段内，采用 `{model_provider}:{model}` 格式，例如："openai:o1"；
- 当不指定模型提供商时，LangChain 会自动推测。

### `model_provider`: Optional[str]=None
- 模型提供商，例如"openai", "anthropic", "google_vertexai"；
- 当不指定模型提供商时，LangChain 会自动推测。
<details>
<summary>支持的模型提供商，截止于2025年7月（点击展开/折叠）</summary>

| 名称                        | 对应依赖库名称                         |
|-----------------------------|--------------------------------------|
| 'openai'                    | langchain-openai                     |
| 'anthropic'                 | langchain-anthropic                  |
| 'azure_openai'              | langchain-openai                     |
| 'azure_ai'                  | langchain-azure-ai                   |
| 'google_vertexai'           | langchain-google-vertexai            |
| 'google_genai'              | langchain-google-genai               |
| 'bedrock'                   | langchain-aws                        |
| 'bedrock_converse'          | langchain-aws                        |
| 'cohere'                    | langchain-cohere                     |
| 'fireworks'                 | langchain-fireworks                  |
| 'together'                  | langchain-together                   |
| 'mistralai'                 | langchain-mistralai                  |
| 'huggingface'               | langchain-huggingface                |
| 'groq'                      | langchain-groq                       |
| 'ollama'                    | langchain-ollama                     |
| 'google_anthropic_vertex'   | langchain-google-vertexai            |
| 'deepseek'                  | langchain-deepseek                   |
| 'ibm'                       | langchain-ibm                        |
| 'nvidia'                    | langchain-nvidia-ai-endpoints        |
| 'xai'                       | langchain-xai                        |
| 'perplexity'                | langchain-perplexity                 |

</details>

### `configurable_fields`: Optional[Union[Literal["any"], List[str], Tuple[str, ...]]]=None
- 指定哪些模型参数可以在运行时被动态配置：
    - None: 无可配置参数；
    - "any": 允许配置任何参数；
    - Union[List[str], Tuple[str, ...]]：仅允许列表 / 元组中列出的参数可配置。
- 如果已显式传入 model，则 `configurable_fields` 默认为 None；
- 如果未传入 model，则默认值为 `{"model", "model_provider"}`。
> 安全提示：若将 configurable_fields="any"，则诸如 api_key、base_url 等敏感字段都可以在运行时被修改，这可能导致请求被重定向到其他服务中。如果需要接收不受信任的配置，请务必显式列出 configurable_fields=(...) 进行白名单控制。

### `config_prefix`: Optional[str]=None
- 如果为非空字符串，则可以通过 `config["configurable"]["{config_prefix}_{param}"]` 动态配置字段；
- 如果为空字符串，则通过 `config["configurable"]["{param}"]` 进行配置。

### 其他:
- temperature: 模型采样温度
- max_tokens: 模型输出最大 Token 数
- timeout: 请求超时时间
- max_retries: 最大重试次数（当因网络超时、限流等错误导致请求失败时）
- base_url: 请求目标地址
- rate_limiter: 用于控制请求的频率，避免触发限流的 `BaseRateLimiter` 实例
- kwargs: 模型的其他特定关键字参数
    - 会传递给 `<<selected ChatModel>>.__init__(model=model_name, **kwargs)`


## 返回值:
- 若推断为不可配置，则返回与 `model_name` 和 `model_provider` 对应的 `BaseChatModel` 实例；
- 若可配置，则返回一个“模型模拟器”，在收到配置后再初始化。

## 异常:
### ValueError
- 当无法推断或不支持 model_provider 时抛出；
### ImportError
- 当未安装对应模型提供商所需的集成包时抛出。
