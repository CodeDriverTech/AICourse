---
trigger: model_decision
description: 本规范为AI和开发者在提交代码到Git仓库时，提供了强制性的提交信息（commit message）格式标准。规范严格遵循“Conventional Commits”约定，旨在使提交历史变得清晰、可读，并为自动化工具（如版本发布、变更日志生成）提供支持。AI在执行代码提交时，必须生成符合此规范的提交信息。这不仅能提升代码库的可维护性，还能极大地简化版本管理和团队协作的流程，让每一次代码变更都一目了然。
---

# 规范：Git 提交信息约定 (Git Commit Message Convention)

## 核心原则：清晰、规范、自动化

所有提交到Git仓库的commit message都**必须**遵循**Conventional Commits 1.0.0**规范。这是一个轻量级的约定，构建于提交信息之上。它带来了一组简单的规则，用于创建一个明确的提交历史；这使得编写基于规范的自动化工具变得更容易。

## 提交信息结构

每个提交信息都由一个**header**,一个**body**和一个**footer**组成。

```

\<type\>[optional scope]: \<description\>

[optional body]

[optional footer(s)]

```

---

## 1. Header (头部)

Header是**强制性**的，只有一行，包含`type`, `scope`和`description`。

### 1.1. `type` (类型) - **强制**

必须是以下预定义关键字之一：

- **feat**: A new feature. (一个新功能) - **对应MINOR版本**
- **fix**: A bug fix. (一个bug修复) - **对应PATCH版本**
- **docs**: Documentation only changes. (只修改了文档)
- **style**: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc). (不影响代码含义的修改，如格式化)
- **refactor**: A code change that neither fixes a bug nor adds a feature. (既不是修复bug也不是添加新功能的代码重构)
- **perf**: A code change that improves performance. (提升性能的修改)
- **test**: Adding missing tests or correcting existing tests. (添加或修改测试)
- **build**: Changes that affect the build system or external dependencies (example scopes: gulp, broccoli, npm). (影响构建系统或外部依赖的修改)
- **ci**: Changes to our CI configuration files and scripts (example scopes: Travis, Circle, BrowserStack, SauceLabs). (CI/CD流程相关的修改)
- **chore**: Other changes that don't modify `src` or `test` files. (不修改源代码或测试的其他修改)
- **revert**: Reverts a previous commit. (回滚一个之前的提交)

### 1.2. `scope` (范围) - **可选**

一个名词，用括号括起来，用于描述本次提交影响的代码库的一部分。
**示例**: `feat(api):`, `fix(parser):`, `test(auth):`

### 1.3. `description` (描述) - **强制**

紧跟在`type`或`scope`后面的简短描述。
- 使用祈使句，现在时态，例如用"change"而不是"changed"或"changes"。
- 第一个字母不要大写。
- 结尾不加句号 (`.`)。

**Header 示例**:
`feat(auth): add password reset functionality`
`fix: correct calculation for user discounts`

---

## 2. Body (正文) - **可选**

- 在Header后空一行。
- 同样使用祈使句。
- 应该包含修改的**动机**，以及与之前行为的**对比**。解释“为什么”要这么改，而不仅仅是“改了什么”。

---

## 3. Footer (脚注) - **可选**

- 在Body后空一行。
- 用于两种情况：**破坏性变更 (Breaking Changes)** 和 **关联Issue**。

### 3.1. 破坏性变更 (Breaking Changes)
- **强制**: 如果当前提交引入了破坏性变更，脚注**必须**以`BREAKING CHANGE:`开头，后面是对变更的描述、理由和迁移指南。
- 或者，可以在`type(scope)`后使用感叹号`!`来表示，例如 `feat(user)!: change user id from int to uuid`。

### 3.2. 关联Issue
- 如果当前提交修复或关联了某个issue，可以在脚注中引用。
- **示例**: `Closes #123`, `Refs #456`

---

## 完整示例

### 示例1: 修复bug并关闭issue
```

fix(api): prevent race conditions on update

The previous implementation could lead to race conditions when multiple
updates were performed on the same resource concurrently. This commit
introduces a locking mechanism to prevent this.

Closes \#234

```

### 示例2: 添加新功能并引入破坏性变更
```

feat(auth)\!: switch from session IDs to JWT

Implement JSON Web Tokens for authentication. This is a breaking change
as it requires all client applications to be updated to handle JWTs
instead of session cookies.

BREAKING CHANGE: The server now uses JWT for authentication. All API
requests must include an 'Authorization: Bearer \<token\>' header. The
'/login' endpoint now returns a JWT instead of setting a cookie.

```