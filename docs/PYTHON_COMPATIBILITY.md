# Python版本兼容性说明

## 支持的Python版本

### 核心功能
- **Python 3.8.1+**: 支持所有核心功能，包括：
  - SonarQube集成
  - Jira集成
  - 项目自动发现
  - Git集成
  - GitLab Merge Request创建
  - 项目管理工具

### AI自动修复功能
- **Python 3.9+**: AI自动修复功能需要更高版本的Python，因为：
  - OpenAI客户端库的某些依赖需要Python 3.9+
  - Anthropic客户端库的某些依赖需要Python 3.9+
  - 特别是`tokenizers`和相关的机器学习包

## 安装方式

### Python 3.8.1 用户（核心功能）
```bash
# 安装核心功能（推荐）
poetry install --without ai

# 或者使用传统pip方式
pip install -r requirements.txt
```

### Python 3.9+ 用户（完整功能）
```bash
# 安装所有功能包括AI
poetry install --with ai

# 或者分步安装
poetry install
poetry install --extras ai
```

## 功能对比

| 功能模块 | Python 3.8.1+ | Python 3.9+ |
|---------|---------------|-------------|
| SonarQube集成 | ✅ | ✅ |
| Jira集成 | ✅ | ✅ |
| 项目自动发现 | ✅ | ✅ |
| Git集成 | ✅ | ✅ |
| GitLab MR | ✅ | ✅ |
| 项目管理工具 | ✅ | ✅ |
| AI自动修复 | ❌ | ✅ |
| OpenAI集成 | ❌ | ✅ |
| Anthropic集成 | ❌ | ✅ |

## 解决方案

### 选项1：升级Python版本（推荐）
```bash
# 使用pyenv安装Python 3.9+
pyenv install 3.9.19
pyenv local 3.9.19

# 重新创建Poetry环境
poetry env use python3.9
poetry install --with ai
```

### 选项2：仅使用核心功能
如果无法升级Python版本，可以：
1. 使用不包含AI的版本进行SonarQube问题分析
2. 手动修复Critical问题
3. 使用工具自动创建Jira任务和Git工作流

### 选项3：混合模式
1. 在Python 3.8环境中运行核心功能
2. 在单独的Python 3.9+环境中运行AI修复
3. 通过文件系统共享数据

## 测试你的环境

```bash
# 检查Python版本
python --version

# 测试核心功能
poetry run python test_connections.py

# 测试项目管理
poetry run python project_manager.py --list

# 如果有AI功能，测试AI连接
poetry run python auto_fix.py --test-only
```

## 常见错误

### `puccinialin requires Python >=3.9`
这是由于AI相关包的依赖导致的，解决方案：
- 使用 `poetry install --without ai`
- 或升级到Python 3.9+

### `tokenizers` 相关错误
同样是AI依赖问题，使用核心功能模式即可避免。

## 建议

对于生产环境，建议：
1. **Python 3.9+**: 获得完整功能体验
2. **Python 3.8**: 专注于问题发现和团队协作工作流
3. **逐步迁移**: 先使用核心功能验证工作流，再升级获得AI能力
