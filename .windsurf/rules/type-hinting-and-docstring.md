---
trigger: model_decision
description: 本规范统一 AI 项目在类型注解与 Docstring 的书写方式，覆盖 Python 3.12 新特性（TypeAlias, ParamSpec, Self 等）、Google 风格 Docstring、mypy/ruff 规则与常见陷阱，确保 IDE 与 AI Coding 工具可正确推理、自动补全、生成 API 文档，并提升代码可读性、可维护性与回归测试质量。
---

# 规范：类型注解与 Docstring 的书写方式
> 覆盖 Python 3.12 新特性（TypeAlias, ParamSpec, Self 等）、Google 风格 Docstring、mypy/ruff 规则与常见陷阱，确保 IDE 与 AI Coding 工具可正确推理、自动补全、生成 API 文档，并提升代码可读性、可维护性与回归测试质量。

## 必要性
- LLM 生成、静态分析、CI 均依赖精确类型。
- 文档即代码：高质量 Docstring 可被 MkDocs、Sphinx、LangChain 自动提取。

## 适用范围
所有 `src/` 内 Python 文件；测试文件可放宽但须类型完整。

## 3 类型注解硬性规则  
| 规则 | 说明 | 例子 |  
|------|------|------|  
| 公开 API 必须全注解 | 包含参数、返回、泛型 | `def create_user(data: UserCreate) -> User:` |  
| ☑ mypy --strict | 在 CI 强制执行 | `pyproject.toml -> [tool.mypy] strict = true` |  
| 导入 typing | 使用 `from __future__ import annotations` 避免循环 | |  
| 使用 TypeAlias | 复杂嵌套类型复用 | `JsonDict: TypeAlias = dict[str, Any]` |  
| 支持协变/逆变 | 泛型 `typing.Protocol` | |  
| ParamSpec & Concatenate | 高阶函数保留签名 | |  

### 3.1 异步注解  
```python
from collections.abc import AsyncIterator

async def stream_events(topic: str) -> AsyncIterator[Event]: ...
```

### 3.2 TypedDict / dataclasses  
前端 JSON 交互使用 `TypedDict`；内部实体优先 `pydantic.BaseModel`.  

## 4 Docstring 规范  
采用 Google 风格 + pep257。  

```python
def fetch_embeddings(
    texts: list[str],
    /,
    *,
    model: str = DEFAULT_EMB_MODEL,
    batch_size: int = 32,
) -> list[list[float]]:
    """Return embeddings for a list of texts.

    Args:
        texts: Input sentences.
        model: Embedding model name.
        batch_size: Batch size for API call.

    Returns:
        A list of embedding vectors.

    Raises:
        EmbeddingServiceError: If remote service fails.
    """
```

要点：  
1. 句号结尾；首行≤72字符；  
2. 参数顺序与函数签名一致；  
3. 高级示例使用 `Example:`；  
4. 若弃用，加 `Deprecated:`；  
5. 属性文档写在类级 Docstring 的 `Attributes:` 段。  

## 5 linter & tooling  
```toml
[tool.ruff]
select = ["ANN", "D", "B", ...]
ignore = ["D401"]  # 可根据需求微调
[tool.pydocstyle]
convention = "google"
```

## 6 常见误区  
- ❌ `list` 代替 `list[str]`；  
- ❌ 忽略 `None` 返回；应写 `-> str | None`;  
- ❌ 在异步函数中返回协程对象；应 `await`。  

## 7 Checklist  
- [ ] mypy & ruff 全绿  
- [ ] Docstring 覆盖率 ≥ 90 % (`pydocstyle`)  
- [ ] 新增公共函数均带示例  