# 连接测试指南

## 概述

SonarResolve 提供了全面的连接测试功能，帮助您验证所有外部服务的连接状态，确保系统能够正常运行。

## 🧪 测试功能

### 支持的服务测试
- ✅ **SonarQube API连接测试**
- ✅ **Jira API连接测试**
- ✅ **Git仓库连接测试**
- ✅ **AI服务连接测试** (OpenAI/Anthropic)
- ✅ **SQLite数据库测试**

## 🚀 快速测试

### 使用快速命令

```bash
# 测试所有连接
python run.py test

# 使用Poetry
poetry run python run.py test

# 直接运行测试脚本
python test_connections.py
```

### 测试输出示例

```
🔧 SonarResolve - 服务连接测试
=====================================

✅ SonarQube连接测试成功
   服务器: https://sonar.example.com
   版本: 9.9.0

✅ Jira连接测试成功  
   服务器: https://jira.example.com
   当前用户: john.doe@company.com

✅ Git仓库连接测试成功
   仓库: https://gitlab.com/team/project.git
   当前分支: main

✅ AI服务连接测试成功
   提供商: OpenAI
   模型: gpt-4

✅ SQLite数据库测试成功
   路径: project_status.db
   表: created_projects, created_tasks

🎉 所有服务连接正常！
```

## ⚙️ 详细测试说明

### 1. SonarQube连接测试

测试内容：
- API认证验证
- 服务器连通性
- 权限检查
- 版本信息获取

配置要求：
```env
SONARQUBE_URL=https://your-sonarqube-server.com
SONARQUBE_TOKEN=your_sonarqube_token
```

### 2. Jira连接测试

测试内容：
- API认证验证
- 用户信息获取
- 项目访问权限
- 创建任务权限

配置要求：
```env
JIRA_URL=https://your-jira-server.com
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your_jira_api_token
```

### 3. Git仓库测试

测试内容：
- 远程仓库连接
- 推送权限验证
- 分支操作权限
- 认证状态检查

配置要求：
```env
GIT_REPOSITORY_PATH=/path/to/local/repo
GIT_REMOTE_URL=https://gitlab.com/user/project.git
GIT_USERNAME=your_username
GIT_TOKEN=your_git_token
```

### 4. AI服务测试

测试内容：
- API密钥验证
- 模型可用性检查
- 简单查询测试
- 响应格式验证

配置要求：
```env
AI_PROVIDER=openai  # 或 anthropic
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
AI_MODEL=gpt-4  # 或其他支持的模型
```

### 5. SQLite数据库测试

测试内容：
- 数据库文件访问
- 表结构验证
- 读写权限检查
- 索引完整性

## 🚨 故障排除

### 常见错误及解决方案

#### SonarQube连接失败
```
❌ SonarQube连接失败: 401 Unauthorized
```
**解决方案**：
- 检查 `SONARQUBE_TOKEN` 是否正确
- 确认token是否已过期
- 验证token是否有足够权限

#### Jira连接失败
```
❌ Jira连接失败: 403 Forbidden
```
**解决方案**：
- 检查 `JIRA_EMAIL` 和 `JIRA_API_TOKEN`
- 确认账户是否有项目访问权限
- 验证Jira实例URL是否正确

#### Git仓库连接失败
```
❌ Git连接失败: Permission denied
```
**解决方案**：
- 检查 `GIT_TOKEN` 权限
- 确认token是否有push权限
- 验证仓库URL格式

#### AI服务连接失败
```
❌ AI服务连接失败: Invalid API key
```
**解决方案**：
- 检查API密钥是否正确
- 确认账户余额是否充足
- 验证模型名称是否正确

## 🔧 高级测试选项

### 仅测试特定服务

```bash
# 仅测试SonarQube
python test_connections.py --sonar-only

# 仅测试Jira
python test_connections.py --jira-only

# 仅测试AI服务
python test_connections.py --ai-only
```

### 详细调试模式

```bash
# 启用详细日志
LOG_LEVEL=DEBUG python test_connections.py

# 保存测试报告
python test_connections.py --save-report
```

## 📊 测试报告

测试完成后，系统会生成详细的测试报告，包括：

- ✅ 成功的连接及详细信息
- ❌ 失败的连接及错误原因
- ⚠️ 警告信息和建议
- 📈 性能指标（响应时间等）
- 🔧 配置建议和优化提示

## 🎯 最佳实践

1. **定期测试**：在生产环境部署前运行完整测试
2. **环境隔离**：在不同环境中使用不同的配置
3. **权限最小化**：只给必要的最小权限
4. **密钥轮换**：定期更新API密钥和token
5. **监控告警**：设置连接失败的监控告警

## 🔐 安全注意事项

- 不要在日志中打印敏感信息
- 使用环境变量存储认证信息
- 定期检查和更新访问权限
- 监控异常的API调用模式

---

💡 **提示**：如果测试失败，请检查网络连接和防火墙设置，确保能够访问相关服务的API端点。
