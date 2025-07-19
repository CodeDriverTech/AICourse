# 如何创建自定义工具

在构建一个 Agent 时，你可以向它提供一组它可以使用的工具列表。一方面你可以使用 LangChain 内置实现的工具，例如 langchain-tavily；另一方面，你也可以自定义工具。对于自定义工具，可以包含以下几个组件：

| Attribute      | Type                  | Description                                                                                                                                                 |
| -------------- | --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| name           | str                   | 在提供给 LLM/Agent 的工具集合中必须是唯一的。                                                                                           |
| description    | str                   | 用于描述工具的作用，并用作在 LLM/Agent 的上下文中。                                                                                          |
| args_schema    | pydantic.BaseModel    | 可选但推荐使用，但如果使用 callback handlers，那么则必须使用。它可以用来提供更多信息（例如，Few-shot 示例）或对预期参数进行验证。 |
| return_direct  | boolean               | 仅适用于 Agent。当设置为 True 时，Agent 当调用完工具后将会直接将工具结果返回给用户。                         |
<br>
LangChain 支持以下方式创建工具：
1. Functions：定义一个函数；
2. LangChain Runnables：
3. 继承 BaseTool：
> 对于大部分案例来说，通过定义一个函数来创建工具就足够了，并通过一个简单的 `@tool` 修饰器来实现。

## 利用函数创建工具
### @tool 修饰器
