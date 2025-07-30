# 科学论文综述生成 Agent

## 背景
对于程序员来说，整个职业生涯可能有 70% 的时间在看代码、学习代码或审查代码；而对于研究者们来说，在阅读、分析理解他人论文也同样占据着大量的时间。对于想快速了解一个研究领域的研究者来说，找到一篇好的综述并认真看完理解它，成为了最具性价比的路径。

然而，对于综述产出者来说，这可不是一件容易的事情。各期刊的综述撰写，通常是邀请制的，这要求你对特定领域有足够深的见解和足够出色的工作。这还不够，在你撰写的过程中，你需要从多个分散的论文数据库生态系统中进行低效的搜索、汇总，并在多篇论文之间综合对比，尝试从中挖掘论文间的关系并进行连接。没错，这很像你在做一张"图（Graph）"，论文是节点，关系是边。

如果你现在处于本科阶段，特别推荐你在大四刚开始的时候就尝试构思自己的毕设主题，并认真地花大量的时间去准备、完善一个偏研究些的学术任务。这不仅能帮你巩固提升检索和信息汇总的能力，还能让你在该领域上快速成长，拥有自己的见解。

总之，传统的文献综述过程包含以下痛点：
- **搜索效率低下**：需要在多个数据库平台间切换搜索
- **信息筛选困难**：从海量文献中筛选高质量相关论文
- **内容理解耗时**：深度阅读和理解每篇论文的核心贡献
- **综合分析复杂**：在多篇论文间建立联系和对比分析
- **写作组织挑战**：将分散信息整合为结构化综述报告

---

而本教程实现了一个基于 LangGraph 的智能研究助手，能够自动化完成上述繁重的文献综述工作。它结合了学术 API、多智能体协作和先进的文本处理技术，为研究人员、学生和专业人员提供了一个高效的学术研究工具。

**该 Agent 的核心能力包括：**
- 🔍 **智能论文搜索**：基于 CORE API 的大规模学术论文检索
- 📥 **并行文档处理**：多线程下载和解析 PDF 文档
- 🧠 **AI 驱动分析**：使用 LLM 深度理解论文内容和贡献
- 📝 **自动综述生成**：基于协调者-工作者模式生成高质量综述
- 🎯 **质量保障机制**：多层次的内容验证和优化流程
<br>

[Mermaid 工作流程图表](./graph_visualization.mmd)

🔧 工作流程
1. **决策节点**：分析用户查询，判断是否需要进行论文研究
2. **规划节点**：制定详细的搜索和分析计划
3. **搜索节点**：通过CORE API搜索相关学术论文
4. **下载节点**：并行下载PDF文件并提取文本内容
5. **分析节点**：使用LLM深度分析每篇论文的核心内容
6. **综述生成**：采用协调者-工作者模式生成结构化综述
7. **质量评估**：自动评估生成结果的质量和完整性

> **特别提示**：该教程实现不针对某一特定领域；对于不同领域的适应且想获得更好效果，你可以尝试修改 Prompts 设计来获得一篇更有价值的学术综述论文。

## 快速开始
### 1. 申请必需的 API 密钥
在该项目中，我们需要两个重要的 API 密钥：

