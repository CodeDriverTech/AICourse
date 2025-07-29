---
trigger: always_on
---

# 规范：Python 代码风格指南 (Python Style Guide)

## 核心工具：Ruff

- **强制**: 所有Python代码都必须使用 [Ruff](https://github.com/astral-sh/ruff) 进行格式化和静态检查。Ruff 整合了 `black`, `isort`, `flake8` 等多种工具的功能，提供了极高的性能和统一的规则集。
- **配置**: 项目应包含 `pyproject.toml` 或 `ruff.toml` 配置文件，以确保所有开发者和AI工具使用相同的规则集。

---

## 1. 编码与格式化 (Coding & Formatting)

### 1.1. PEP 8 合规性
- **要求**: 严格遵守 [PEP 8](https://peps.python.org/pep-0008/) 风格指南。Ruff将自动处理大部分格式化问题，如缩进（4个空格）、行长（推荐不超过88个字符）、操作符周围的空格等。

### 1.2. 编程范式
- **偏好**: 优先使用函数式、声明式编程。尽可能避免使用类（Class），除非是为了管理复杂的状态或与需要类的框架（如Pydantic）集成。
- **迭代**: 优先使用迭代和模块化，避免代码复制。

---

## 2. 命名约定 (Naming Conventions)

- **目录与文件**: **强制**使用小写字母和下划线 (`lowercase_with_underscores`)。
  - **示例**: `utils/string_helpers.py`, `api_routers/user_routes.py`
- **变量与函数**: **强制**使用小写字母和下划线 (`lowercase_with_underscores`)。
  - **示例**: `user_profile`, `calculate_total_price()`
- **描述性布尔变量**: 对于布尔值，使用辅助动词，使其含义更清晰。
  - **示例**: `is_active`, `has_permission`, `enable_caching`
- **常量**: **强制**使用大写字母和下划线 (`UPPERCASE_WITH_UNDERSCORES`)。
  - **示例**: `MAX_RETRIES = 3`, `DEFAULT_TIMEOUT = 60`
- **类**: **强制**使用驼峰命名法 (`PascalCase`)。
  - **示例**: `class UserProfile:`, `class DatabaseManager:`

---

## 3. 类型注解 (Type Annotations)

- **强制**: 所有函数签名（包括参数和返回类型）都**必须**包含类型注解。所有类成员变量也必须有类型注解。
- **要求**: 使用 `typing` 模块提供的最具体的类型。
- **理由**: 类型注解极大地提高了代码的可读性和健壮性，是静态分析工具（如`mypy`）和AI编码工具理解代码上下文的关键。
- **示例**:
  ```python
  from typing import List, Dict, Optional

  def get_user_by_id(user_id: int, user_database: Dict[int, str]) -> Optional[str]:
      return user_database.get(user_id)

  class DataProcessor:
      processed_items: List[str] = []

      def process(self, items: List[str]) -> None:
          # ... logic ...
````

-----

## 4. 文档字符串 (Docstrings)

  - **强制**: 所有公开的模块、函数、类和方法都**必须**有文档字符串。
  - **格式**: **强制**使用 Google 风格（Google Style）的 Docstrings。
  - **内容**: Docstrings 必须清晰地解释其目的、参数（`Args`）、返回值（`Returns`）以及可能抛出的异常（`Raises`）。在适当时，应包含简短的使用示例。
  - **示例**:
    ```python
    """A module for processing user data."""

    from typing import List

    class UserProcessor:
        """Processes and validates user information.

        Attributes:
            validated_users (List[str]): A list of names of validated users.
        """

        def __init__(self, user_list: List[str]):
            """Initializes the UserProcessor.

            Args:
                user_list: A list of user names to be processed.
            """
            self.user_list = user_list
            self.validated_users = []

        def validate_and_store(self) -> int:
            """Validates users and stores the valid ones.

            This method iterates through the user list, checks for validity,
            and stores valid user names in the `validated_users` attribute.

            Returns:
                The number of users that were successfully validated.

            Raises:
                ValueError: If the initial user_list is empty.
            """
            if not self.user_list:
                raise ValueError("User list cannot be empty.")
            # ... validation logic ...
            return len(self.validated_users)
    ```

-----

## 5. 导入 (Imports)

  - **规范**: 导入应分组，顺序为：标准库、第三方库、本项目库。Ruff (`isort`) 会自动处理。
  - **导出**: 优先使用命名导出（`named exports`）而不是通配符导出（`from ... import *`），以增强代码的清晰度和可维护性。