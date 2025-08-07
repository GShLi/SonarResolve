# SonarQube自动修复与Jira集成工具

这是一个强大的Python工具，能够自动从SonarQube获取Critical级别## 📦 安装依赖AI大模型**进行专业代码修复，并集成Git和Jira工作流。

## 🚀 功能特性

### 🔍 智能项目管理 ⭐ 升级!
- 🔗 **自动发现和匹配**：智能匹配SonarQube与Jira项目
- 📊 **基于多维度匹配**：项目名称、关键词、Git仓库URL的智能关联
- 📋 **项目分析功能**：项目列表浏览和问题统计分析
- 🎯 **交互式选择**：用户友好的项目选择界面
- � **SQLite智能缓存**：避免重复创建，提升处理效率

### 📋 第一阶段：Jira任务批量创建 ⭐ 重点功能!
- 🔍 **批量扫描所有SonarQube Critical问题**
- 📊 **按项目自动分组处理**，支持多项目并行
- 🎯 **智能匹配或自动创建Jira项目**
- 📝 **详细任务信息**：包含代码片段、规则描述、文件位置
- 🔄 **重复检测机制**：避免创建重复任务
- 📈 **完整处理报告**：生成详细的批量处理统计
- 🔧 **健壮错误处理**：详细日志和异常恢复

### 🤖 第二阶段：LangChain AI自动修复 ⭐ 新功能!
- 🎯 **LangChain最佳实践**：使用专业提示词架构
- 🔧 **专门针对SonarQube问题优化**的AI修复策略  
- 💎 **SystemMessage + HumanMessage**结构化提示词设计
- 🤖 **多AI模型支持**：OpenAI GPT-4 和 Anthropic Claude
- 📝 **智能Git集成**：自动生成提交信息和分支管理
- 🔀 **自动MR创建**：创建详细的Merge Request
- 📊 **修复对比报告**：详细的修复前后对比分析
- 🎭 **专家角色AI**：资深代码修复专家人格设定

### 🔄 增强的代码片段功能 ⭐ 新增!
- 📖 **直接从SonarQube获取**：使用 `sources/issue_snippets` API
- 🧹 **HTML标签清理**：自动清理SonarQube返回的HTML标签
- 📍 **精确定位**：标记问题所在的具体代码行
- 📋 **上下文代码**：包含问题周围的代码上下文
- 🔧 **规则信息集成**：通过 `rules/show` API获取详细规则描述

### 🛡️ 规则信息增强 ⭐ 新增!
- 📚 **完整规则描述**：自动获取SonarQube规则的详细说明
- 🏷️ **规则分类信息**：包含规则类型、严重程度、标签等
- 📝 **Jira任务增强**：在任务描述中包含完整的规则信息
- 🔍 **智能HTML清理**：自动清理规则描述中的HTML格式
## 📚 详细文档

### 🚀 快速开始
- 📋 **[快速开始指南](docs/QUICK_START_JIRA.md)** - 5分钟上手指南
- 🧪 **[连接测试](docs/CONNECTION_TEST.md)** - 测试各服务连接状态
- ⚙️ **[配置说明](docs/CONFIGURATION.md)** - 详细的配置参数说明

### 🔄 核心工作流程
- 📊 **[SonarQube到Jira工作流程](docs/SONAR_TO_JIRA_WORKFLOW.md)** - 完整的批量处理流程说明
- 📈 **[工作流程图](docs/WORKFLOW_DIAGRAMS.md)** - 可视化流程图
- 💾 **[SQLite缓存指南](docs/SQLITE_CACHE_GUIDE.md)** - 智能缓存机制说明

### 🤖 AI集成
- 🎯 **[LangChain AI指南](docs/LANGCHAIN_AI_GUIDE.md)** - AI大模型集成说明
- 🔧 **[AI修复实现报告](docs/LANGCHAIN_IMPLEMENTATION_REPORT.md)** - 技术实现详解
- 📝 **[API调用示例](docs/API_EXAMPLES.md)** - 详细的API使用示例

### 🛠️ 技术文档
- 📦 **[Poetry管理指南](docs/POETRY_GUIDE.md)** - 依赖管理详解
- 🐍 **[Python兼容性](docs/PYTHON_COMPATIBILITY.md)** - Python版本兼容说明
- 🔄 **[Git自动发现](docs/GIT_AUTO_DISCOVERY.md)** - Git仓库自动匹配
- 🏗️ **[项目结构说明](docs/PROJECT_STRUCTURE.md)** - 代码组织架构