**OpenAI API 密钥**：用于大语言模型调用
- 访问 [OpenAI 官网](https://platform.openai.com/api-keys) 获取 API 密钥
- 或访问 [中转平台（推荐）](https://yunwu.ai/register?aff=bFOA) 获取 API 密钥，并修改 BASE_URL 为 https://api.yunwu.ai/v1。

**CORE API 密钥**：用于学术论文搜索
- 访问 [CORE API 官网](https://core.ac.uk/services/api#form) 申请免费 API 密钥

### 2. 安装依赖
```bash
$ pip install -r requirements.txt
```

### 3. 设置环境变量
```bash
$ cp .env.example .env
```
在 `.env` 文件中设置必需的环境变量：
```bash
# OpenAI 配置
OPENAI_API_KEY="your_openai_api_key_here"
OPENAI_BASE_URL="your_openai_base_url_here"
DEFAULT_MODEL="your_default_model_here"

# CORE API 配置
CORE_API_KEY="your_core_api_key_here"

# 模型参数(可动态调整)
TEMPERATURE=0.3
MAX_SURVEY_REFERENCE=10

# 文件保存配置
SAVE_DIR="papers"

# 语言设置（可选，默认为中文）
LANGUAGE="cn"  # cn为中文，en为英文
```

### 4. 运行代码
我们提供了两种运行方式。相对应的，也是两种你理解代码的方式。
- `main.py`：结构化项目版本，虽然作为`llm-projects`下的教程项目，并不未编写对外接口、流式返回或者交互界面，但相较于单文件版本，其更符合一个完整项目的样子，适合你更深入理解每一个组件、模块应该所处的位置，而不是全部堆砌在一个代码文件内。
- `run.py`：单文件版本，一种脚本化的写法。你需要知道的是，通常来说，这种写法并不好，既不易于维护和扩展，也不便于你理解代码的逻辑。但其作为该项目的“实验阶段的雏型”，我也稍加完善并进行保留。或许你能从该文件内发现在该项目编码过程中的思考过程。
```bash
# 运行结构化项目版本
$ python main.py "深度学习中的注意力机制综述"

# 或运行单文件版本
$ python run.py  # 交互式运行
```

### 5. 使用示例
```bash
# 生成综述 / 报告 / 对比分析（保存为一份 Markdown 文件）
$ python main.py "扩散模型在指纹图像生成领域的研究进展综述"
$ python main.py "生成一份近3年（2022-2025）的大语言模型研究进展报告"
$ python main.py "分析基于自回归和Diffusion架构在图像生成模型上的差异与优劣"

# 查询论文（会自动下载）
$ python main.py "帮我找到 10 篇与LLM4Rec（Large Language Model for Recommendation）相关的论文"
$ python main.py "3 篇最新的（2025）LLM 在代码生成方面的论文（AICoding）"

# 下载论文（会简短介绍该论文）
$ python main.py "下载这篇论文：https://core.ac.uk/download/578172631.pdf"
```

## 基本方法解析
> **提示：**<br>
> **以下示例代码来自实际的教程代码实现，展示了关键概念和技术细节。建议结合完整代码来理解每个组件的作用。**<br>

### 核心技术架构：协调者-工作者模式

本项目在综述生成节点采用了 Anthropic 在《Building effective agents》中提到的**协调者-工作者（Orchestrator-Worker）**架构模式。这种模式特别适合需要处理大量并行任务和复杂工作流的场景。

```python
# 协调者阶段：分析论文并规划综述结构
print("🧠 协调者阶段：分析论文内容并规划综述结构...")
paper_summaries = []
for i, paper in enumerate(papers_info):
    print(f"  📄 分析第 {i+1} 篇论文...")
    summary = paper_service.summarize_paper_content(paper['content'], original_query)
    paper_summaries.append(summary)

# 生成综述大纲
planner_llm = llm.with_structured_output(SurveySections)
survey_outline = planner_llm.invoke([HumanMessage(content=outline_prompt_text)])

# 工作者阶段：并行生成各章节详细内容
print("✍️ 工作者阶段：并行生成各章节详细内容...")
completed_sections = survey_service.parallel_generate_sections(
    survey_outline.sections, original_query, paper_summaries
)
```

### 核心点一：LangGraph 工作流设计

项目使用 LangGraph 构建了一个复杂的多节点工作流，包含决策、规划、执行、判断等多个阶段：

```python
from langgraph.graph import StateGraph, END
from src.models import AgentState

def create_workflow() -> StateGraph:
    workflow = StateGraph(AgentState)
    
    # 添加核心节点
    workflow.add_node("decision_making", decision_making_node)  # 决策节点
    workflow.add_node("planning", planning_node)              # 规划节点
    workflow.add_node("agent", agent_node)                    # 智能助手节点
    workflow.add_node("tools", tools_node)                    # 工具执行节点
    workflow.add_node("judge", judge_node)                    # 质量判断节点
    workflow.add_node("generate_survey", generate_survey_agent) # 综述生成节点
    
    # 添加条件边和控制流
    workflow.add_conditional_edges(
        "decision_making", router,
        {"planning": "planning", "end": END}
    )
    
    return workflow
```

### 核心点二：并行文档处理

为了提高效率，项目实现了多线程并行下载和处理 PDF 文档：

```python
def _parallel_download_papers(self, download_urls: list[str], max_workers: int = 3) -> None:
    def download_single_paper(url: str) -> tuple[str, bool, str]:
        try:
            from ..tools.download_tools import download_paper
            result = download_paper(url)
            return url, True, result
        except Exception as e:
            return url, False, str(e)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(download_single_paper, url): url 
                        for url in download_urls}
        
        for future in as_completed(future_to_url):
            url, success, result = future.result()
            if success:
                print(f"  ✅ 下载完成: {os.path.basename(url)}")
            else:
                print(f"  ❌ 下载失败: {result}")
```

### 核心点三：结构化数据模型

项目使用 Pydantic 定义了严格的数据模型，确保数据流的类型安全：

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class PaperSummary(BaseModel):
    """论文摘要结构化数据"""
    title: str = Field(description="论文标题")
    abstract: str = Field(description="论文摘要")
    key_contributions: List[str] = Field(description="主要贡献")
    methodology: str = Field(description="研究方法")
    limitations: str = Field(description="局限性")
    relevance_score: int = Field(description="相关性评分(1-10)")

class SurveySection(BaseModel):
    """综述章节结构"""
    title: str = Field(description="章节标题")
    description: str = Field(description="章节描述")

class SurveySections(BaseModel):
    """综述章节集合"""
    sections: List[SurveySection] = Field(description="章节列表")
```

### 核心点四：智能工具集成

项目集成了多个专业工具，每个工具都用 `@tool` 装饰器进行了标准化：

```python
from langchain_core.tools import tool
from ..models import SearchPapersInput

@tool("search-papers", args_schema=SearchPapersInput)
def search_papers(query: str, max_papers: int = 1) -> str:
    """使用CORE API搜索科学论文"""
    try:
        from ..services.core_api import CoreAPIWrapper
        print(f"🔍 正在搜索论文: {query} (最多 {max_papers} 篇)")
        return CoreAPIWrapper(top_k_results=max_papers).search(query)
    except Exception as e:
        return f"执行论文搜索时出错: {e}"

@tool("download-paper")
def download_paper(url: str) -> str:
    """从给定URL下载特定科学论文"""
    # 实现PDF下载和文本提取逻辑
    # ...
    return f"论文内容: {text}"
```

### 核心点五：模块化项目结构

项目采用了标准化的模块化结构，符合最佳实践：

```
src/
├── models.py           # 数据模型定义
├── config.py          # 配置管理
├── utils.py           # 工具函数
├── main.py            # 主程序入口
├── core/              # 核心业务逻辑
│   ├── nodes.py       # LangGraph 工作流节点
│   └── workflow.py    # 工作流定义和编译
├── services/          # 服务层
│   ├── core_api.py    # CORE API 封装
│   ├── paper_service.py   # 论文处理服务
│   └── survey_service.py  # 综述生成服务
└── tools/             # 工具模块
    ├── search_tools.py    # 论文搜索工具
    ├── download_tools.py  # 文件下载工具
    └── feedback_tools.py  # 人机交互工具
```

### 扩展思路

基于当前实现，你可以考虑以下扩展方向：

1. **网络搜索**: 通过网络搜索获取一些某领域下的最新资讯
    - 为什么是网络搜索，而不是集成更多学术数据库？
    - 如果你有更多学术数据库权限你当然可以接入，但这并不好申请；
    - 而接入网络搜索并不是为了获取更多论文，而是针对于某一正飞速发展的领域（如AICoding），大部分最新发展不会出现在论文中，而是在博客中。不少博客也有着很大的价值；
    - 举个例子，截止2025.07，大部分能检索到的AICoding学术论文，大多还停留在扩增Coding任务数据，重新训练、微调来进行刷榜；
    - 进一步的，也有一些利用类似于 GRPO 的规则奖励模型，结合构建 RL 代码执行场景，根据执行结果来奖励模型；
    - 但如果我作为用户，我想了解 AICoding 的场景，生成的综述应该包括最新的 Claude-4、Gemini-CLI、ClaudeCode、Qwen3-Coder 等内容。
2. **指定文献**: 支持用户自行传入文献PDF，Agent根据指定的文献生成综述
3. **高级数据分析与可视化**：对文献数据进一步处理，以洞察更深层次的趋势
    - 文献中大量高价值的数据存在于表格、图表中，对于这部分数据你可以需要结合多模态文档数据提取工具进行结构化处理或挖掘（如 DocLayOut-YOLO）；
    - 在提取/挖掘出数据过后，你应该指示 Agent 结合这些数据进行对比分析，进一步的，你可以将对比的数据和结果利用`Mermaid`可视化一些图表；
    - 当然，你应该必要的加入一些trick，否则就不叫“高级” ... 例如存储为SQL，或为这些数据关系尝试构建出一个Graph等等，自行发挥，根据你的场景需求来不断改进代码吧！
4. **可视化界面**：开发 Web 界面或桌面应用
5. **个性化定制**：根据用户研究领域动态调整提示词，或者你可以写一套更具扩展性的提示词模版

> OK，很期待你在成功运行和理解该教程代码后，尝试做一套改进。你也可以联系我一起，Share 你的想法～ 一起为本项目贡献！🎉

## 技术深度解析

### LangGraph vs 传统 Agent 框架

相比传统的 Agent 实现，LangGraph 提供了以下优势：

1. **可视化工作流**：能够清晰地看到 Agent 的执行路径
2. **状态管理**：更好的状态持久化和传递机制
3. **条件控制**：支持复杂的分支和循环逻辑
4. **调试友好**：详细的执行日志和状态追踪

### 协调者-工作者模式的优势

这种架构模式特别适合科学文献处理任务：

- **协调者**负责整体规划和质量控制
- **工作者**并行处理具体的分析任务
- **合成器**整合所有结果生成最终报告

### 性能优化策略

1. **并行处理**：PDF 下载和文本提取并行执行
2. **缓存机制**：避免重复下载和分析相同论文
3. **流式输出**：实时显示处理进度和中间结果
4. **错误恢复**：支持断点续传和错误重试

## 备注

### 环境配置问题
如果你的代码运行不通，请按照 `依赖 -> 环境（base_url、api_key） -> 模型提供商设置 -> 中转网站日志查看是否有请求进来` 的顺序检查代码。

### 常见问题排查

1. **API 密钥错误**：检查 `.env` 文件中的密钥配置
2. **网络连接问题**：确认能够访问 OpenAI 和 CORE API
3. **文献查询失败**：首先检查网络环境，其次检查 CORE API 是否产生了速率限制
4. **Tokens 超出**：请尽量选择上下文长度在 64K 以上的模型，否则极有可能因为上下文窗口溢出而失败

> 如若还是没办法解决，欢迎在 [CodeDriver/AICourse](https://github.com/CodeDriverTech/AICourse) 内提交 Issue，或联系作者邮箱: JHxu77@gmail.com。如果你是牧码南山成员应该可以在飞书群或通过学长学姐联系到我，期待你的来信！

### 性能调优建议

- 根据你的网络状况调整并行下载线程数
- 适当设置 `MAX_SURVEY_REFERENCE` 来平衡质量和速度
- 使用更快的 LLM 模型（如 `gpt-4.1-mini-2025-04-14`）来降低成本

### 贡献指南

如果你成功解决了某个 Bug，或觉得文档有误需要补充，欢迎你进行 Contribution！你可以：

1. 在本项目仓库中提交 Issue
2. 提交 Pull Request 来改进代码或文档
3. 分享你的使用经验和改进建议

一起完善这个课程，让更多的同学和研究者受益！

---

**享受你的学术研究之旅！** 🎓✨
