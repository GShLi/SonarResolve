# SonarResolve AI自动修复功能

## 🚀 新功能介绍

SonarResolve 现在支持AI自动修复功能！通过集成LangChain和大模型（OpenAI），可以自动分析和修复SonarQube检测到的Critical问题。

## 📋 功能特点

### 🤖 AI自动修复

- 自动获取SonarQube Critical问题
- 智能分析问题根因和影响
- 生成高质量的修复代码
- 自动创建Git分支和提交
- 自动创建GitLab Merge Request

### 🔄 完整的工作流程

1. **问题获取**: 从SonarQube获取Critical问题
2. **仓库准备**: 自动发现并克隆/更新GitLab仓库
3. **AI分析**: 使用大模型分析问题根因
4. **代码修复**: 生成符合最佳实践的修复代码
5. **质量验证**: AI验证修复质量和合规性
6. **自动提交**: 创建分支、提交代码、推送到远程
7. **MR创建**: 自动创建详细的Merge Request

## 🛠️ 环境配置

### 必需依赖

```bash
pip install langchain langchain-openai python-gitlab requests python-dotenv
```

### 环境变量配置

复制 `env_template.txt` 为 `.env` 并配置以下变量：

#### SonarQube配置

```bash
SONARQUBE_URL=https://your-sonarqube-server.com
SONARQUBE_TOKEN=your_sonarqube_token
```

#### GitLab配置

```bash
GITLAB_URL=https://your-gitlab-server.com
GITLAB_TOKEN=your_gitlab_access_token
LOCAL_WORKSPACE=./workspace
```

#### AI模型配置

```bash
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=http://your-litellm-proxy:8000  # LiteLLM代理地址
AI_MODEL=gpt-4
AI_TEMPERATURE=0.1
```

## 🚀 使用方法

### 统一启动脚本（推荐）

```bash
# AI自动修复所有项目
python run.py --mode ai-fix

# 修复指定项目
python run.py --mode ai-fix --project MY_PROJECT_KEY

# 连接测试
python run.py --mode ai-fix --test

# 试运行（分析但不修复）
python run.py --mode ai-fix --dry-run

# Jira任务创建（原功能）
python run.py --mode jira
```

### 独立AI修复脚本

```bash
# 修复所有项目
python ai_fix.py

# 修复指定项目
python ai_fix.py --project MY_PROJECT_KEY

# 连接测试
python ai_fix.py --test

# 试运行模式
python ai_fix.py --dry-run
```

### 原始主脚本（已升级）

```bash
# AI修复模式
python -m sonar_tools.main --mode ai-fix

# Jira模式（默认）
python -m sonar_tools.main --mode jira
```

## 🔍 使用示例

### 1. 首次使用 - 连接测试

```bash
python run.py --mode ai-fix --test
```

确保所有服务连接正常。

### 2. 试运行 - 查看问题

```bash
python run.py --mode ai-fix --dry-run
```

分析将要修复的问题，不实际修复。

### 3. 开始修复

```bash
python run.py --mode ai-fix
```

自动修复所有项目的Critical问题。

### 4. 修复特定项目

```bash
python run.py --mode ai-fix --project "my-java-project"
```

只修复指定项目的问题。

## 📊 修复流程详解

### 阶段1：问题分析

AI会分析每个SonarQube问题：

- 问题类型和严重性
- 根本原因分析
- 风险等级评估
- 修复复杂度

### 阶段2：代码修复

- 生成符合最佳实践的修复代码
- 保持原有功能逻辑
- 遵循编程语言规范
- 确保代码可读性

### 阶段3：质量验证

- SonarQube合规性检查
- 功能完整性验证
- 代码质量评估
- 安全性审查

### 阶段4：自动提交

- 创建修复分支
- 生成规范的提交信息
- 推送到远程仓库
- 创建详细的MR

## 🔧 配置选项

### AI模型配置

```bash
AI_MODEL=gpt-4              # 使用的模型
AI_TEMPERATURE=0.1          # 创造性（0-1）
AI_MAX_TOKENS=4000          # 最大令牌数
AI_CODE_CONTEXT_LINES=10    # 代码上下文行数
AI_MAX_RETRIES=3            # 最大重试次数
```

### GitLab配置

```bash
GITLAB_URL=https://gitlab.company.com
GITLAB_TOKEN=glpat-xxxxxxxxxxxxxxxxxxxx
LOCAL_WORKSPACE=./workspace  # 本地工作目录
```

## 📝 输出示例

### 成功修复示例

```
🚀 开始AI自动修复...
📁 为项目准备Git仓库: my-java-project
✅ 仓库准备完成: ./workspace/my-java-project
🔍 开始修复问题: AXnJg1K2F8eY3hZ7wQ9s
🤖 成功分析问题: AXnJg1K2F8eY3hZ7wQ9s
🛠️ 成功生成修复方案: AXnJg1K2F8eY3hZ7wQ9s
✅ 修复验证通过: AXnJg1K2F8eY3hZ7wQ9s
💾 成功修复问题: AXnJg1K2F8eY3hZ7wQ9s
🌿 分支创建成功: fix/sonar-critical-1691234567
📝 提交成功: fix: 修复 3 个SonarQube Critical问题
🚀 分支推送成功: fix/sonar-critical-1691234567
🔗 成功创建Merge Request: https://gitlab.company.com/project/-/merge_requests/123
🎉 AI自动修复完成
```

## ⚠️ 注意事项

1. **代码审查**: AI生成的代码需要人工审查
2. **测试验证**: 建议在修复后进行完整测试
3. **权限要求**: 确保GitLab token有足够权限
4. **资源消耗**: AI修复会消耗OpenAI API配额
5. **备份数据**: 重要代码建议先备份

## 🐛 故障排除

### 常见问题

#### 1. 连接测试失败

```bash
# 检查网络连接和配置
python run.py --mode ai-fix --test
```

#### 2. GitLab权限不足

确保GitLab token有以下权限：

- `api`
- `read_repository`
- `write_repository`

#### 3. AI响应格式错误

检查OpenAI API配额和模型可用性。

#### 4. 代码修复失败

查看日志文件获取详细错误信息：

```bash
tail -f logs/sonar_resolve.log
```

## 📈 性能优化

- 使用 `--project` 参数处理特定项目
- 调整 `AI_MAX_TOKENS` 控制响应长度
- 使用本地LiteLLM代理减少延迟
- 定期清理 `LOCAL_WORKSPACE` 目录

## 🆕 版本更新

当前版本支持：

- ✅ OpenAI GPT-4/GPT-3.5集成
- ✅ LiteLLM代理支持
- ✅ GitLab自动发现和MR创建
- ✅ 多项目批量处理
- ✅ 质量验证和回滚机制

计划功能：

- 🔄 支持更多AI提供商
- 🔄 增量修复模式
- 🔄 修复效果统计
- 🔄 自定义修复策略
