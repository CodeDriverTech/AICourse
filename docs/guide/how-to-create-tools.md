# 如何创建自定义工具

在构建一个 Agent 时，你可以向它提供一组它可以使用的工具列表。一方面你可以使用 LangChain 内置实现的工具，例如 `langchain-tavily`；另一方面，你也可以自定义工具。对于自定义工具，可以包含以下几个组件：

| Attribute      | Type                  | Description                                                                                                                                                 |
| -------------- | --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| name           | str                   | 在提供给 LLM/Agent 的工具集合中必须是唯一的。                                                                                           |
| description    | str                   | 用于描述工具的作用，并用作在 LLM/Agent 的上下文中。                                                                                          |
| args_schema    | pydantic.BaseModel    | 可选但推荐使用，但如果使用 callback handlers，那么则必须使用。它可以用来提供更多信息（例如，Few-shot 示例）或对预期参数进行验证。 |
| return_direct  | boolean               | 仅适用于 Agent。当设置为 True 时，Agent 当调用完工具后将会直接将工具结果返回给用户。                         |
<br>
LangChain 支持以下方式创建工具：
1. Functions：最简单，定义一个函数即可；<br>
2. LangChain Runnables：通过 `as_tool` 方法转换为工具；<br>
3. 继承 BaseTool：能够进行最大控制。<br>
> 对于大部分案例来说，通过定义一个函数来创建工具就足够了，并通过一个简单的 `@tool` 修饰器来实现。

## 1. 利用函数创建工具
### 1.1 @tool 修饰器
通过 `@tool` 修饰器是自定义工具最简单的方法。使用该修饰器，默认使用**函数名作为工具名** ，但可以通过将字符串作为修饰器的第一个参数来覆盖。此外，其使用函数中的**文档字符串作为工具的描述**（所以请必须提供文档字符串）。
#### 基本示例
```python
from langchain_core.tools import tool

@tool
def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

print(multiply.name)
print(multiply.description)
print(multiply.args)
```
**示例输出**:
```python
multiply
Multiply two numbers.
{'a': {'title': 'A', 'type': 'integer'}, 'b': {'title': 'B', 'type': 'integer'}}
```
#### 注解解析、嵌套模式支持示例
此外，`@tool` 支持注解解析、嵌套模式等功能：
```python
from typing import Annotated, List

@tool
def multiply_by_max(
    a: Annotated[int, "scale factor"],
    b: Annotated[List[int], "list of ints over which to take maximum"],
) -> int:
    """Multiply a by the maximum of b."""
    return a * max(b)

print(multiply_by_max.args_schema.model_json_schema())
```
**示例输出**:
```python
{'description': 'Multiply a by the maximum of b.',
 'properties': {'a': {'description': 'scale factor',
   'title': 'A',
   'type': 'integer'},
  'b': {'description': 'list of ints over which to take maximum',
   'items': {'type': 'integer'},
   'title': 'B',
   'type': 'array'}},
 'required': ['a', 'b'],
 'title': 'multiply_by_maxSchema',
 'type': 'object'}
```
#### 自定义工具名和指定参数示例
你还可以通过在修饰器内传递参数来自定义工具名和 JSON 参数：
```python
from pydantic import BaseModel, Field

class CalculatorInput(BaseModel):
    a: int = Field(description="first number")
    b: int = Field(description="second number")

@tool("multiplication-tool", args_schema=CalculatorInput, return_direct=True)
def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

print(multiply.name)
print(multiply.description)
print(multiply.args)
print(multiply.return_direct)
```
**示例输出**:
```python
multiplication-tool
Multiply two numbers.
{'a': {'description': 'first number', 'title': 'A', 'type': 'integer'}, 'b': {'description': 'second number', 'title': 'B', 'type': 'integer'}}
True
```
#### Google 风格的文档字符串解析
此外，`@tool` 可以选择性地解析 Google 风格的 docstrings，并将 docstring 的组成部分（例如参数描述）关联到 tool schema 的对应部分。你需要指定 `parse_docstring=True` 来实现这个功能。<br>
> **注意：**如果文档字符串无法按 Google 风格解析，该方法会导致 `ValueError`。
```python
@tool(parse_docstring=True)
def foo(bar: str, baz: int) -> str:
    """The foo.

    Args:
        bar: The bar.
        baz: The baz.
    """
    return bar

print(foo.args_schema.model_json_schema())
```
**示例输出**:
```python
{'description': 'The foo.',
 'properties': {'bar': {'description': 'The bar.',
   'title': 'Bar',
   'type': 'string'},
  'baz': {'description': 'The baz.', 'title': 'Baz', 'type': 'integer'}},
 'required': ['bar', 'baz'],
 'title': 'fooSchema',
 'type': 'object'}
```
### 1.2 结构化工具
你还可以利用 `StructuredTool.from_function` 方法来利用函数创建工具，这种方法相比 `@tool` 提供了更多的可配置性，且无需编写太多额外的代码。
#### 基本示例：
```python
from langchain_core.tools import StructuredTool

def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

async def amultiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

calculator = StructuredTool.from_function(func=multiply, coroutine=amultiply)

print(calculator.invoke({"a": 2, "b": 3}))
print(await calculator.ainvoke({"a": 2, "b": 5}))
```
**示例输出**:
```python
6
10
```
#### 配置示例：
```python
class CalculatorInput(BaseModel):
    a: int = Field(description="first number")
    b: int = Field(description="second number")

def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

calculator = StructuredTool.from_function(
    func=multiply,
    name="Calculator",
    description="multiply numbers",
    args_schema=CalculatorInput,
    return_direct=True,
    # coroutine= ... <- you can specify an async method if desired as well
)

print(calculator.invoke({"a": 2, "b": 3}))
print(calculator.name)
print(calculator.description)
print(calculator.args)
```
**示例输出**:
```python
6
Calculator
multiply numbers
{'a': {'description': 'first number', 'title': 'A', 'type': 'integer'}, 'b': {'description': 'second number', 'title': 'B', 'type': 'integer'}}
```

