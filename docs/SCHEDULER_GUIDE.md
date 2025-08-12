# 任务调度器文档

## 概述

SonarQube到Jira任务调度器 (`scheduler.py`) 提供了基于cron表达式的定时任务执行功能，可以自动化地定期运行SonarQube Critical问题检测和Jira任务创建流程。

## 主要功能

### 1. 定时执行
- 基于cron表达式的灵活调度
- 支持标准的5位cron格式（分 时 日 月 周）
- 可配置时区支持

### 2. 任务管理
- 自动化执行主要的SonarQube到Jira工作流
- 连接测试和错误处理
- 详细的执行日志和统计

### 3. 状态监控
- 实时状态查询
- 执行统计（成功/失败次数）
- 下次执行时间预测

## 配置说明

### 环境变量配置

在 `.env` 文件中添加以下配置：

```bash
# 调度器配置
SCHEDULER_ENABLED=true                    # 是否启用调度器
SCHEDULER_CRON_EXPRESSION=0 2 * * *       # Cron表达式
SCHEDULER_TIMEZONE=Asia/Shanghai          # 时区设置
```

### Cron表达式格式

格式：`分 时 日 月 周`

- **分钟**: 0-59
- **小时**: 0-23
- **日期**: 1-31
- **月份**: 1-12
- **星期**: 0-7 (0和7都表示周日)

### 常用Cron表达式示例

```bash
# 每天凌晨2点执行
0 2 * * *

# 每小时执行一次
0 * * * *

# 每天早上9点和下午6点执行
0 9,18 * * *

# 工作日每天早上9点执行
0 9 * * 1-5

# 每周一凌晨3点执行
0 3 * * 1

# 每月1号凌晨2点执行
0 2 1 * *
```

## 使用方法

### 1. 直接运行调度器

```bash
# 运行调度器（需要先配置环境变量）
python run_scheduler.py
```

### 2. 作为模块使用

```python
from sonar_tools.scheduler import TaskScheduler

# 创建调度器实例
scheduler = TaskScheduler()

# 启动调度器
if scheduler.start():
    print("调度器启动成功")
    
    # 获取状态
    status = scheduler.get_status()
    print(f"下次执行时间: {status['next_run_time']}")
    
    # 手动执行一次
    result = scheduler.run_once()
    
    # 停止调度器
    scheduler.stop()
```

### 3. 系统服务部署

#### Windows服务
```bash
# 使用NSSM或SC命令创建Windows服务
sc create SonarJiraScheduler binPath="python C:\path\to\run_scheduler.py"
```

#### Linux系统服务
```bash
# 创建systemd服务文件
sudo nano /etc/systemd/system/sonar-jira-scheduler.service
```

服务配置示例：
```ini
[Unit]
Description=SonarQube to Jira Task Scheduler
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/SonarResolve
ExecStart=/usr/bin/python3 run_scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## 依赖要求

调度器需要额外安装 `croniter` 库：

```bash
# 使用pip安装
pip install croniter

# 使用poetry安装（已在pyproject.toml中配置）
poetry install
```

## 日志和监控

### 日志输出

调度器会输出详细的日志信息：

```
2024-08-09 10:00:00 - scheduler - INFO - 任务调度器初始化完成
2024-08-09 10:00:00 - scheduler - INFO - 调度器配置信息:
2024-08-09 10:00:00 - scheduler - INFO -   - 调度器状态: 启用
2024-08-09 10:00:00 - scheduler - INFO -   - Cron表达式: 0 2 * * *
2024-08-09 10:00:00 - scheduler - INFO -   - 时区设置: Asia/Shanghai
2024-08-09 10:00:00 - scheduler - INFO -   - 下次执行时间: 2024-08-10 02:00:00
```

### 执行日志

```
2024-08-10 02:00:00 - scheduler - INFO - 开始执行定时任务...
2024-08-10 02:00:05 - scheduler - INFO - ✅ SonarQube连接测试通过
2024-08-10 02:00:06 - scheduler - INFO - ✅ Jira连接测试通过
2024-08-10 02:00:30 - scheduler - INFO - 本次创建JIRA任务: 15 个
2024-08-10 02:00:30 - scheduler - INFO - 定时任务执行成功
2024-08-10 02:00:30 - scheduler - INFO - 任务执行耗时: 0:00:30.123456
```

### 状态查询

```python
status = scheduler.get_status()
print(f"总运行次数: {status['total_runs']}")
print(f"成功次数: {status['successful_runs']}")
print(f"失败次数: {status['failed_runs']}")
```

## 错误处理

### 1. 配置错误

```bash
# 无效的cron表达式
2024-08-09 10:00:00 - scheduler - ERROR - 无效的cron表达式 'invalid': ...
```

### 2. 连接错误

```bash
# 连接测试失败
2024-08-10 02:00:00 - scheduler - ERROR - 定时任务执行失败: 连接测试失败
```

### 3. 依赖缺失

```bash
# croniter库未安装
ImportError: croniter库未安装，请运行: pip install croniter
```

## 最佳实践

### 1. 调度频率建议

- **开发环境**: 每小时或每2小时执行一次
- **测试环境**: 每天2-3次
- **生产环境**: 每天1-2次（建议在非工作时间）

### 2. 资源管理

- 确保JIRA任务创建限制合理配置
- 监控系统资源使用情况
- 设置合适的日志轮转策略

### 3. 故障恢复

- 配置系统服务自动重启
- 设置健康检查和告警
- 定期检查日志文件

### 4. 安全考虑

- 保护环境变量和配置文件
- 限制调度器运行用户权限
- 定期更新依赖包

## 故障排除

### 常见问题

1. **调度器未启动**
   - 检查 `SCHEDULER_ENABLED=true` 配置
   - 验证cron表达式格式

2. **时区问题**
   - 确认 `SCHEDULER_TIMEZONE` 设置正确
   - 检查系统时区配置

3. **依赖问题**
   - 安装 `croniter` 库
   - 检查Python环境

4. **权限问题**
   - 确保有文件读写权限
   - 检查网络访问权限

### 调试模式

```python
# 启用调试日志
import logging
logging.getLogger().setLevel(logging.DEBUG)

# 立即执行测试
scheduler = TaskScheduler()
result = scheduler.run_once()
```

## 版本历史

- **v1.0**: 初始版本
  - 基本的cron调度功能
  - 配置化的时区支持
  - 详细的日志记录
  - 状态监控和统计