### 🔧 高级功能
- 🏷️ **[Jira标签修复](docs/JIRA_LABELS_FIX.md)** - 标签处理优化
- 📊 **[简化SQLite实现](docs/SIMPLIFIED_SQLITE_IMPLEMENTATION.md)** - 数据库设计说明
- 📝 **[更新日志](docs/CHANGELOG.md)** - 版本更新记录ra任务批量创建 ⭐ 升级!
- 🔍 **批量扫描所有SonarQube Critical问题**
- 📋 **按项目自动分组处理**
- 🎯 **智能匹配或自动创建Jira项目**
- 📊 为每个问题在Jira中创建详细任务
- 🔄 避免重复创建任务
- � 生成完整的批量处理报告
- �📝 详细的日志记录和错误处理

### 第二阶段：LangChain风格AI自动修复 ⭐ NEW!
- 🤖 使用**LangChain最佳实践**的专业提示词架构
- 🎯 **专门针对SonarQube问题优化**的AI修复策略
- 💎 **SystemMessage + HumanMessage** 结构化提示词设计
- 🔧 支持OpenAI GPT-4和Anthropic Claude（专门为Claude 4.0优化）
- 📝 自动生成Git提交信息和分支
- 🔀 自动创建Merge Request
- 📊 详细的修复前后对比报告
- 🎭 **资深代码修复专家**角色的AI人格设定

## 📦 安装依赖

### 使用Poetry（推荐）

1. 安装Poetry：
```bash
# Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -

# 或使用pip
pip install poetry
```

2. 安装项目依赖：
```bash
# 安装所有依赖（包括开发依赖）
poetry install

# 仅安装生产依赖
poetry install --no-dev
```

3. 激活虚拟环境：
```bash
poetry shell
```

### 使用传统方式

```bash
# 导出requirements.txt
poetry export -f requirements.txt --output requirements.txt

# 安装依赖
pip install -r requirements.txt
```

## ⚙️ 配置设置

1. 复制配置文件模板：
```bash
copy .env.example .env
```

2. 编辑 `.env` 文件，填入实际配置：
```env
# SonarQube配置
SONARQUBE_URL=https://your-sonarqube-server.com
SONARQUBE_TOKEN=your_sonarqube_token

# Jira配置
JIRA_URL=https://your-jira-instance.atlassian.net
JIRA_EMAIL=your_email@company.com
JIRA_API_TOKEN=your_jira_api_token

# Git配置（可选，用于项目自动匹配和MR创建）
GIT_REPOSITORY_PATH=/path/to/your/local/repository
GIT_REMOTE_URL=https://gitlab.com/your-username/your-project.git
GIT_USERNAME=your_username
GIT_TOKEN=your_git_token

# GitLab配置（用于创建Merge Request）
GITLAB_URL=https://gitlab.com
GITLAB_TOKEN=your_gitlab_token

# AI模型配置（LangChain架构增强版）⭐ NEW!
AI_PROVIDER=openai                    # 支持 openai 或 anthropic
OPENAI_API_KEY=your_openai_api_key    # GPT-4 专业修复
ANTHROPIC_API_KEY=your_anthropic_key  # Claude 4.0 专门优化
AI_MODEL=gpt-4                        # 推荐：gpt-4, claude-3-opus-20240229

# 日志配置
LOG_LEVEL=INFO
```

## 🎯 使用方法

### 🚀 快速开始

使用Poetry（推荐）：
```bash
# 设置开发环境
make setup
# 或 Windows用户使用
make.bat setup

# 测试连接
poetry run python test_connections.py
# 或使用简化命令
make run-test
```

### 1. 📋 连接测试和验证
```bash
# 测试所有服务连接
python run.py test

# 使用Poetry
poetry run python run.py test

# 直接运行测试脚本
python test_connections.py
```

**测试内容包括：**
- ✅ SonarQube API连接和权限
- ✅ Jira API连接和用户验证
- ✅ Git仓库连接（如配置）
- ✅ AI服务连接（如配置）
- ✅ SQLite数据库状态

### 2. 🔍 项目管理和分析
```bash
# 列出所有可用的SonarQube和Jira项目
python run.py projects --list

# 自动发现项目匹配关系
python run.py projects --discover

# 分析特定SonarQube项目的Critical问题
python run.py projects --analyze PROJECT_KEY

# 交互式项目选择和管理
python run.py projects --interactive
```

### 3. 📋 创建Jira任务（第一阶段核心功能）
```bash
# 使用快速启动脚本
python run.py jira

# 使用Poetry运行
poetry run python run.py jira

# 直接运行核心模块
python -m src.sonar_resolve.main

# 指定特定项目
python run.py jira --project PROJECT_KEY
```

