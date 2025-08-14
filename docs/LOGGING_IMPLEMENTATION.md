# 日志配置实现总结

## 📋 功能概述

已成功实现了完整的日志存储位置配置功能，默认存储在与 `src` 同级的 `logs` 目录中。

## 🔧 配置参数

### 环境变量配置

在 `.env` 文件中可以配置以下日志相关参数：

```bash
# 日志配置
LOG_FILE_PATH=logs/sonar_resolve.log    # 日志文件路径（相对于项目根目录）
LOG_LEVEL=INFO                          # 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_MAX_SIZE=10                         # 日志文件最大大小（MB）
LOG_BACKUP_COUNT=5                      # 备份文件数量
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s  # 日志格式
```

### 默认配置

- **日志文件路径**: `logs/sonar_resolve.log`
- **日志级别**: `INFO`
- **最大文件大小**: `10 MB`
- **备份文件数量**: `5`
- **日志格式**: 标准格式包含时间、模块名、级别和消息

## 📁 目录结构

```
SonarResolve/
├── src/
│   └── sonar_resolve/
│       └── core/
│           └── config.py       # 配置管理
├── logs/                       # 日志存储目录
│   ├── sonar_resolve.log      # 主日志文件
│   ├── sonar_resolve.log.1    # 备份文件（轮转后）
│   └── ...
└── db/                        # 数据库存储目录
    └── project_status.db
```

## 🚀 主要功能特性

### 1. 自动目录创建

- 系统启动时自动创建 `logs` 目录
- 无需手动创建目录结构

### 2. 日志文件轮转

- 当日志文件达到最大大小时自动轮转
- 保留指定数量的备份文件
- 使用 `RotatingFileHandler` 实现

### 3. 双重输出

- 同时输出到日志文件和控制台
- 控制台输出便于开发调试
- 文件输出便于生产环境日志保存

### 4. 灵活配置

- 支持环境变量自定义所有日志参数
- 支持相对路径和绝对路径
- 支持不同日志级别过滤

## 📖 核心方法

### `Config.setup_logging()`

```python
@classmethod
def setup_logging(cls) -> str:
    """
    设置日志配置
    
    Returns:
        str: 实际的日志文件路径
    """
```

- 创建日志目录
- 配置文件和控制台处理器
- 设置日志格式和轮转规则
- 返回实际的日志文件路径

### `Config.get_log_info()`

```python
@classmethod
def get_log_info(cls) -> dict:
    """
    获取日志配置信息
    
    Returns:
        dict: 包含所有日志配置的字典
    """
```

- 返回完整的日志配置信息
- 包含文件路径、级别、大小限制等
- 包含目录和文件存在状态

## 🧪 测试验证

### 测试脚本

已创建 `test_simple_log.py` 用于验证日志功能：

```bash
python test_simple_log.py
```

### 测试内容

- ✅ 配置信息读取
- ✅ 日志目录自动创建
- ✅ 日志文件写入
- ✅ 多级别日志记录
- ✅ 文件轮转功能

## 🔒 安全与维护

### Git 忽略

- 日志目录已添加到 `.gitignore`
- 避免日志文件被提交到版本控制

### 权限处理

- 自动处理目录创建权限
- 支持 Windows 和 Linux 系统

### 错误处理

- 完善的异常处理机制
- 日志配置失败时的降级处理

## 📊 使用示例

### 基本使用

```python
from sonar_tools.core.config import Config

# 设置日志配置
log_path = Config.setup_logging()

# 使用日志
import logging

logger = Config.setup_logging(__name__)
logger.info("这是一条日志消息")
```

### 自定义配置

```python
import os

# 设置环境变量
os.environ['LOG_FILE_PATH'] = 'custom_logs/my_app.log'
os.environ['LOG_LEVEL'] = 'DEBUG'
os.environ['LOG_MAX_SIZE'] = '20'

# 应用配置
log_path = Config.setup_logging()
```

## 🎯 与数据库配置的一致性

日志配置与数据库配置保持一致的设计模式：

- 都支持环境变量自定义路径
- 都有默认的存储目录（`logs/` 和 `db/`）
- 都实现了自动目录创建
- 都提供了配置信息查询方法

## ✅ 完成状态

- [x] 日志存储位置配置
- [x] 默认存储在 logs/ 目录
- [x] 环境变量支持
- [x] 自动目录创建
- [x] 日志文件轮转
- [x] 配置信息查询
- [x] 测试验证
- [x] 文档更新

## 🚀 后续优化建议

1. **日志分级存储**: 不同级别的日志可以存储到不同文件
2. **日志压缩**: 旧的备份文件可以自动压缩节省空间
3. **日志清理**: 定期清理超过保留期的旧日志文件
4. **远程日志**: 支持发送日志到远程日志服务器
5. **日志分析**: 集成日志分析和监控功能
