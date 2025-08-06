# LangChain AI 大模型集成指南

## 概述

SonarResolve 现在使用 LangChain 框架来对接各种大语言模型，提供更强大、更灵活的代码自动修复能力。

## 主要特性

✅ **统一接口**: 通过 LangChain 统一不同AI提供商的接口  
✅ **专业提示词**: 针对 SonarQube Critical 问题优化的提示词  
✅ **消息格式**: 使用 SystemMessage 和 HumanMessage 提高AI理解能力  
✅ **错误处理**: 更好的异常处理和重试机制  
✅ **模型切换**: 支持多种AI模型，可灵活切换  

## 支持的AI提供商

### 1. OpenAI (GPT系列)
- **推荐模型**: `gpt-4`, `gpt-4-turbo`
- **经济模型**: `gpt-3.5-turbo`
- **优势**: 代码理解能力强，修复质量高

### 2. Anthropic (Claude系列)  
- **推荐模型**: `claude-3-5-sonnet-20241022`
- **平衡模型**: `claude-3-sonnet-20240229`
- **经济模型**: `claude-3-haiku-20240307`
- **优势**: 安全性高，长文本处理能力强

## 配置方法

### 环境变量配置 (.env文件)

```env
# AI模型配置（使用LangChain对接）
AI_PROVIDER=openai                    # 或 anthropic

# OpenAI配置
OPENAI_API_KEY=sk-your_openai_key
OPENAI_BASE_URL=https://api.openai.com/v1    # 可选，用于代理

# Anthropic配置  
ANTHROPIC_API_KEY=sk-ant-your_anthropic_key

# AI模型选择
AI_MODEL=gpt-4                        # 具体使用的模型
```

### 模型选择建议

#### 高质量修复（推荐）
```env
AI_PROVIDER=openai
AI_MODEL=gpt-4
```

#### 成本平衡
```env
AI_PROVIDER=openai  
AI_MODEL=gpt-3.5-turbo
```

#### 安全优先
```env
AI_PROVIDER=anthropic
AI_MODEL=claude-3-5-sonnet-20241022
```

## 代码架构

### LangChain AI客户端结构

```python
# 抽象基类
class AIClient(ABC):
    def fix_code_issue(self, issue: SonarIssue, file_content: str) -> Optional[str]

# LangChain基类
class LangChainAIClient(AIClient):
    def __init__(self, chat_model: BaseChatModel)
    def _create_messages(self, issue, file_content) -> List[BaseMessage]
    def _get_system_prompt() -> str
    def _create_human_prompt(issue, file_content) -> str

# 具体实现
class LangChainOpenAIClient(LangChainAIClient):
    # 使用 ChatOpenAI 模型

class LangChainAnthropicClient(LangChainAIClient):  
    # 使用 ChatAnthropic 模型
```

### 消息构建

#### SystemMessage (系统角色设定)
```python
system_prompt = (
    "你是一名资深代码修复专家，擅长根据SonarQube检测结果修复代码中的Critical级别问题。"
    "你的目标是只修复指定的问题，保持代码原有风格和业务逻辑，输出高质量、可运行的修复后完整代码。"
    # ... 详细要求
)
```

#### HumanMessage (具体任务)
```python
human_prompt = f"""请修复以下代码中的SonarQube Critical问题：

【问题详情】
- 规则代码: {issue.rule}
- 严重程度: {issue.severity}
- 问题描述: {issue.message}
- 文件位置: {issue.get_location_info()}
- 问题类型: {issue.type}

【待修复的代码文件】
```{issue.language}
{file_content}
```

【修复要求】
请分析上述SonarQube检测出的问题，并对代码进行精确修复。只返回修复后的完整代码文件内容。
"""
```

## 使用示例

### 基本使用
```python
from src.sonar_resolve.clients.ai_client import AIClientFactory

# 创建AI客户端（根据.env配置自动选择）
ai_client = AIClientFactory.create_client()

# 修复代码问题
fixed_content = ai_client.fix_code_issue(sonar_issue, file_content)
```

