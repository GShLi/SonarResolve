# API调用示例和数据格式

## SonarQube API调用

### 1. 获取所有Critical问题

**请求：**
```http
GET /api/issues/search?severities=CRITICAL&statuses=OPEN,CONFIRMED,REOPENED&ps=500&p=1
Authorization: Bearer {SONARQUBE_TOKEN}
```

**响应示例：**
```json
{
  "total": 25,
  "p": 1,
  "ps": 500,
  "issues": [
    {
      "key": "AYxxx",
      "rule": "java:S2589",
      "severity": "CRITICAL",
      "component": "my-project:src/main/java/com/example/Service.java",
      "project": "my-project",
      "line": 45,
      "message": "Remove this expression which always evaluates to \"true\"",
      "type": "BUG",
      "status": "OPEN",
      "creationDate": "2025-08-05T10:30:00+0000",
      "updateDate": "2025-08-05T10:30:00+0000"
    }
  ]
}
```

### 2. 获取项目信息

**请求：**
```http
GET /api/components/search?qualifiers=TRK&ps=500
Authorization: Bearer {SONARQUBE_TOKEN}
```

**响应示例：**
```json
{
  "components": [
    {
      "key": "my-project",
      "name": "My Project",
      "qualifier": "TRK",
      "description": "项目描述"
    }
  ]
}
```

## Jira API调用

### 1. 获取所有项目

**请求：**
```http
GET /rest/api/2/project
Authorization: Basic {BASE64(email:api_token)}
```

**响应示例：**
```json
[
  {
    "key": "TEST",
    "id": "10000",
    "name": "Test Project",
    "lead": {
      "displayName": "项目负责人"
    }
  }
]
```

### 2. 创建项目

**请求：**
```http
POST /rest/api/2/project
Content-Type: application/json
Authorization: Basic {BASE64(email:api_token)}

{
  "key": "SONAR1",
  "name": "[SonarQube] My Project",
  "description": "自动创建的项目，用于管理SonarQube项目 my-project 的Critical问题",
  "lead": "user@company.com",
  "assigneeType": "PROJECT_LEAD"
}
```

### 3. 创建问题

**请求：**
```http
POST /rest/api/2/issue
Content-Type: application/json
Authorization: Basic {BASE64(email:api_token)}

{
  "fields": {
    "project": {"key": "SONAR1"},
    "summary": "[SonarQube Critical] java:S2589: src/main/java/com/example/Service.java",
    "description": "*SonarQube Critical Issue 自动创建任务*\n\n*问题描述:*\nRemove this expression which always evaluates to \"true\"\n\n*受影响文件:*\nsrc/main/java/com/example/Service.java:45\n\n*问题严重等级:*\nCRITICAL\n\n*相关项目:*\nmy-project\n\n*规则:*\njava:S2589\n\n*问题类型:*\nBUG",
    "issuetype": {"name": "Task"},
    "priority": {"name": "High"},
    "labels": ["sonarqube", "critical", "automated"]
  }
}
```

**响应示例：**
```json
{
  "key": "SONAR1-1",
  "self": "https://jira.company.com/rest/api/2/issue/10001"
}
```

### 4. 检查问题是否存在

**请求：**
```http
GET /rest/api/2/search?jql=project=SONAR1 AND summary~"AYxxx"&maxResults=1
Authorization: Basic {BASE64(email:api_token)}
```

## 数据转换示例

### SonarQube问题到Jira任务的转换

**输入（SonarQube问题）：**
```python
{
  "key": "AYxxx",
  "rule": "java:S2589", 
  "severity": "CRITICAL",
  "component": "my-project:src/main/java/Service.java",
  "project": "my-project",
  "line": 45,
  "message": "Remove this expression which always evaluates to \"true\"",
  "type": "BUG",
  "status": "OPEN"
}
```

**输出（Jira任务）：**
```python
{
  "summary": "[SonarQube Critical] java:S2589: src/main/java/Service.java",
  "description": """*SonarQube Critical Issue 自动创建任务*

*问题描述:*
Remove this expression which always evaluates to "true"

*受影响文件:*
src/main/java/Service.java:45

*问题严重等级:*
CRITICAL

*相关项目:*
my-project

*规则:*
java:S2589

*问题类型:*
BUG""",
  "project_key": "MYPROJ",
  "issue_type": "Task",
  "priority": "High",
  "labels": ["sonarqube", "critical", "automated", "bug"]
}
```

### 项目Key生成示例

