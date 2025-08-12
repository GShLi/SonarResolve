# 配置参数详细说明

## 概述

SonarResolve 使用环境变量进行配置管理，支持灵活的配置选项来适应不同的使用场景。本文档详细说明了所有可用的配置参数。

## 📋 完整配置清单

### 🔧 SonarQube配置

| 参数 | 必需 | 描述 | 示例 |
|------|------|------|------|
| `SONARQUBE_URL` | ✅ | SonarQube服务器地址 | `https://sonar.company.com` |
| `SONARQUBE_TOKEN` | ✅ | SonarQube API认证令牌 | `squ_abc123...` |
| `SONARQUBE_FETCH_CODE_SNIPPET` | ❌ | 是否获取代码片段 | `true` (默认: `true`) |

### 🎫 Jira配置

| 参数 | 必需 | 描述 | 示例 |
|------|------|------|------|
| `JIRA_URL` | ✅ | Jira服务器地址 | `https://company.atlassian.net` |
| `JIRA_EMAIL` | ✅ | Jira账户邮箱 | `user@company.com` |
| `JIRA_API_TOKEN` | ✅ | Jira API令牌 | `ATATT3x...` |
| `JIRA_TASK_PREFIX` | ❌ | 任务标题前缀 | `[SONAR]` (默认: `[质量管理]`) |
| `JIRA_PROJECT_LEAD` | ❌ | 默认项目负责人 | `john.doe` |
| `JIRA_INCLUDE_CODE_SNIPPET` | ❌ | 任务中包含代码片段 | `true` (默认: `true`) |

### 🔀 Git配置

| 参数 | 必需 | 描述 | 示例 |
|------|------|------|------|
| `GIT_REPOSITORY_PATH` | ❌ | 本地仓库路径 | `/path/to/repo` |
| `GIT_REMOTE_URL` | ❌ | 远程仓库URL | `https://gitlab.com/user/project.git` |
| `GIT_USERNAME` | ❌ | Git用户名 | `git_user` |
| `GIT_TOKEN` | ❌ | Git访问令牌 | `glpat-xxx...` |
| `GIT_DEFAULT_BRANCH` | ❌ | 默认分支名 | `main` (默认: `main`) |

### 🚀 GitLab配置

| 参数 | 必需 | 描述 | 示例 |
|------|------|------|------|
| `GITLAB_URL` | ❌ | GitLab服务器地址 | `https://gitlab.com` |
| `GITLAB_TOKEN` | ❌ | GitLab访问令牌 | `glpat-xxx...` |
| `GITLAB_PROJECT_ID` | ❌ | GitLab项目ID | `12345` |

### 🤖 AI模型配置

| 参数 | 必需 | 描述 | 示例 |
|------|------|------|------|
| `AI_PROVIDER` | ❌ | AI服务提供商 | `openai` 或 `anthropic` |
| `AI_MODEL` | ❌ | AI模型名称 | `gpt-4`, `claude-3-5-sonnet-20241022` |
| `OPENAI_API_KEY` | ⚠️ | OpenAI API密钥 | `sk-xxx...` |
| `OPENAI_BASE_URL` | ❌ | OpenAI API基础URL | `https://api.openai.com/v1` |
| `ANTHROPIC_API_KEY` | ⚠️ | Anthropic API密钥 | `sk-ant-xxx...` |
| `AI_MAX_TOKENS` | ❌ | 最大令牌数 | `4000` (默认: `4000`) |
| `AI_TEMPERATURE` | ❌ | 生成温度 | `0.1` (默认: `0.1`) |

### 📊 日志配置

| 参数 | 必需 | 描述 | 示例 |
|------|------|------|------|
| `LOG_LEVEL` | ❌ | 日志级别 | `INFO`, `DEBUG`, `WARNING`, `ERROR` |
| `LOG_FILE` | ❌ | 日志文件路径 | `logs/sonar_resolve.log` |
| `LOG_MAX_SIZE` | ❌ | 日志文件最大大小(MB) | `10` (默认: `10`) |
| `LOG_BACKUP_COUNT` | ❌ | 日志备份文件数量 | `5` (默认: `5`) |

### 💾 数据库配置

| 参数 | 必需 | 描述 | 示例 |
|------|------|------|------|
| `DATABASE_PATH` | ❌ | SQLite数据库文件路径 | `db/project_status.db` (默认: `db/project_status.db`) |
| `DATABASE_BACKUP` | ❌ | 是否自动备份数据库 | `true` (默认: `false`) |

**注意**: 数据库路径可以是相对路径或绝对路径。相对路径基于项目根目录。

## 🔧 配置文件示例

### 基础配置 (.env)

```env
# SonarQube配置 (必需)
SONARQUBE_URL=https://sonar.company.com
SONARQUBE_TOKEN=squ_1234567890abcdef

# Jira配置 (必需)
JIRA_URL=https://company.atlassian.net
JIRA_EMAIL=developer@company.com
JIRA_API_TOKEN=ATATT3xFfGF0...

# 可选：自定义设置
JIRA_TASK_PREFIX=[代码质量]
LOG_LEVEL=INFO
```

### 完整配置示例

