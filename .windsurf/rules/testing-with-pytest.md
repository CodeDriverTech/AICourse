---
trigger: always_on
description: 本规范定义了使用Pytest进行自动化测试的标准和最佳实践。编写高质量的测试是确保代码可靠性、促进安全重构的关键。本指南强制要求使用Pytest作为唯一的测试框架，并详细说明了测试文件的组织、命名约定、Fixture的使用以及如何编写清晰、独立的测试用例。AI在生成或修改代码时，必须为其提供相应的单元测试，以保证代码质量和项目的长期健康。
---

# 规范：使用 Pytest 进行测试 (Testing with Pytest)

## 核心原则

- **测试是必需品**: 所有新增的核心业务逻辑都**必须**有相应的单元测试。测试不是可选的。
- **Pytest Only**: **强制**只使用 `pytest` 及其插件进行测试。严禁在项目中使用`unittest`模块。
- **测试覆盖率**: 追求高的测试覆盖率（目标90%以上），但更要注重测试的质量，确保覆盖了核心逻辑和关键的边界情况。

---

## 1. 测试文件和函数的组织

- **目录结构**: 所有测试文件都必须放在项目根目录下的 `tests/` 目录中。`tests/` 的内部结构应镜像 `src/` 目录。
  - **示例**: `src/my_app/services/user_service.py` 的测试应放在 `tests/services/test_user_service.py`。
- **文件命名**: 测试文件**必须**以 `test_` 开头。
- **函数命名**: 测试函数**必须**以 `test_` 开头，并且函数名应清晰地描述其测试的场景。
  - **示例**: `def test_create_user_with_valid_data_succeeds():`

---

## 2. 编写测试用例

- **AAA 模式 (Arrange, Act, Assert)**: 每个测试用例都应遵循此结构。
  1.  **Arrange**: 设置测试的初始状态，准备测试数据和依赖项。
  2.  **Act**: 调用被测试的代码或函数。
  3.  **Assert**: 验证结果是否符合预期。
- **独立性**: 每个测试用例都应该是独立的，其执行不应依赖于其他测试用例的顺序或结果。
- **简洁性**: 每个测试用例应只测试一个具体的行为或场景。

```python
# In tests/services/test_calculator.py
from src.my_app.services.calculator import add

def test_add_positive_numbers():
    """Tests that adding two positive numbers returns the correct sum."""
    # Arrange
    num1 = 5
    num2 = 10

    # Act
    result = add(num1, num2)

    # Assert
    assert result == 15

def test_add_negative_number_to_positive():
    """Tests adding a negative number to a positive one."""
    # Arrange
    num1 = -5
    num2 = 10

    # Act
    result = add(num1, num2)

    # Assert
    assert result == 5
```

-----

## 3. Fixtures: 管理测试依赖和状态

  - **目的**: 使用 `pytest` 的 Fixtures 来提供测试所需的数据、对象或连接，以减少代码重复。
  - **定义**: Fixtures 在 `conftest.py` 文件中定义（用于项目范围共享）或直接在测试文件中定义（用于模块范围）。
  - **使用**: 将fixture的函数名作为参数传递给测试函数。
```python
# In tests/conftest.py
import pytest

@pytest.fixture
def sample_user_data() -> dict:
    """Provides a sample user data dictionary for tests."""
    return {"username": "testuser", "email": "test@example.com", "is_active": True}

# In tests/services/test_user_service.py
def test_create_user_from_data(sample_user_data: dict):
    # ... use sample_user_data to test user creation ...
    assert user.username == sample_user_data["username"]
```

-----

## 4. Mocking (模拟)

  - **目的**: 使用 Mocking 来隔离被测试单元，替换其外部依赖（如数据库、外部API）。
  - **工具**: **强制**使用 `pytest-mock` 插件（它提供了 `mocker` fixture）。
  - **示例**:
```python
def test_get_user_from_external_api(mocker):
    """Tests that the function correctly processes data from a mocked API call."""
    # Arrange
    mock_api_response = {"id": 1, "name": "John Doe"}
    # Mock the requests.get call
    mocker.patch("requests.get", return_value=mocker.Mock(json=lambda: mock_api_response))

    # Act
    user = get_user_from_api(1)

    # Assert
    assert user.name == "John Doe"
```

## 5. 类型注解

  - **强制**: 所有测试文件、测试函数和fixture都**必须**有完整的类型注解。