**功能说明：**
- 🔍 批量扫描所有SonarQube Critical问题
- 📊 按项目自动分组处理
- 🎯 智能匹配或自动创建Jira项目
- 📝 创建包含代码片段和规则信息的详细任务
- 💾 SQLite缓存避免重复创建

### 4. 🤖 AI自动修复（第二阶段功能）
```bash
# 使用快速启动脚本
python run.py autofix

# 使用Poetry运行
poetry run python run.py autofix

# 直接运行AI修复模块
python -m src.sonar_resolve.auto_fix

# 仅修复代码，不创建Jira任务
python run.py autofix --no-jira

# 仅测试AI连接
python run.py autofix --test-only
```

**AI修复功能：**
- 🤖 LangChain架构的专业代码修复
- 📝 自动生成Git提交和分支
- 🔀 创建详细的Merge Request
- 📊 生成修复前后对比报告

### 开发工具

```bash
# 运行测试
make test

# 代码格式化
make format

# 代码检查
make lint

# 类型检查
make type-check

# 运行所有检查
make pre-commit
```

## 📁 项目结构

```
SonarResolve/
├── 📝 README.md                     # 项目说明文档
├── 🚀 run.py                        # 主入口脚本
├── ⚙️ quick_start.py                # 快速启动脚本
├── 🧪 test_connections.py          # 连接测试脚本
├── 📦 pyproject.toml                # Poetry配置和项目元数据
├── 🔒 poetry.lock                   # 依赖版本锁定文件
├── 🔧 .env.example                  # 配置文件模板
├── 📊 Makefile / make.bat           # 构建和开发命令
├── 📂 src/sonar_resolve/            # 主要源代码目录
│   ├── 🔧 __init__.py
│   ├── 🤖 auto_fix.py               # AI自动修复主程序
│   ├── 📋 main.py                   # Jira任务创建主程序
│   ├── 📂 core/                     # 核心模块
│   │   ├── ⚙️ config.py             # 配置管理
│   │   └── 📊 models.py             # 数据模型定义
│   ├── 📂 clients/                  # 外部API客户端
│   │   ├── 🤖 ai_client.py          # AI服务客户端 (OpenAI/Anthropic)
│   │   ├── 🔧 git_client.py         # Git操作客户端
│   │   ├── 🎫 jira_client.py        # Jira API客户端
│   │   └── 📊 sonarqube_client.py   # SonarQube API客户端
│   └── 📂 utils/                    # 工具模块
│       └── 💾 project_db.py         # SQLite数据库管理
├── 📂 scripts/                      # 辅助脚本
│   ├── 🧪 test_independent_db.py    # 独立数据库测试
│   ├── 🔄 test_main_cache_integration.py # 缓存集成测试
│   └── 📊 test_simplified_db.py     # 简化数据库测试
├── 📂 tests/                        # 单元测试
│   ├── 🧪 test_models.py
│   └── 🧪 test_sonarqube_client.py
├── 📂 docs/                         # 详细文档
│   ├── 🚀 QUICK_START_JIRA.md       # 快速开始指南
│   ├── 🔧 CONNECTION_TEST.md        # 连接测试指南
│   ├── ⚙️ CONFIGURATION.md         # 配置参数说明
│   ├── 📊 SONAR_TO_JIRA_WORKFLOW.md # 核心工作流程
│   ├── 🤖 LANGCHAIN_AI_GUIDE.md     # AI集成指南
│   ├── 💾 SQLITE_CACHE_GUIDE.md     # 缓存机制说明
│   ├── 📦 POETRY_GUIDE.md           # Poetry使用指南
│   ├── 🔄 GIT_AUTO_DISCOVERY.md     # Git自动发现
│   ├── 🏗️ PROJECT_STRUCTURE.md      # 项目架构说明
│   ├── 🔧 API_EXAMPLES.md           # API使用示例
│   ├── 📈 WORKFLOW_DIAGRAMS.md      # 流程图说明
│   ├── 🏷️ JIRA_LABELS_FIX.md       # 标签处理优化
│   ├── 🐍 PYTHON_COMPATIBILITY.md   # Python兼容性
│   ├── 📊 SIMPLIFIED_SQLITE_IMPLEMENTATION.md # 数据库设计
│   ├── 🔬 LANGCHAIN_IMPLEMENTATION_REPORT.md # 技术实现报告
│   └── 📝 CHANGELOG.md              # 版本更新日志
└── 📂 logs/                         # 日志文件目录 (运行时生成)
    └── 📄 sonar_resolve_*.log       # 应用日志文件
```

## 📋 Jira任务信息 ⭐ 升级!

每个自动创建的Jira任务包含以下丰富信息：