```python
# 输入的SonarQube项目Key示例
sonar_keys = [
    "my-awesome-project",      # → MYAWESOME  
    "web-app-frontend",        # → WEBAPP
    "backend-api-service",     # → BACKEND
    "legacy-system-old",       # → LEGACY
    "mobile-ios-app",          # → MOBILE
    "data-processing-engine",  # → DATA
    "test-automation-suite",   # → TEST
    "123-numeric-project",     # → S123NUM
    "a",                       # → SA
    "special-chars!@#$%",      # → SPECIAL
]

# 生成规则：
# 1. 提取字母和数字
# 2. 转换为大写
# 3. 限制长度2-10字符
# 4. 确保首字符为字母
# 5. 如果太短添加S前缀
```

## 错误响应处理

### SonarQube错误响应

```json
{
  "errors": [
    {
      "msg": "Insufficient privileges"
    }
  ]
}
```

### Jira错误响应

```json
{
  "errorMessages": [
    "Project key 'INVALID' is invalid - must be all uppercase"
  ],
  "errors": {
    "key": "Project key 'INVALID' is invalid - must be all uppercase"
  }
}
```

## 批处理数据结构

### 问题分组结构

```python
issues_by_project = {
    "my-project-1": [
        SonarIssue(key="AY1", rule="java:S2589", ...),
        SonarIssue(key="AY2", rule="java:S1192", ...),
        SonarIssue(key="AY3", rule="java:S106", ...)
    ],
    "web-application": [
        SonarIssue(key="AY4", rule="javascript:S3776", ...),
        SonarIssue(key="AY5", rule="javascript:S1541", ...)
    ],
    "backend-service": [
        SonarIssue(key="AY6", rule="python:S5547", ...)
    ]
}
```

### 处理结果结构

```python
batch_results = {
    "start_time": datetime(2025, 8, 6, 14, 50, 23),
    "end_time": datetime(2025, 8, 6, 14, 52, 58),
    "duration": timedelta(0, 155),  # 2分35秒
    "total_projects": 3,
    "total_sonar_issues": 6,
    "total_jira_tasks_created": 5,
    "successful_projects": 2,
    "failed_projects": 1,
    "created_projects": ["MYPROJ", "WEBAPP"],
    "project_results": {
        "my-project-1": {
            "sonar_project_key": "my-project-1",
            "sonar_issues_count": 3,
            "jira_project_key": "MYPROJ",
            "jira_project_created": True,
            "jira_tasks_created": 3,
            "created_tasks": ["MYPROJ-1", "MYPROJ-2", "MYPROJ-3"],
            "errors": [],
            "success": True
        },
        "web-application": {
            "sonar_project_key": "web-application",
            "sonar_issues_count": 2,
            "jira_project_key": "WEBAPP",
            "jira_project_created": True,
            "jira_tasks_created": 2,
            "created_tasks": ["WEBAPP-1", "WEBAPP-2"],
            "errors": [],
            "success": True
        },
        "backend-service": {
            "sonar_project_key": "backend-service",
            "sonar_issues_count": 1,
            "jira_project_key": None,
            "jira_project_created": False,
            "jira_tasks_created": 0,
            "created_tasks": [],
            "errors": ["创建Jira项目失败: 权限不足"],
            "success": False
        }
    },
    "errors": []
}
```

## 性能考虑

### API调用优化

```python
# 分页获取大量问题
def get_all_critical_issues(page_size=500):
    issues = []
    page = 1
    
    while True:
        params = {
            'severities': 'CRITICAL',
            'statuses': 'OPEN,CONFIRMED,REOPENED',
            'ps': page_size,
            'p': page
        }
        
        response = sonar_client.get('issues/search', params)
        page_issues = response['issues']
        issues.extend(page_issues)
        
        if len(page_issues) < page_size:
            break
            
        page += 1
    
    return issues
```

### 批量处理优化

```python
# 批量创建任务，减少API调用
def create_issues_batch(issues, project_key, batch_size=10):
    created_tasks = []
    
    for i in range(0, len(issues), batch_size):
        batch = issues[i:i + batch_size]
        
        # 处理一批任务
        for issue in batch:
            if not issue_exists(issue, project_key):
                task_key = create_issue(issue, project_key)
                if task_key:
                    created_tasks.append(task_key)
        
        # 避免API限制，添加延迟
        time.sleep(0.1)
    
    return created_tasks
```

这些示例展示了整个系统中涉及的所有API调用和数据格式，帮助理解系统的具体实现细节。