## 2. 利用 Runnables 创建工具
接受字符串或 `dict` 输入的 LangChain Runnable 可以通过 `ass_tool` 方法转换为工具。该方法允许指定名称、描述以及参数的附加 Schema 等信息。
### 基本示例：
```python
from langchain_core.language_models import GenericFakeChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages(
    [("human", "Hello. Please respond in the style of {answer_style}.")]
)

llm = GenericFakeChatModel(messages=iter(["hello matey"]))

chain = prompt | llm | StrOutputParser()

as_tool = chain.as_tool(
    name="Style responder", description="Description of when to use tool."
)
as_tool.args
```
**示例输出**:
```python
{'answer_style': {'title': 'Answer Style', 'type': 'string'}}
```

## 3. 继承 BaseTool
你可以通过继承 `BaseTool` 来定义一个自定义工具。这是能够对工具定义进行最大灵活控制的方法，但需要编写更多代码。
#### 基本示例：
```python
from typing import Optional

from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain_core.tools import BaseTool
from langchain_core.tools.base import ArgsSchema
from pydantic import BaseModel, Field

class CalculatorInput(BaseModel):
    a: int = Field(description="first number")
    b: int = Field(description="second number")

# 建议：保证每个字段都有类型提示，否则可能出现意外错误。
class CustomCalculatorTool(BaseTool):
    name: str = "Calculator"
    description: str = "useful for when you need to answer questions about math"
    args_schema: Optional[ArgsSchema] = CalculatorInput
    return_direct: bool = True

    def _run(
        self, a: int, b: int, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> int:
        """Use the tool."""
        return a * b

    async def _arun(
        self,
        a: int,
        b: int,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> int:
        """Use the tool asynchronously."""
        return self._run(a, b, run_manager=run_manager.get_sync())

multiply = CustomCalculatorTool()
print(multiply.name)
print(multiply.description)
print(multiply.args)
print(multiply.return_direct)

print(multiply.invoke({"a": 2, "b": 3}))
print(await multiply.ainvoke({"a": 2, "b": 3}))
```
**示例输出**:
```python
Calculator
useful for when you need to answer questions about math
{'a': {'description': 'first number', 'title': 'A', 'type': 'integer'}, 'b': {'description': 'second number', 'title': 'B', 'type': 'integer'}}
True
6
6
```