### 📊 基础信息
- ✅ **问题描述**：来自SonarQube的详细问题说明
- ✅ **受影响文件**：精确的文件路径和代码行号
- ✅ **问题严重等级**：Critical级别标识
- ✅ **相关项目**：SonarQube项目关联信息
- ✅ **创建时间**：问题发现和更新时间

### 🔧 规则详细信息 ⭐ 新增!
- ✅ **规则Key**：SonarQube规则标识符
- ✅ **规则名称**：规则的友好名称
- ✅ **规则描述**：完整的规则说明（自动清理HTML）
- ✅ **规则类型**：Bug、Vulnerability、Code Smell等
- ✅ **规则标签**：相关技术标签

### 📖 代码片段信息 ⭐ 新增!
- ✅ **受影响代码**：直接从SonarQube获取的代码片段
- ✅ **上下文代码**：问题周围的代码上下文
- ✅ **精确标记**：用箭头标记具体问题行
- ✅ **HTML清理**：自动清理代码中的HTML标签
- ✅ **文件路径**：显示完整的文件路径信息

### 🏷️ 标签和分类
- ✅ **自动标签**：sonarqube、critical、automated
- ✅ **规则标签**：来自SonarQube规则的相关标签
- ✅ **问题类型**：根据SonarQube分类自动设置
- ✅ **优先级**：自动设置为Major级别

## 🔀 Merge Request信息

自动创建的Merge Request包含：
- ✅ 修复前后的代码diff
- ✅ 关联的SonarQube问题描述
- ✅ 详细的修复说明
- ✅ 影响文件列表
- ✅ 修复统计信息
- ✅ 自动生成的分支名称

## 🤖 支持的AI模型

### OpenAI
- GPT-4 (推荐)
- GPT-3.5-turbo
- 支持自定义API端点

### Anthropic
- Claude-3-Sonnet
- Claude-3-Haiku

## � 详细文档

### 核心功能文档
- 📋 **[SonarQube到Jira工作流程](docs/SONAR_TO_JIRA_WORKFLOW.md)** - 完整的批量处理流程说明
- 🚀 **[快速开始指南](docs/QUICK_START_JIRA.md)** - 5分钟上手指南
- 📊 **[工作流程图](docs/WORKFLOW_DIAGRAMS.md)** - 可视化流程图
- �🔧 **[API调用示例](docs/API_EXAMPLES.md)** - 详细的API使用示例

### 技术文档
- 🎯 **[LangChain AI指南](docs/LANGCHAIN_AI_GUIDE.md)** - AI大模型集成说明
- 📦 **[Poetry安装指南](docs/POETRY_GUIDE.md)** - 依赖管理详解
- 🔄 **[Git自动发现](docs/GIT_AUTO_DISCOVERY.md)** - Git仓库自动匹配
- 🏗️ **[项目结构说明](docs/PROJECT_STRUCTURE.md)** - 代码组织架构

## 🔧 工作流程

### 第一阶段：批量Jira任务创建 ⭐ 升级!
1. **批量扫描**：获取所有SonarQube Critical问题
2. **智能分组**：按项目自动分组处理
3. **项目匹配**：智能匹配或自动创建Jira项目
4. **任务创建**：为每个问题创建详细Jira任务
5. **报告生成**：生成完整的批量处理报告

### 第二阶段：AI自动修复
1. 获取SonarQube Critical问题
2. 使用AI分析并修复代码
3. 创建Git分支并提交修复
4. 推送到远程仓库
5. 创建Merge Request
6. （可选）创建Jira任务
7. 生成详细修复报告

## ⚠️ 注意事项

1. **权限配置**：确保SonarQube、Jira、Git和AI服务的API权限配置正确
2. **代码审查**：AI生成的修复建议进行人工审查
3. **测试验证**：修复后的代码应通过单元测试和集成测试
4. **备份重要**：在运行自动修复前备份重要代码
5. **环境隔离**：建议在开发环境中先测试流程

## 🔐 安全建议

- 使用环境变量存储敏感信息
- 定期轮换API令牌
- 限制Git仓库的访问权限
- 审查AI修复的代码更改

## 🐛 故障排除

### 常见问题

1. **连接失败**：检查网络和API令牌
2. **权限错误**：确认账户有相应的操作权限
3. **AI修复质量**：调整提示词或尝试不同模型
4. **Git推送失败**：检查仓库权限和分支保护规则

### 日志分析
- 查看生成的日志文件了解详细错误信息
- 使用 `LOG_LEVEL=DEBUG` 获取更详细的调试信息

## 📈 扩展功能

可根据需要扩展以下功能：
- 支持更多AI服务提供商
- 集成更多代码托管平台（GitHub、Bitbucket等）
- 添加代码质量评估
- 集成CI/CD流水线
- 支持批量项目处理