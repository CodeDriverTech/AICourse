---
trigger: always_on
---

# 规范：通用编码原则 (General Coding Principles)

## 核心理念：编写人类易于理解的代码

> "Anybody can write code that a computer can understand. Good programmers write code that humans can understand." - Martin Fowler

此话是本规范的核心。AI生成的所有代码，首要目标是**清晰性**和**可维护性**，其次才是功能实现。代码的生命周期中，阅读和维护的时间远超编写时间。因此，必须为未来的开发者（包括您自己和团队成员）优化。

---

## 1. 清晰性与可读性 (Clarity & Readability)

### 1.1. 使用有意义的描述性命名 (Use Meaningful and Descriptive Names)
- **要求**: 变量名、函数名、类名必须准确反映其用途和行为。
- **示例**:
  - **禁止**: `def calc(p): discount = p * 0.1`
  - **强制**: `def calculate_discount(product_price: float) -> float: TEN_PERCENT_DISCOUNT = 0.1; discount_amount = product_price * TEN_PERCENT_DISCOUNT; return product_price - discount_amount`
- **原则**: 如果一个名字需要注释来解释，那这个名字本身就取得不够好。

### 1.2. 避免使用魔法数字 (Avoid Magic Numbers)
- **要求**: 禁止在代码中直接使用未解释的硬编码数值。应将其定义为有意义的命名常量。
- **示例**:
  - **禁止**: `if age > 21:`
  - **强制**: `LEGAL_DRINKING_AGE = 21; if age > LEGAL_DRINKING_AGE:`
- **理由**: 提高代码的可读性，并在数值需要变动时，只需修改一处定义即可。

### 1.3. 精简且有意义的注释 (Use Comments Sparingly and Meaningfully)
- **要求**:
  - 不要为“显而易见”的代码添加注释。函数和变量的命名应使其自解释。
  - 注释的目的是解释“**为什么**”这么做，而不是“**做什么**”。解释复杂的逻辑、业务背景或某个决策的权衡。
  - 对于函数和类，使用标准格式的文档字符串（Docstrings）代替普通注释来解释其功能、参数和返回值。
- **示例**:
  - **禁止**: `# 循环用户列表 \n for user in users:`
  - **强制**: `# 为了兼容旧版API返回的数据格式，这里需要手动处理nil值 \n if user.id is None:`

---

## 2. 结构与设计 (Structure & Design)

### 2.1. 单一职责原则 (Single Responsibility Principle - SRP)
- **要求**: 每个函数或类应该只负责一项明确的职责。
- **原则**: 如果一个函数的功能无法用一句话清晰概括，那么它可能承担了过多的职责，需要进行拆分。
- **示例**: 一个函数不应同时负责“从数据库获取用户数据”、“验证数据”和“格式化输出”。应将这三项职责拆分为三个独立的函数。

### 2.2. 避免重复 (Don't Repeat Yourself - DRY)
- **要求**: 避免复制代码逻辑。如果一段代码在多处出现，应将其抽象成一个可重用的函数、类或模块。
- **理由**: 重复代码会增加维护成本和引入错误的风险。一次修改，处处生效。

### 2.3. 模块化设计 (Modular Design)
- **要求**: 鼓励将代码组织成逻辑清晰、高内聚、低耦合的模块。这有助于代码的复用、测试和维护。

---

## 3. 健壮性与安全性 (Robustness & Security)

### 3.1. 优先处理错误和边界情况 (Prioritize Error Handling and Edge Cases)
- **要求**:
  - 在函数开头使用“卫语句”（Guard Clauses）来处理无效输入和边界条件，并尽早返回。
  - 将主逻辑（happy path）放在函数的最后，以提高代码的可读性。
  - 实现健壮的错误处理和日志记录机制。
- **示例**:
  ```python
  def process_data(data: dict | None) -> str:
      if not data:
          logging.warning("Input data is empty.")
          return "No data to process"
      # ... main logic here ...
  ```

### 3.2. 安全第一 (Security-First Approach)
  - **要求**:
      - 始终考虑代码的安全隐患，尤其是在处理用户输入和外部数据时。
      - 对所有外部输入进行严格的验证和清理。
      - 了解并防范常见的安全漏洞（如SQL注入、跨站脚本等）。

### 3.3. 使用断言验证假设 (Use Assertions)
  - **要求**: 在适当的地方使用断言（`assert`）来验证代码中的假设，这有助于在开发阶段及早发现潜在的错误。

-----

## 4. AI 协作元规则 (Meta-Rules for AI Collaboration)

  - **验证信息**: 在提供信息前，必须进行核实，不要基于不清晰的证据进行推测。
  - **保持简洁**: 避免过度工程化。在满足需求的前提下，追求最简单、最直接的解决方案。
  - **持续重构**: 将代码重构视为开发流程的常规部分。始终致力于让代码库比你接手时更整洁。