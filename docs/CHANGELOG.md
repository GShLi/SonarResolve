# SonarResolve 更新日志

## v2.0.0 - Git自动仓库发现 (2024-01-XX)

### 🚀 重大功能更新

#### Git自动仓库发现和管理
- **新增**: 根据SonarQube项目名自动发现GitLab仓库
- **新增**: 智能项目匹配算法（完全匹配 > 路径匹配 > 包含匹配）
- **新增**: 自动克隆仓库到本地工作目录
- **新增**: 每次运行前自动执行git pull确保代码最新
- **新增**: 多项目支持，可同时管理多个仓库
- **新增**: `GitRepositoryManager` 类用于统一仓库管理
- **新增**: `AutoFixProcessor` 类用于自动化修复流程

#### 配置简化
- **移除**: 不再需要手动配置 `GIT_REPOSITORY_PATH` 和 `GIT_REMOTE_URL`
- **新增**: `LOCAL_WORKSPACE` 配置用于指定本地工作目录
- **简化**: GitLab配置现在同时用于仓库管理和MR创建

#### 项目结构标准化
- **重构**: 采用标准Python项目结构 `src/sonar_resolve/`
- **重构**: 模块化设计：`clients/`, `core/`, `utils/`
- **修复**: 所有import语句使用相对导入
- **优化**: 依赖管理，AI功能设为可选

### 📁 文件结构变更

#### 新增文件
```
src/sonar_resolve/utils/git_manager.py  # Git自动管理功能
scripts/test_git_discovery.py          # Git功能测试
scripts/test_simple_git.py             # 简化配置测试
docs/GIT_AUTO_DISCOVERY.md             # Git自动发现使用指南
.env.example                           # 更新的配置模板
```

#### 移动的文件
```
main.py → src/sonar_resolve/core/main.py
config.py → src/sonar_resolve/core/config.py
models.py → src/sonar_resolve/core/models.py
project_discovery.py → src/sonar_resolve/core/project_discovery.py
auto_fix.py → src/sonar_resolve/core/auto_fix.py
sonarqube_client.py → src/sonar_resolve/clients/sonarqube_client.py
jira_client.py → src/sonar_resolve/clients/jira_client.py
ai_client.py → src/sonar_resolve/clients/ai_client.py
git_manager.py → src/sonar_resolve/utils/git_manager.py
```

### 🔧 技术改进

#### 依赖管理
- **修复**: Python版本要求更新为 >=3.8.1 解决flake8兼容性
- **新增**: `python-gitlab` 库支持GitLab API集成
- **优化**: AI依赖设为可选，避免版本冲突

#### 错误处理
- **增强**: GitLab连接失败时的错误提示
- **增强**: 项目未找到时的详细说明
- **增强**: Git操作失败时的自动重试机制

#### 日志和监控
- **改进**: 详细的Git操作日志
- **新增**: 仓库发现过程的步骤记录
- **优化**: 错误日志包含具体的解决建议

### 🚦 配置迁移指南

#### 从v1.x迁移到v2.0

1. **备份现有配置**:
   ```bash
   cp .env .env.backup
   ```

2. **更新.env文件**:
   ```env
   # 移除这些配置（不再需要）:
   # GIT_REPOSITORY_PATH=/path/to/repo
   # GIT_REMOTE_URL=https://gitlab.com/user/repo.git
   
   # 添加新配置:
   GITLAB_URL=https://gitlab.com
   GITLAB_TOKEN=your_gitlab_token
   LOCAL_WORKSPACE=/path/to/workspace
   ```

3. **测试新功能**:
   ```bash
   poetry run python scripts/test_simple_git.py
   ```

### 💡 使用示例

#### 自动仓库管理
```python
from src.sonar_resolve.utils.git_manager import GitRepositoryManager

repo_manager = GitRepositoryManager()

# 自动发现并准备仓库
success, local_path, repo_info = repo_manager.prepare_repository_for_project("my-project")

if success:
    print(f"仓库已准备: {local_path}")
```

#### 自动修复流程
```python
from src.sonar_resolve.utils.git_manager import AutoFixProcessor

processor = AutoFixProcessor()

# 处理项目修复
fixes = [{'file_path': 'src/main.java', 'old_code': '...', 'new_code': '...'}]
success = processor.process_project_fixes("my-project", fixes)
```

### 🔍 测试功能

#### 配置测试
```bash
# 简单配置测试
poetry run python scripts/test_simple_git.py

# 完整功能测试  
poetry run python scripts/test_git_discovery.py
```

### 📚 文档更新

- **新增**: [Git自动发现使用指南](docs/GIT_AUTO_DISCOVERY.md)
- **更新**: [项目结构文档](docs/PROJECT_STRUCTURE.md)
- **更新**: 配置示例文件 `.env.example`

### ⚠️ 重要说明

- **兼容性**: 保持向后兼容，旧版配置文件仍然可用
- **权限**: GitLab token需要有 `read_repository` 和 `write_repository` 权限
- **网络**: 首次克隆大型仓库可能需要较长时间
- **存储**: 本地工作目录需要足够的磁盘空间

### 🐛 已知问题

- 大型仓库首次克隆可能超时（已增加超时处理）
- 某些特殊字符的项目名可能影响匹配（已添加清理逻辑）

### 🎯 下一版本计划

- 支持SSH克隆方式
- 增加仓库缓存机制
- 支持分支策略配置
- 添加GitLab Webhook集成

---

## v1.x.x - 基础功能 (2024-01-XX)

### 功能
- SonarQube集成
- Jira任务创建
- 基础Git操作
- AI自动修复

### 配置
- 手动Git仓库配置
- 环境变量管理
