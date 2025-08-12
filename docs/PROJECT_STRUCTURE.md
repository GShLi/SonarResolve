# 项目文件结构

这个文档描述了SonarResolve项目的标准Python项目文件结构。

## 目录结构

```
SonarResolve/
├── README.md                    # 项目主文档
├── pyproject.toml              # Poetry配置和项目元数据
├── poetry.lock                 # 依赖锁定文件
├── .env.example                # 环境变量模板
├── .env                        # 环境变量（需要用户创建）
├── .gitignore                  # Git忽略文件
├── .pre-commit-config.yaml     # pre-commit钩子配置
├── Makefile                    # Make构建脚本
├── make.bat                    # Windows Make脚本
├── run.py                      # 快速启动脚本
├── main.py                     # 传统入口点（向后兼容）
├── setup.py                    # setuptools配置（向后兼容）
├── requirements.txt            # pip依赖文件（从poetry导出）
│
├── src/                        # 源代码目录
│   └── sonar_resolve/          # 主包
│       ├── __init__.py         # 包初始化
│       ├── clients/            # 外部服务客户端
│       │   ├── __init__.py
│       │   ├── sonarqube_client.py     # SonarQube API客户端
│       │   ├── jira_client.py          # Jira API客户端
│       │   └── ai_client.py            # AI服务客户端
│       ├── core/               # 核心业务逻辑
│       │   ├── __init__.py
│       │   ├── config.py               # 配置管理
│       │   ├── models.py               # 数据模型
│       │   ├── project_discovery.py   # 项目发现和匹配
│       │   ├── main.py                 # 主要处理逻辑（Jira任务创建）
│       │   └── auto_fix.py             # AI自动修复逻辑
│       └── utils/              # 工具模块
│           ├── __init__.py
│           └── git_manager.py          # Git操作管理
│
├── scripts/                    # 可执行脚本
│   ├── test_connections.py     # 连接测试脚本
│   ├── project_manager.py      # 项目管理工具
│   ├── test_labels.py          # 标签测试脚本
│   ├── test_git_discovery.py   # Git自动发现功能测试
│   └── test_simple_git.py      # 简化Git配置测试
│
├── tests/                      # 测试文件
│   ├── __init__.py
│   ├── test_models.py          # 模型测试
│   └── test_sonarqube_client.py # SonarQube客户端测试
│
├── docs/                       # 项目文档
│   ├── PROJECT_STRUCTURE.md    # 项目结构说明
│   ├── GIT_AUTO_DISCOVERY.md   # Git自动发现功能指南
│   ├── POETRY_GUIDE.md         # Poetry使用指南
│   └── ...                     # 其他文档
│
├── docs/                       # 文档目录
│   ├── JIRA_LABELS_FIX.md      # Jira标签修复文档
│   ├── POETRY_GUIDE.md         # Poetry使用指南
│   ├── POETRY_INSTALL.md       # Poetry安装说明
│   └── PYTHON_COMPATIBILITY.md # Python版本兼容性
│
└── __pycache__/               # Python缓存（Git忽略）
```

## 模块说明

### src/sonar_resolve/
主要的Python包，包含所有核心功能。

#### clients/
与外部服务交互的客户端模块：
- `sonarqube_client.py`: SonarQube REST API封装
- `jira_client.py`: Jira REST API封装，包含标签处理增强
- `ai_client.py`: OpenAI和Anthropic AI服务封装

#### core/
核心业务逻辑模块：
- `config.py`: 环境变量和配置管理
- `models.py`: 数据模型定义（SonarIssue, JiraTask等）
- `project_discovery.py`: 智能项目发现和匹配算法
- `main.py`: 第一阶段功能 - SonarQube问题到Jira任务
- `auto_fix.py`: 第二阶段功能 - AI自动修复和MR创建

#### utils/
工具和辅助函数：
- `git_manager.py`: **Git自动仓库管理** - 支持根据SonarQube项目名自动发现GitLab仓库、自动克隆和更新、分支管理和MR创建

### scripts/
独立的可执行脚本：
- `test_connections.py`: 测试所有外部服务连接
- `project_manager.py`: 项目管理和分析工具
- `test_labels.py`: Jira标签功能测试

### tests/
单元测试和集成测试文件。

### docs/
项目文档，包括用户指南、故障排除等。

## 使用方式

### 1. 使用快速启动脚本（推荐）
```bash
# 测试连接
python run.py test

# 项目管理
python run.py projects --list

# 创建Jira任务
python run.py jira

# AI自动修复
python run.py autofix
```

### 2. 使用Poetry脚本
```bash
# 安装后可用的命令
poetry run sonar-test
poetry run sonar-jira
poetry run sonar-autofix
poetry run project-manager
```

### 3. 直接运行模块
```bash
# 使用Python模块方式
python -m sonar_resolve.core.main
python -m sonar_resolve.core.auto_fix

# 运行脚本
python scripts/test_connections.py
python scripts/project_manager.py --list
```

## 配置

所有配置都通过环境变量管理，参考`.env.example`创建`.env`文件。

## 依赖管理

项目使用Poetry进行依赖管理：
- `pyproject.toml`: 主要配置文件
- `poetry.lock`: 锁定的依赖版本
- `requirements.txt`: 传统pip兼容（从poetry导出）

## 开发

```bash
# 安装开发依赖
poetry install

# 运行测试
poetry run pytest

# 代码格式化
poetry run black .
poetry run isort .

# 类型检查
poetry run mypy .

# 代码质量检查
poetry run flake8
```

## 向后兼容性

为了保持向后兼容，项目根目录仍然保留了：
- `main.py`: 传统入口点
- `setup.py`: setuptools配置
- `requirements.txt`: pip依赖列表

这些文件会自动适配新的项目结构。
