# SonarQube到Jira任务创建 - 快速开始指南

## 🚀 快速开始

### 1. 配置环境变量

创建 `.env` 文件：
```bash
# SonarQube配置
SONARQUBE_URL=https://your-sonarqube-server.com
SONARQUBE_TOKEN=your_sonar_token

# Jira配置  
JIRA_URL=https://your-jira-server.com
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your_jira_api_token
```

### 2. 安装依赖

```bash
pip install jira requests python-dotenv GitPython python-gitlab
```

### 3. 测试连接

```bash
python run.py test
```

### 4. 执行批量处理

```bash
python run.py jira
```

## 📋 执行流程

```
1. 扫描所有SonarQube Critical问题
   ↓
2. 按项目分组
   ↓  
3. 匹配或创建Jira项目
   ↓
4. 批量创建Jira任务
   ↓
5. 生成处理报告
```

## 📊 预期结果

- ✅ 自动创建缺失的Jira项目
- ✅ 为每个Critical问题创建Jira任务
- ✅ 避免重复任务创建
- ✅ 生成详细的处理报告

## 🔧 故障排除

**连接失败？**
- 检查URL和凭据
- 确认网络连接

**权限错误？**  
- 验证SonarQube Token权限
- 检查Jira用户权限

**依赖缺失？**
```bash
pip install -r requirements.txt
```

更多详细信息请参考 [完整工作流程文档](SONAR_TO_JIRA_WORKFLOW.md)。