```env
# =================== SonarQube配置 ===================
SONARQUBE_URL=https://sonar.company.com
SONARQUBE_TOKEN=squ_1234567890abcdef1234567890abcdef12345678
SONARQUBE_FETCH_CODE_SNIPPET=true

# =================== Jira配置 ===================
JIRA_URL=https://company.atlassian.net
JIRA_EMAIL=developer@company.com
JIRA_API_TOKEN=ATATT3xFfGF0T1234567890abcdef
JIRA_TASK_PREFIX=[代码质量]
JIRA_PROJECT_LEAD=project.manager
JIRA_INCLUDE_CODE_SNIPPET=true

# =================== Git配置 ===================
GIT_REPOSITORY_PATH=/home/user/projects/myproject
GIT_REMOTE_URL=https://gitlab.company.com/team/project.git
GIT_USERNAME=git.user
GIT_TOKEN=glpat-xxxxxxxxxxxxxxxxxxxx
GIT_DEFAULT_BRANCH=main

# =================== GitLab配置 ===================
GITLAB_URL=https://gitlab.company.com
GITLAB_TOKEN=glpat-xxxxxxxxxxxxxxxxxxxx
GITLAB_PROJECT_ID=123

# =================== AI配置 ===================
AI_PROVIDER=openai
AI_MODEL=gpt-4
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
AI_MAX_TOKENS=4000
AI_TEMPERATURE=0.1

# =================== 日志配置 ===================
LOG_LEVEL=INFO
LOG_FILE=logs/sonar_resolve.log
LOG_MAX_SIZE=10
LOG_BACKUP_COUNT=5

# =================== 数据库配置 ===================
DATABASE_PATH=db/project_status.db
DATABASE_BACKUP=true
```

## 🎯 不同场景的配置

### 1. 仅Jira任务创建

最小配置，只创建Jira任务：

```env
SONARQUBE_URL=https://sonar.company.com
SONARQUBE_TOKEN=your_token
JIRA_URL=https://company.atlassian.net
JIRA_EMAIL=your@email.com
JIRA_API_TOKEN=your_jira_token
```

### 2. 包含AI自动修复

包含AI修复功能的配置：

```env
# 基础配置
SONARQUBE_URL=https://sonar.company.com
SONARQUBE_TOKEN=your_token
JIRA_URL=https://company.atlassian.net
JIRA_EMAIL=your@email.com
JIRA_API_TOKEN=your_jira_token

# Git配置 (AI修复需要)
GIT_REPOSITORY_PATH=/path/to/repo
GIT_REMOTE_URL=https://gitlab.com/user/project.git
GIT_USERNAME=git_user
GIT_TOKEN=git_token

# AI配置
AI_PROVIDER=openai
AI_MODEL=gpt-4
OPENAI_API_KEY=sk-your_openai_key
```

### 3. 开发调试配置

用于开发和调试的详细配置：

```env
# 启用详细日志
LOG_LEVEL=DEBUG
LOG_FILE=debug.log

# 禁用某些功能进行测试
SONARQUBE_FETCH_CODE_SNIPPET=false
JIRA_INCLUDE_CODE_SNIPPET=false

# 测试AI配置
AI_TEMPERATURE=0.2
AI_MAX_TOKENS=2000
```

## ⚙️ 配置验证

### 自动验证

系统启动时会自动验证关键配置：

```python
# 验证必需配置
python -c "from sonar_resolve.core.config import Config; Config.validate()"
```

### 手动验证

```bash
# 测试所有连接
python run.py test

# 验证特定配置
python -c "
from sonar_resolve.core.config import Config
print('SonarQube URL:', Config.SONARQUBE_URL)
print('Jira URL:', Config.JIRA_URL)
print('AI Provider:', Config.AI_PROVIDER)
"
```

## 🔐 安全最佳实践

### 1. 敏感信息管理

- 使用 `.env` 文件存储敏感配置
- 将 `.env` 添加到 `.gitignore`
- 不要在代码中硬编码敏感信息

### 2. 权限最小化

- SonarQube token只需要 `Browse` 权限
- Jira token只需要项目访问和任务创建权限
- Git token只需要仓库读写权限

### 3. 定期轮换

- 定期更新API令牌
- 监控令牌使用情况
- 设置令牌过期提醒

## 🚨 常见配置错误

### 1. URL格式错误

❌ 错误：
```env
SONARQUBE_URL=sonar.company.com  # 缺少协议
JIRA_URL=https://company.atlassian.net/  # 多余的尾部斜杠
```

✅ 正确：
```env
SONARQUBE_URL=https://sonar.company.com
JIRA_URL=https://company.atlassian.net
```

### 2. 布尔值配置错误

❌ 错误：
```env
SONARQUBE_FETCH_CODE_SNIPPET=True  # 大写
JIRA_INCLUDE_CODE_SNIPPET=1        # 数字
```

✅ 正确：
```env
SONARQUBE_FETCH_CODE_SNIPPET=true
JIRA_INCLUDE_CODE_SNIPPET=false
```

### 3. 路径配置错误

❌ 错误：
```env
GIT_REPOSITORY_PATH=~/projects/repo    # 波浪号不会展开
DATABASE_PATH=./data/db.sqlite         # 相对路径可能有问题
```

✅ 正确：
```env
GIT_REPOSITORY_PATH=/home/user/projects/repo
DATABASE_PATH=/full/path/to/data/db.sqlite
```

## 📋 配置检查清单

在部署前请检查：

- [ ] 所有必需的配置参数都已设置
- [ ] API令牌有足够的权限
- [ ] URL格式正确（包含协议，无多余斜杠）
- [ ] 文件路径使用绝对路径
- [ ] 布尔值使用小写 `true`/`false`
- [ ] `.env` 文件已添加到 `.gitignore`
- [ ] 运行连接测试验证配置正确性

---

💡 **提示**：使用 `python run.py test` 命令可以验证大部分配置是否正确。
