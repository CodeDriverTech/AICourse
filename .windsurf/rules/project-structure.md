---
trigger: always_on
---

# 规范：项目结构指南 (Project Structure Guide)

## 核心原则

一个良好、统一的项目结构是可维护软件的根基。AI在创建新项目或向现有项目中添加文件时，必须严格遵守以下目录结构。这不仅有助于人类开发者快速理解项目，也为AI自身提供了清晰的工作上下文。

---

## 标准目录结构

一个典型的AI/Python项目应采用以下结构。根据项目复杂性，某些目录可能是可选的，但如果需要，必须按此规范创建。

````

project\_name/
│
├── .github/                \# (可选) CI/CD 配置文件 (如 GitHub Actions)
│   └── workflows/
│       ├── test.yml
│       └── deploy.yml
│
├── .vscode/                \# (可选) VSCode 编辑器配置
│   └── settings.json
│
├── data/                   \# (可选) 用于存放原始数据、处理后数据
│   ├── raw/
│   └── processed/
│
├── docs/                   \# (可选) 项目文档
│   ├── index.md
│   └── usage.md
│
├── notebooks/              \# (可选) Jupyter notebooks，用于实验和探索
│   └── 01\_initial\_exploration.ipynb
│
├── scripts/                \# (可选) 独立的辅助脚本 (如数据迁移、部署)
│   ├── run\_migrations.py
│   └── deploy\_to\_staging.sh
│
├── src/                    \# 项目核心源代码
│   └── project\_name/       \# Python 包
│       ├── **init**.py
│       ├── api/            \# FastAPI/Streamlit 等Web接口相关
│       │   ├── **init**.py
│       │   ├── routers/
│       │   └── dependencies.py
│       ├── core/           \# 核心业务逻辑、配置
│       │   ├── **init**.py
│       │   └── config.py
│       ├── models/         \# Pydantic 模型、数据库模型
│       │   └── **init**.py
│       ├── services/       \# 业务服务层
│       │   └── **init**.py
│       └── utils/          \# 通用工具函数
│           └── **init**.py
│
├── tests/                  \# 测试代码
│   ├── **init**.py
│   ├── conftest.py         \# Pytest 配置文件和全局 fixtures
│   ├── test\_api/
│   └── test\_services/
│
├── .dockerignore           \# Docker 忽略文件
├── .gitignore              \# Git 忽略文件
├── .env.example            \# 环境变量示例文件
├── Dockerfile              \# Docker 配置文件
├── README.md               \# 项目说明文档
├── pyproject.toml          \# 项目配置文件 (Poetry/Rye, Ruff, Pytest)
└── ...

```

---

## 目录详解

- **`.github/`**: 存放持续集成/持续部署（CI/CD）的工作流文件。AI在被要求设置CI/CD时，应在此处创建相应文件。
- **`data/`**: 用于存放项目所需的数据文件。严格区分原始数据（`raw`）和经过处理的数据（`processed`）。AI不应将数据文件直接硬编码在代码中，而应从该目录读取。
- **`docs/`**: 存放项目的所有文档，如用户指南、API文档等。
- **`notebooks/`**: 用于存放探索性数据分析（EDA）和模型原型验证的Jupyter Notebooks。这些Notebooks不应包含生产代码。
- **`scripts/`**: 存放一次性或辅助性的脚本，例如数据迁移、环境设置等。
- **`src/`**: **核心源代码目录**。
  - 为了避免命名冲突和方便打包，所有源代码都应放在一个与项目同名的子目录中（例如 `src/my_awesome_app/`）。
  - **`__init__.py`**: 每个包含代码的目录都应有 `__init__.py` 文件，以将其标记为Python包。
  - **模块化设计**: 在 `src/project_name/` 内，应根据功能进一步划分模块，如 `api`, `core`, `models`, `services`, `utils` 等。AI在添加新功能时，应遵循这种模块化划分，将代码放置在合适的目录中。
- **`tests/`**: **所有测试代码的存放地**。
  - 测试目录的结构应镜像 `src/` 目录的结构，以便清晰地对应被测试的模块。
  - `conftest.py` 用于定义全局的 `pytest` fixtures 和 hooks。
- **根目录文件**:
  - **`README.md`**: 项目的入口点，必须包含项目简介、安装步骤、使用方法和贡献指南。
  - **`pyproject.toml`**: **项目依赖和工具配置的核心文件**。用于管理 `poetry` 或 `rye` 的依赖，以及 `ruff` 和 `pytest` 的配置。
  - **`Dockerfile`**: 用于将应用容器化。
  - **`.env.example`**: 提供所需环境变量的模板，但不包含任何敏感信息。实际的 `.env` 文件应被 `.gitignore` 忽略。

AI在执行文件操作时，必须严格遵守上述结构。如果需要创建新目录，必须确保其符合此规范的逻辑。