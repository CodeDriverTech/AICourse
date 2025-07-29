---
trigger: always_on
description: 本规范统一AI项目的异常处理与日志策略，涵盖错误分级、守卫式校验、结构化日志与安全合规要求，确保服务稳定、可观测、易排障，适用于FastAPI、LangChain等异步环境。并指导团队持续改进能训练。  
---

# 规范：异常处理与日志策略 (Exception Handling & Logging Policy)
> 本规范统一AI项目的异常处理与日志策略，涵盖错误分级、守卫式校验、结构化日志与安全合规要求，确保服务稳定、可观测、易排障。 

## 1. 核心理念 (Core Philosophy)

- **快速失败，大声宣告 (Fail Fast, Fail Loudly)**: 在开发和测试阶段，问题应尽早、尽可能明显地暴露出来。不要隐藏或忽略错误。
- **优雅失败，信息丰富 (Graceful Failure, Informative Logging)**: 在生产环境中，应用在遇到问题时不应崩溃，而应能优雅地处理错误，同时记录下足够详细的日志信息，以便于问题排查。
- **错误是可预见的**: 将错误处理视为程序正常逻辑的一部分，而不是需要避免的意外。

---

## 2. 异常处理策略 (Exception Handling Strategy)

### 2.1. 使用具体的异常类型 (Use Specific Exceptions)
- **强制**: **禁止**捕获泛泛的`except Exception:`或裸露的`except:`。必须捕获最具体的异常类型，如`ValueError`, `KeyError`, `FileNotFoundError`等。
- **自定义异常**: 对于应用特定的业务逻辑错误（例如“余额不足”、“用户名已存在”），应创建自定义的异常类。这能使代码意图更清晰。

```python
# Custom exception for business logic
class InsufficientBalanceError(Exception):
    """Raised when an account has insufficient balance for a transaction."""
    pass

def withdraw(account_balance: float, amount: float):
    if amount > account_balance:
        raise InsufficientBalanceError(f"Cannot withdraw {amount}, balance is only {account_balance}")
    # ...
````

### 2.2. 强制使用“卫语句”模式 (The "Guard Clause" Pattern)

  - **要求**: 在函数或方法的开头，立即对前置条件和参数进行检查。如果检查失败，则立刻抛出异常或返回，避免深层嵌套的`if/else`。这被称为“卫语句”。
  - **理由**: 该模式极大地提升了代码的可读性，使得函数的主逻辑（Happy Path）清晰地呈现在最外层。

```python
# 👎 禁止 (Don't do this - nested logic)
def process_user(user: dict | None):
    if user is not None:
        if "name" in user and isinstance(user["name"], str):
            # ... main logic is deeply nested ...
            print(f"Processing user: {user['name']}")
        else:
            raise TypeError("User name must be a string.")
    else:
        raise ValueError("User cannot be None.")

# 👍 强制 (Do this - flat logic)
def process_user_guard(user: dict | None):
    """Processes user data using guard clauses."""
    if user is None:
        raise ValueError("User cannot be None.")

    if "name" not in user or not isinstance(user.get("name"), str):
        raise TypeError("User must have a 'name' key with a string value.")

    # Main logic is clean and at the top level
    print(f"Processing user: {user['name']}")

```

### 2.3. 禁止“吞噬”异常 (Never Swallow Exceptions)

  - **强制**: 任何`except`块都**必须**有一个明确的处理动作：**记录日志 (Log)**、**重新引发 (Re-raise)** 或 **有意义地处理 (Handle)**。严禁使用空的`except`块或仅仅`pass`。

### 2.4. 保留异常上下文 (Preserve Exception Context)

  - **要求**: 当你需要捕获一个异常并引发另一个自定义异常时，**必须**使用`raise NewException from original_exception`语法。
  - **理由**: 这会保留原始的堆栈跟踪（stack trace），为调试提供了完整的上下文，至关重要。

---

# 3. Logging Guideline  
1. **强制**使用 `structlog`，**禁止**使用 `print()` 语句进行调试或记录信息；  
2. JSON 输出：`timestamp`, `level`, `event`, `service`, `trace_id`;    
3. 在中间件中注入 `trace_id`；  
4. 本地 `DEBUG`，生产 ≥ `INFO`；  

# 4. Log Levels
- **DEBUG**: 用于开发和诊断的详细信息，进行错误调试、代码审查的过程中必须使用。
- **INFO**: 用于确认程序按预期运行的常规信息。例如：服务启动、配置加载、请求处理成功等。
- **WARNING**: 表明发生了意外情况或潜在问题，但应用仍在正常工作。例如：API响应慢、配置项即将废弃、磁盘空间不足等。
- **ERROR**: 表明由于一个较严重的问题，程序的某个功能无法完成。例如：数据库连接失败、必要的文件未找到、第三方API调用失败。
- **CRITICAL**: 表明一个非常严重的错误，可能导致整个应用无法继续运行。

# 5. Checklist  
- [ ] 每个 API 有 try/except & HTTPException  
- [ ] 日志不写入 PII，特别是 API 密钥
- [ ] 异常类集中定义 `src/exceptions.py`