### 直接使用特定客户端
```python
from src.sonar_resolve.clients.ai_client import LangChainOpenAIClient, LangChainAnthropicClient

# OpenAI客户端
openai_client = LangChainOpenAIClient(
    api_key="your-api-key",
    model="gpt-4"
)

# Anthropic客户端
anthropic_client = LangChainAnthropicClient(
    api_key="your-api-key", 
    model="claude-3-5-sonnet-20241022"
)
```

### 批量修复
```python
from src.sonar_resolve.clients.ai_client import CodeFixer

fixer = CodeFixer()
fixes = fixer.fix_multiple_issues(sonar_issues, repository_path)

for fix in fixes:
    print(f"修复文件: {fix['file_path']}")
    print(f"修复内容: {fix['diff']}")
```

## 提示词优化

### 系统提示词特点
1. **明确角色定位**: 资深代码修复专家
2. **具体任务说明**: 修复SonarQube Critical问题  
3. **严格输出要求**: 只返回修复后代码，无解释
4. **质量保证**: 要求符合最佳实践

### 用户提示词特点
1. **结构化信息**: 清晰的问题详情格式
2. **代码块标记**: 使用语言标识的代码块
3. **明确指令**: 明确的修复要求和输出格式

## 测试功能

### 运行测试脚本
```bash
# 测试LangChain AI客户端功能
poetry run python scripts/test_langchain_ai.py
```

### 测试内容
- ✅ 配置验证
- ✅ AI客户端初始化
- ✅ 代码修复功能
- ✅ 错误处理机制

## 优势对比

### LangChain vs 直接API调用

| 特性 | LangChain | 直接API |
|------|-----------|---------|
| 统一接口 | ✅ | ❌ |
| 消息管理 | ✅ | 手动 |
| 错误处理 | ✅ | 手动 |
| 模型切换 | ✅ | 复杂 |
| 扩展性 | ✅ | 有限 |
| 维护成本 | 低 | 高 |

## 最佳实践

### 1. 模型选择
- **生产环境**: 使用 GPT-4 或 Claude-3.5-Sonnet
- **测试环境**: 使用 GPT-3.5-turbo 或 Claude-3-Haiku
- **成本控制**: 根据问题复杂度选择合适模型

### 2. API密钥管理
- 使用环境变量存储API密钥
- 定期轮换密钥
- 监控API使用量和费用

### 3. 错误处理
- 捕获网络超时异常
- 处理API限速问题
- 记录详细的错误日志

### 4. 性能优化
- 合理设置temperature参数（推荐0.1）
- 限制max_tokens避免过长输出
- 批量处理时控制并发数

## 故障排除

### 常见问题

1. **导入错误**
   ```bash
   poetry add langchain langchain-openai langchain-anthropic
   ```

2. **API密钥错误**
   - 检查.env文件配置
   - 验证密钥有效性

3. **模型不存在**
   - 确认模型名称正确
   - 检查API访问权限

4. **网络超时**
   - 增加超时时间设置
   - 检查网络连接

### 调试建议
- 启用详细日志: `LOG_LEVEL=DEBUG`
- 使用简单测试用例验证
- 检查LangChain版本兼容性

## 依赖管理

### 必需依赖
```toml
langchain = "^0.1.0"
langchain-openai = "^0.1.0"     # OpenAI支持
langchain-anthropic = "^0.1.0"  # Anthropic支持
```

### 安装命令
```bash
poetry add langchain langchain-openai langchain-anthropic
```

## 未来计划

- 🔄 支持更多AI提供商 (Azure OpenAI, Cohere等)
- 🎯 针对不同编程语言优化提示词
- 📊 添加修复效果评估机制
- 🔧 支持自定义提示词模板
- 💾 添加修复结果缓存机制

---

*更多信息请参考 [LangChain官方文档](https://docs.langchain.com/)*