# 如何创建异步工具
稍微注意下以下事项，剩下的看代码即可:<br>
1. 所有 Runnables 对象都暴露了 `invoke` 和 `ainvoke` 方法（以及 `batch`、`abatch`、`astream` 等其他方法）；<br>
2. LangChain 默认提供异步实现，它假设函数计算成本较高（计算资源），因此会直接将执行委托给另一个线程<br>
3. 如果在异步方法/代码库中工作，你应该创建异步工具而不是同步工具，以避免由于该线程而产生的小但不必要的开销；<br>
4. 如果你同时需要同步和异步的实现，使用 `StructuredTool.from_function` 或使用继承 `BaseTool` 方法；<br>
5. 如果同时实现同步和异步，并且同步代码运行速度更快，可以覆盖默认的 LangChain 异步实现，并直接调用同步代码；<br>
6. 你绝对不能在创建并绑定了异步工具的情况下，使用同步的 `invoke`。但即使你只提供了一个同步工具的实现，也仍然可以使用 `ainvoke` 接口，因为第一点中提到的 “所有 Runnables ...”。<br>
<br>
很好，上述不用背。直接看代码：
## 示例一：

```python
from langchain_core.tools import StructuredTool

def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

calculator = StructuredTool.from_function(func=multiply)

print(calculator.invoke({"a": 2, "b": 3}))
print(
    await calculator.ainvoke({"a": 2, "b": 5})
)  # 使用异步实现会带来较小的开销
```
**示例输出**:
```python
6
10
```
## 示例二：
在仅提供异步定义时，你就不能使用 `ainvoke` 了，不然会报错噢：
```python
@tool
async def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

try:
    multiply.invoke({"a": 2, "b": 3})
except NotImplementedError:
    print("Raised not implemented error. You should not be doing this.")
```
**示例输出**:
```bash
Raised not implemented error. You should not be doing this.
```

# 处理工具错误
在 Agent 中添加工具调用能力时，安全起见，需要一个错误处理策略，以便 Agent 能够从错误中恢复并继续执行。<br>
一个简单的策略是从工具内部抛出一个 `ToolException`，并使用 `handle_tool_error` 指定一个错误处理器。<br>
当制定了错误处理器后，异常会被捕获，错误处理器将决定从工具返回哪个输出。<br>
你可以将 `handle_tool_error` 设置为 `True` 、一个字符串值，或一个函数。如果它是函数，该函数应将 `ToolException` 作为参数并返回一个值。<br>
> 请注意，仅触发 `ToolException` 是无效的。你还需要设置工具的 `handle_tool_error`，因为它的默认值是 `False`。<br>
```python
from langchain_core.tools import ToolException

def get_weather(city: str) -> int:
    """Get weather for the given city."""
    raise ToolException(f"Error: There is no city by the name of {city}.")
```
一个基本示例是：
```python
get_weather_tool = StructuredTool.from_function(
    func=get_weather,
    handle_tool_error=True,
)

get_weather_tool.invoke({"city": "foobar"})
```
**示例输出**:
```python
'Error: There is no city by the name of foobar.'
```
你还可以将 `handle_tool_error` 设置为一个字符串，它将始终被返回。
```python
get_weather_tool = StructuredTool.from_function(
    func=get_weather,
    handle_tool_error="There is no such city, but it's probably above 0K there!",
)

get_weather_tool.invoke({"city": "foobar"})
```
**示例输出**:
```python
"There is no such city, but it's probably above 0K there!"
```
你还可以使用函数处理错误：
```python
def _handle_error(error: ToolException) -> str:
    return f"The following errors occurred during tool execution: `{error.args[0]}`"

get_weather_tool = StructuredTool.from_function(
    func=get_weather,
    handle_tool_error=_handle_error,
)

get_weather_tool.invoke({"city": "foobar"})
```
**示例输出**:
```python
'The following errors occurred during tool execution: `Error: There is no city by the name of foobar.`'
```

