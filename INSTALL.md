# 安装依赖说明

## 基础安装

```bash
# 安装基础依赖（Jira模式）
poetry install

# 或使用pip
pip install -r requirements.txt
```

## AI功能安装

### 使用Poetry（推荐）

```bash
# 安装包含AI功能的完整依赖
poetry install --extras ai

# 或安装所有功能
poetry install --extras all

# 仅安装AI开发组依赖
poetry install --with ai
```

### 使用pip

```bash
# 手动安装LangChain相关依赖
pip install langchain>=0.1.0
pip install langchain-openai>=0.1.0  
pip install openai>=1.0.0

# 可选：Anthropic支持
pip install anthropic>=0.5.0
```

## 依赖说明

### 基础依赖（Jira模式）

- `requests` - HTTP客户端
- `jira` - Jira API客户端
- `python-dotenv` - 环境变量管理
- `pydantic` - 数据验证
- `GitPython` - Git操作
- `python-gitlab` - GitLab API客户端
- `croniter` - 定时任务支持

### AI功能依赖

- `langchain` - LangChain框架核心
- `langchain-openai` - OpenAI集成
- `openai` - OpenAI API客户端
- `anthropic` - Anthropic API客户端（可选）

## 验证安装

```bash
# 测试基础功能
python -c "import requests, jira, gitlab; print('基础依赖安装成功')"

# 测试AI功能
python -c "import langchain, langchain_openai; print('AI依赖安装成功')"

# 运行连接测试
python run.py --mode jira --test      # Jira模式测试
python run.py --mode ai-fix --test    # AI模式测试
```

## 常见问题

### Python版本要求

- 基础功能：Python >= 3.9
- AI功能：Python >= 3.9（由于LangChain要求）

### 安装失败

如果使用Poetry安装失败，可以尝试：

```bash
# 清除缓存
poetry cache clear pypi --all

# 重新安装
poetry install --extras ai
```

### 版本冲突

如果遇到版本冲突，可以手动指定版本：

```bash
pip install langchain==0.1.17 langchain-openai==0.1.8
```
