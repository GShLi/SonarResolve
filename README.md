# SonarQube自动修复与Jira集成工具

这是一个强大的Python工具，能够自动从SonarQube获取Critical级别的问题，使用**LangChain架构的AI大模型**进行专业代码修复，并集成Git和Jira工作流。

## 🚀 功能特性

### 智能项目管理
- 🔗 自动发现和匹配SonarQube与Jira项目
- 📊 基于项目名称、关键词、Git仓库URL的智能匹配
- 📋 项目列表浏览和分析
- 🎯 交互式项目选择
- 📈 项目问题统计和分析

### 第一阶段：Jira任务创建
- 🔍 自动获取SonarQube项目中的Critical问题
- 📋 为每个问题在Jira中创建详细任务
- 📊 生成处理报告
- 🔄 避免重复创建任务
- 📝 详细的日志记录

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

### 快速开始

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

### 1. 项目管理和分析
```bash
# 列出所有可用的SonarQube和Jira项目
python run.py projects --list

# 自动发现项目匹配（基于名称、关键词、Git URL等）
python run.py projects --discover

# 分析特定SonarQube项目的Critical问题
python run.py projects --analyze PROJECT_KEY

# 交互式项目选择
python run.py projects --interactive
```

### 2. 测试连接和自动项目发现
```bash
# 使用新的快速启动脚本
python run.py test

# 或使用Poetry
poetry run sonar-test

# 或直接运行脚本
python scripts/test_connections.py
```

### 3. 仅创建Jira任务（第一阶段功能）
```bash
# 使用快速启动脚本
python run.py jira

# 使用Poetry
poetry run sonar-jira

# 或直接运行核心模块
python -m sonar_resolve.core.main
```

### 4. AI自动修复并创建Merge Request（第二阶段功能）
```bash
# 使用快速启动脚本
python run.py autofix

# 使用Poetry
poetry run sonar-autofix

# 直接运行模块
python -m sonar_resolve.core.auto_fix

# 仅修复代码，不创建Jira任务
python run.py autofix --no-jira

# 仅测试连接
python run.py autofix --test-only
```

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
├── main.py                      # 第一阶段：Jira任务创建
├── auto_fix.py                  # 第二阶段：AI自动修复主程序
├── config.py                    # 配置管理
├── models.py                    # 数据模型
├── sonarqube_client.py         # SonarQube API客户端
├── jira_client.py              # Jira API客户端
├── ai_client.py                # AI修复客户端（OpenAI/Anthropic）
├── git_manager.py              # Git和GitLab操作管理
├── test_connections.py         # 连接测试脚本
├── tests/                      # 测试文件目录
│   ├── __init__.py
│   ├── test_models.py
│   └── test_sonarqube_client.py
├── pyproject.toml              # Poetry配置和项目元数据
├── .pre-commit-config.yaml     # 预提交钩子配置
├── Makefile                    # Make命令（Linux/Mac）
├── make.bat                    # 批处理命令（Windows）
├── POETRY_GUIDE.md             # Poetry使用指南
├── .env.example               # 配置文件模板
└── README.md                  # 说明文档
```

## 📋 Jira任务信息

每个自动创建的Jira任务包含以下信息：
- ✅ 问题描述（来自SonarQube）
- ✅ 受影响的文件和代码行
- ✅ 问题严重等级（Critical）
- ✅ 相关项目名称
- ✅ SonarQube规则信息
- ✅ 问题类型和标签
- ✅ 创建时间

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

## 🔧 工作流程

### 第一阶段：Jira任务创建
1. 连接SonarQube获取Critical问题
2. 解析问题详情和位置信息
3. 在Jira中创建结构化任务
4. 生成处理报告

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