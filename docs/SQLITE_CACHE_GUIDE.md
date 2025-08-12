# SQLite项目状态数据库指南

## 概述

SonarResolve使用SQLite数据库来记录已创建的Jira项目和任务，避免重复创建。数据库采用简化设计，只记录成功创建的记录，无过期时间字段。

## 功能特性

### 1. 项目创建记录
- **自动记录**: 自动记录成功创建的Jira项目
- **重复检查**: 防止重复创建相同的项目
- **映射关系**: 保存SonarQube项目与Jira项目的映射关系

### 2. 任务创建记录
- **任务跟踪**: 记录每个已创建的Jira任务
- **项目关联**: 任务与项目的关联关系
- **重复避免**: 避免为同一SonarQube问题重复创建任务

### 3. 高效查询
- **索引优化**: 添加数据库索引提高查询性能
- **快速检查**: 毫秒级的本地查询速度
- **统计信息**: 提供创建项目和任务的统计数据

## 数据库结构

### created_projects表
记录已创建的Jira项目：
```sql
CREATE TABLE created_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sonar_project_key TEXT UNIQUE NOT NULL,    -- SonarQube项目Key
    jira_project_key TEXT NOT NULL,            -- Jira项目Key
    created_by_us BOOLEAN DEFAULT TRUE,        -- 是否由系统创建
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- 创建时间
)
```

### created_tasks表
记录已创建的Jira任务：
```sql
CREATE TABLE created_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sonar_issue_key TEXT UNIQUE NOT NULL,      -- SonarQube问题Key
    jira_task_key TEXT NOT NULL,               -- Jira任务Key
    jira_project_key TEXT NOT NULL,            -- 所属Jira项目Key
    sonar_project_key TEXT NOT NULL,           -- 来源SonarQube项目Key
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- 创建时间
)
```

### 索引
为提高查询性能添加的索引：
```sql
-- 项目查询索引
CREATE INDEX idx_created_projects_sonar_key ON created_projects (sonar_project_key);

-- 任务查询索引  
CREATE INDEX idx_created_tasks_sonar_issue ON created_tasks (sonar_issue_key);
CREATE INDEX idx_created_tasks_project ON created_tasks (sonar_project_key);
```

## 使用方法

### 1. 自动使用（推荐）
数据库功能已集成到主处理流程中，无需手动操作：

```python
from sonar_tools.core.main import SonarToJiraProcessor

# 创建处理器时会自动初始化数据库
processor = SonarToJiraProcessor()

# 处理过程中会自动检查和记录项目/任务
results = processor.process_critical_issues()
```

### 2. 手动数据库操作
如需手动管理数据库，可以直接使用ProjectStatusDB：

```python
from sonar_tools.utils.project_db import ProjectStatusDB

# 初始化数据库
project_db = ProjectStatusDB()

# 检查项目是否已创建
jira_key = project_db.is_project_created("my-sonar-project")
if jira_key:
    print(f"项目已存在: {jira_key}")
else:
    print("项目尚未创建")

# 记录新创建的项目
project_db.record_created_project("my-sonar-project", "MYPROJ")

# 检查任务是否已创建
if project_db.is_task_created("SONAR-ISSUE-123"):
    print("任务已创建")
else:
    print("任务尚未创建")

# 记录新创建的任务
project_db.record_created_task(
    sonar_issue_key="SONAR-ISSUE-123",
    jira_task_key="MYPROJ-1",
    jira_project_key="MYPROJ",
    sonar_project_key="my-sonar-project"
)
```

### 3. 查看统计信息
```python
# 获取项目统计
project_stats = project_db.get_project_statistics()
print(f"已创建项目数: {project_stats['total_projects']}")

# 获取任务统计
task_stats = project_db.get_task_statistics()
print(f"已创建任务数: {task_stats['total_tasks']}")

# 获取所有已创建的项目
projects = project_db.get_all_created_projects()
for project in projects:
    print(f"{project['sonar_project_key']} -> {project['jira_project_key']}")
```

## 配置数据库存储位置

### 默认存储位置

数据库文件默认存储在项目根目录的 `db/` 文件夹中：
```
SonarResolve/
├── db/
│   └── project_status.db     # SQLite数据库文件
├── src/
├── docs/
└── ...
```

### 自定义存储位置

可以通过环境变量 `DATABASE_PATH` 自定义数据库存储位置：

```env
# 使用相对路径（基于项目根目录）
DATABASE_PATH=data/cache/sonar_cache.db

# 使用绝对路径
DATABASE_PATH=/var/lib/sonar_resolve/project_status.db

# Windows绝对路径
DATABASE_PATH=C:\ProgramData\SonarResolve\project_status.db
```

### 自动目录创建

系统会自动创建数据库文件所需的目录结构，无需手动创建。

### 数据库备份

可以启用自动备份功能：
```env
DATABASE_BACKUP=true
```选项

### 数据库文件位置
默认数据库文件位于当前工作目录下的`project_status.db`，可以通过参数指定：

```python
project_db = ProjectStatusDB(db_path="/path/to/custom/database.db")
```

## 性能优化效果

### API调用减少
- **首次运行**: 需要调用Jira API检查所有项目
- **后续运行**: 仅检查数据库中不存在的项目
- **典型场景**: 可减少90%以上的API调用

### 响应时间优化
- **本地查询**: < 1ms
- **API调用**: 100-500ms
- **总体提升**: 处理速度提升10-50倍

## 维护和管理

### 数据清理
系统会自动处理重复记录，但可以手动清理旧数据：

```python
# 清理1年以前的记录（默认保留365天）
project_db.cleanup_old_records(days=365)
```

### 数据备份
由于数据库记录了重要的项目和任务映射关系，建议定期备份：

```bash
# 简单文件复制备份
cp project_status.db project_status_backup_$(date +%Y%m%d).db
```

### 数据库重置
如需完全重置数据库，删除数据库文件即可：

```bash
rm project_status.db
```

## 故障排除

### 常见问题

#### 1. 数据库文件权限错误
**问题**: `sqlite3.OperationalError: unable to open database file`
**解决**: 确保当前用户对数据库文件目录有读写权限

#### 2. 重复记录处理
**问题**: 担心重复记录影响数据一致性
**解决**: 数据库使用`INSERT OR REPLACE`，自动处理重复记录

#### 3. 查询性能问题
**问题**: 随着记录增多查询变慢
**解决**: 数据库已添加适当索引，大量数据时考虑定期清理

### 调试模式
启用调试日志以查看详细的数据库操作：

```python
import logging
logging.getLogger('src.sonar_resolve.utils.project_db').setLevel(logging.DEBUG)
```

## 测试验证

运行数据库功能测试脚本：

```bash
cd scripts
python test_independent_db.py
```

该脚本会验证：
- 基本数据库操作
- 重复记录处理
- 统计信息准确性

## 最佳实践

### 1. 定期监控
- 定期检查数据库大小和记录数量
- 监控查询性能
- 适时清理旧记录

### 2. 环境隔离
- 不同环境使用不同的数据库文件
- 避免开发和生产环境数据混淆

### 3. 性能调优
- 大型环境可考虑使用SQLite的WAL模式
- 定期运行VACUUM命令优化数据库文件

### 4. 数据完整性
- 定期验证项目映射关系的准确性
- 发现异常时及时清理相关记录

## 技术实现细节

### 线程安全
使用线程锁确保并发访问的数据一致性。

### 事务处理
所有写操作都在事务中执行，确保数据原子性。

### 错误处理
完善的异常处理机制，确保数据库故障不影响主流程。

### 向后兼容
简化设计不影响现有工作流程，是渐进式的改进。