# 返回工具执行结果
有时候，我们希望将工具执行产生的某些结果暴露给链或者Agent中的下游组件，但不想直接暴露给模型本身。例如，如果工具返回自定义对象（如文档），我们可能希望在不将原始输出直接传递给模型的情况下，将一些视图或元数据传递给模型。同时，我们可能还需要在其他地方（例如在下游组件中）访问原始的完整输出。<br>
<br>
Tool 和 ToolMessage 接口使得我们可以区分工具输出中供模型使用的部分（即 `ToolMessage.content`）和供模型外部使用的部分（`ToolMessage.artifact`）。<br>
这时，需要我们在定义工具时指定 `response_format="content_and_artifact"`，并确保我们返回一个（内容，工件）的元组：
```python
import random
from typing import List, Tuple
from langchain_core.tools import tool

@tool(response_format="content_and_artifact")
def generate_random_ints(min: int, max: int, size: int) -> Tuple[str, List[int]]:
    """Generate size random ints in the range [min, max]."""
    array = [random.randint(min, max) for _ in range(size)]
    content = f"Successfully generated array of {size} random ints in [{min}, {max}]."
    return content, array
```
如果我们直接使用工具参数调用我们的模型，我们将只会得到输出内容部分：
```python
generate_random_ints.invoke({"min": 0, "max": 9, "size": 10})
```
**示例输出**:
```bash
'Successfully generated array of 10 random ints in [0, 9].'
```
如果我们使用一个 ToolCall（例如由调用模型生成的那些）来调用我们的工具，我们将得到一个包含工具生成的内容和工件的 ToolMessage：
```python
generate_random_ints.invoke(
    {
        "name": "generate_random_ints",
        "args": {"min": 0, "max": 9, "size": 10},
        "id": "123",  # required
        "type": "tool_call",  # required
    }
)
```
**示例输出**:
```bash
ToolMessage(content='Successfully generated array of 10 random ints in [0, 9].', name='generate_random_ints', tool_call_id='123', artifact=[4, 8, 2, 4, 1, 0, 9, 5, 8, 1])
```
当我们继承 BaseTool 时，也可以这样做：
```python
from langchain_core.tools import BaseTool

class GenerateRandomFloats(BaseTool):
    name: str = "generate_random_floats"
    description: str = "Generate size random floats in the range [min, max]."
    response_format: str = "content_and_artifact"

    ndigits: int = 2

    def _run(self, min: float, max: float, size: int) -> Tuple[str, List[float]]:
        range_ = max - min
        array = [
            round(min + (range_ * random.random()), ndigits=self.ndigits)
            for _ in range(size)
        ]
        content = f"Generated {size} floats in [{min}, {max}], rounded to {self.ndigits} decimals."
        return content, array

    # Optionally define an equivalent async method

    # async def _arun(self, min: float, max: float, size: int) -> Tuple[str, List[float]]:
    #     ...
```
```python
rand_gen = GenerateRandomFloats(ndigits=4)

rand_gen.invoke(
    {
        "name": "generate_random_floats",
        "args": {"min": 0.1, "max": 3.3333, "size": 3},
        "id": "123",
        "type": "tool_call",
    }
)
```
**示例输出**：
```bash
ToolMessage(content='Generated 3 floats in [0.1, 3.3333], rounded to 4 decimals.', name='generate_random_floats', tool_call_id='123', artifact=[1.5566, 0.5134, 2.7914])
```