---
trigger: model_decision
description: 本规范为使用FastAPI构建API提供了详细的指导方针和最佳实践。其核心是推动开发者采用函数式、声明式的编码风格，并充分利用FastAPI的异步能力和依赖注入系统。规范内容覆盖了项目结构、路由定义、数据验证、错误处理和性能优化等关键方面。AI在生成FastAPI相关代码时必须严格遵守这些规则，以确保最终交付的API具有高性能、高可读性、强健壮性和易于维护的特性。
---

# 规范：FastAPI API 开发指南

## 核心设计理念

- **函数式组件优先**: 优先使用纯函数（`def` 或 `async def`）作为业务逻辑单元和依赖项，而不是类。这使得代码更易于测试和推理。
- **声明式与类型驱动**: 充分利用Python的类型注解和Pydantic模型来声明API的结构、输入和输出。让FastAPI自动完成数据验证、序列化和文档生成。
- **异步优先**: 所有I/O密集型操作（如数据库查询、外部API调用）都**必须**是异步的，使用 `async def` 和 `await`。

---

## 1. 项目与路由结构

- **文件结构**:
  - 使用 `APIRouter` 将路由按业务领域（如 `users`, `products`）拆分到不同的文件中（例如 `routers/user_routes.py`）。
  - 在主应用文件（如 `main.py`）中，通过 `app.include_router()` 聚合所有路由。
- **RORO模式 (Receive an Object, Return an Object)**:
  - **强制**: API的输入和输出都应使用Pydantic模型。即使只有一个字段，也应封装在模型中。这保证了API接口的稳定性和可扩展性。

## 2. 路由定义

- **同步与异步**:
  - 对于纯计算、不涉及I/O的CPU密集型任务，使用 `def` 定义同步路由。
  - 对于任何涉及网络或文件I/O的操作，**强制**使用 `async def` 定义异步路由。
- **类型注解**:
  - **强制**: 所有路径操作函数都必须有完整的类型注解，包括路径参数、查询参数、请求体和响应模型（`response_model`）。
- **响应模型**: **强制**使用 `response_model` 参数来定义响应的数据结构。这不仅可以过滤掉多余的数据，确保响应符合约定，还能在API文档中清晰地展示。

```python
from fastapi import APIRouter
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    email: str

class UserCreate(BaseModel):
    name: str
    email: str

router = APIRouter()

@router.post("/users/", response_model=User, status_code=201)
async def create_user(user_in: UserCreate) -> User:
    # Logic to create user in database
    # ...
    # The returned object will be automatically validated against the User model
    return new_user
```

-----

## 3. 依赖注入 (Dependency Injection)

  - **广泛使用**: **强制**使用FastAPI的依赖注入系统来管理共享资源，如数据库连接、配置对象、认证逻辑等。
  - **实现方式**: 将可复用的逻辑封装成函数，并使用 `Depends` 将其注入到路径操作函数中。
  - **示例 (数据库会话管理)**:


```python
# In dependencies.py
async def get_db_session() -> AsyncGenerator[Session, None]:
    async with SessionLocal() as session:
        yield session

# In user_routes.py
@router.get("/users/{user_id}", response_model=User)
async def read_user(
    user_id: int,
    db: Session = Depends(get_db_session)
):
    # ... use db session ...
```

-----

## 4. 错误处理

  - **预期错误**: 对于可预见的客户端错误（如资源未找到、权限不足），**强制**使用 `HTTPException` 来中断请求并返回标准的HTTP错误响应。
  - **非预期错误**: 使用中间件（Middleware）来捕获所有未处理的异常。该中间件应负责记录详细的错误日志（stack trace），并向客户端返回一个通用的500服务器错误响应，避免泄露内部实现细节。
  - **卫语句模式**: 在函数开始处进行前置条件和无效状态的检查，并使用`if-return`或`raise HTTPException`提前退出，避免深层嵌套的`if-else`。

-----

## 5. 性能优化

  - **避免阻塞I/O**: 这是最高优先级的性能准则。绝不在异步函数中调用任何阻塞的I/O操作。
  - **缓存**: 对不经常变化且频繁访问的数据（如配置信息、热门商品列表）实施缓存策略。可以使用`fastapi-cache`库或集成Redis。
  - **后台任务**: 对于不需要立即返回结果的耗时操作（如发送邮件、生成报告），使用 `BackgroundTasks` 将其推到后台执行，从而快速响应客户端请求。
  - **Lifespan事件**: 优先使用`lifespan`上下文管理器来管理应用的启动和关闭事件（如初始化数据库连接池），而不是已废弃的`@app.on_event`装饰器。