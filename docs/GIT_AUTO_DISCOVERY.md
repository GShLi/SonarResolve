# Git自动仓库发现功能使用指南

## 概述

SonarResolve现在支持根据SonarQube项目名自动发现和管理GitLab仓库，无需手动配置Git仓库路径。

## 主要特性

✅ **自动仓库发现**: 根据SonarQube项目名在GitLab中查找匹配的仓库
✅ **智能匹配**: 支持项目名、路径名和模糊匹配
✅ **自动克隆**: 首次使用时自动克隆仓库到本地
✅ **自动更新**: 每次运行前自动执行git pull确保代码最新
✅ **多项目支持**: 可以同时管理多个项目的仓库
✅ **分支管理**: 自动创建修复分支并推送到GitLab

## 配置方法

### 1. 环境变量配置 (.env文件)

```env
# GitLab配置（用于仓库管理和Merge Request）
GITLAB_URL=https://gitlab.com  # 或者你的私有GitLab服务器
GITLAB_TOKEN=your_gitlab_token

# 本地工作目录配置（自动创建基于项目名的子目录）
LOCAL_WORKSPACE=/path/to/local/workspace  # 例如: C:\workspace 或 ./workspace
```

### 2. 移除的配置项

以下配置项已不再需要（已从.env文件中移除）：
- ~~GIT_REPOSITORY_PATH~~
- ~~GIT_REMOTE_URL~~

## 工作流程

### 1. 项目仓库准备

```python
from sonar_tools.utils.git_manager import GitClient

repo_manager = GitClient()

# 根据SonarQube项目名准备仓库
success, local_path, repo_info = repo_manager.prepare_repository_for_project("my-project")

if success:
    print(f"仓库准备完成: {local_path}")
    print(f"GitLab项目: {repo_info['full_path']}")
```

### 2. 仓库查找
```python
# 在GitLab中搜索项目
repo_info = repo_manager.find_repository_by_project_name("my-project")

if repo_info:
    print(f"找到项目: {repo_info['name']}")
    print(f"克隆URL: {repo_info['clone_url']}")
    print(f"默认分支: {repo_info['default_branch']}")
```

### 3. 克隆或更新仓库
```python
# 自动克隆或更新仓库
success, local_path = repo_manager.clone_or_update_repository("my-project")

if success:
    print(f"仓库已准备完成: {local_path}")
```

## 匹配规则

系统会按以下优先级查找匹配的GitLab项目：

1. **完全匹配**: 项目名完全相同
2. **路径匹配**: 项目路径（path）完全相同
3. **包含匹配**: 项目名包含搜索的名称
4. **第一个匹配**: 如果没有完美匹配，使用第一个搜索结果

## 目录结构

本地工作目录结构：
```
LOCAL_WORKSPACE/
├── project-1/           # 项目1的仓库
│   ├── .git/
│   ├── src/
│   └── ...
├── project-2/           # 项目2的仓库
│   ├── .git/
│   ├── src/
│   └── ...
└── ...
```

## 自动修复流程

### 1. 使用AutoFixProcessor

```python
from sonar_tools.utils.git_manager import AutoFixProcessor

processor = AutoFixProcessor()

# 处理项目的自动修复
fixes = [
    {
        'file_path': 'src/main.java',
        'old_code': 'if (x = 5)',
        'new_code': 'if (x == 5)'
    }
]

success = processor.process_project_fixes("my-project", fixes)
```

### 2. 完整的自动修复流程
1. 根据项目名找到GitLab仓库
2. 克隆或更新本地仓库
3. 创建新的修复分支（格式：`fix/sonar-issues-{timestamp}`）
4. 应用代码修复
5. 提交更改
6. 推送分支到GitLab

## 错误处理

### 常见问题和解决方案

1. **GitLab连接失败**
   - 检查GITLAB_URL和GITLAB_TOKEN配置
   - 确保token有足够的权限

2. **项目未找到**
   - 确认SonarQube项目名拼写正确
   - 检查在GitLab中是否有访问该项目的权限
   - 尝试使用部分项目名进行搜索

3. **Git操作失败**
   - 确保本地有git命令
   - 检查网络连接
   - 确认GitLab token有push权限

## 测试功能

运行测试脚本验证配置：

```bash
# 简单配置测试
poetry run python scripts/test_simple_git.py

# 完整功能测试
poetry run python scripts/test_git_discovery.py
```

## 迁移指南

### 从手动配置迁移到自动发现

1. **备份现有配置**
   ```bash
   cp .env .env.backup
   ```

2. **更新.env文件**
   ```env
   # 移除这些行：
   # GIT_REPOSITORY_PATH=/path/to/repo
   # GIT_REMOTE_URL=https://gitlab.com/user/repo.git
   
   # 添加这些行：
   GITLAB_URL=https://gitlab.com
   GITLAB_TOKEN=your_gitlab_token
   LOCAL_WORKSPACE=/path/to/workspace
   ```

3. **测试新功能**
   ```bash
   poetry run python scripts/test_simple_git.py
   ```

4. **运行自动修复**
   - 系统会自动找到项目对应的GitLab仓库
   - 自动克隆到LOCAL_WORKSPACE目录
   - 执行修复并创建Merge Request

## 优势

✅ **减少配置**: 不需要为每个项目手动配置Git路径
✅ **自动化**: 自动发现、克隆、更新仓库
✅ **智能匹配**: 支持多种项目名匹配方式
✅ **多项目支持**: 可以同时处理多个项目
✅ **错误恢复**: 自动处理常见的Git操作问题
✅ **最新代码**: 每次运行前自动更新确保使用最新代码

## 注意事项

- 确保GitLab token有足够的权限（read_repository, write_repository）
- 首次克隆大型仓库可能需要一些时间
- 本地工作目录需要足够的磁盘空间
- 建议定期清理本地工作目录中不再需要的项目
