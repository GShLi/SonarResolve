# Poetry 安装和初始化指南

## Poetry 安装

### 方法一：官方安装脚本（推荐）
在PowerShell中运行：
```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

### 方法二：使用pip安装
如果您的Python已配置：
```bash
pip install poetry
```

### 方法三：使用conda安装
如果您使用conda：
```bash
conda install -c conda-forge poetry
```

### 方法四：手动下载安装
1. 访问 https://python-poetry.org/docs/#installation
2. 下载适合您系统的安装包
3. 按照官方文档安装

## 验证安装

安装完成后，重新打开命令行窗口并运行：
```bash
poetry --version
```

如果显示版本号，说明安装成功。

## 项目初始化

在项目目录中运行以下命令：

```bash
# 1. 安装依赖
poetry install

# 2. 激活虚拟环境
poetry shell

# 3. 验证安装
poetry run python --version

# 4. 运行测试
poetry run python test_connections.py
```

## 常用命令

```bash
# 添加新依赖
poetry add requests

# 添加开发依赖
poetry add --group dev pytest

# 运行脚本
poetry run python main.py

# 更新依赖
poetry update

# 查看依赖树
poetry show --tree

# 导出requirements.txt
poetry export -f requirements.txt --output requirements.txt
```

## 如果Poetry安装失败

### 临时解决方案
您可以继续使用传统的pip方式：

1. 创建虚拟环境：
```bash
python -m venv venv
```

2. 激活虚拟环境：
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. 导出并安装依赖：
```bash
# 在有Poetry的环境中导出
poetry export -f requirements.txt --output requirements.txt

# 然后使用pip安装
pip install -r requirements.txt
```

## 环境配置

Poetry配置建议：
```bash
# 在项目目录中创建虚拟环境
poetry config virtualenvs.in-project true

# 查看配置
poetry config --list
```

## 故障排除

1. **权限问题**：以管理员身份运行PowerShell
2. **网络问题**：检查防火墙和代理设置
3. **Python版本**：确保Python 3.8+已安装
4. **PATH问题**：重启命令行或添加Poetry到系统PATH

## 验证完整设置

运行以下命令验证所有配置：
```bash
poetry install
poetry run python test_connections.py
```

如果一切正常，您将看到连接测试结果。
