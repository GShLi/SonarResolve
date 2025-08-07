import os
import logging
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from src.sonar_resolve.core.models import SonarIssue
from src.sonar_resolve.core.config import Config

# 尝试导入LangChain（可选）
try:
    from langchain_core.messages import SystemMessage, HumanMessage
    from langchain_core.language_models import BaseChatModel
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    # 如果LangChain不可用，创建简单的替代类
    class SystemMessage:
        def __init__(self, content: str):
            self.content = content
    
    class HumanMessage:
        def __init__(self, content: str):
            self.content = content
    
    class BaseChatModel:
        pass

logger = logging.getLogger(__name__)

class AIClient(ABC):
    """AI客户端抽象基类"""
    
    @abstractmethod
    def fix_code_issue(self, issue: SonarIssue, file_content: str) -> Optional[str]:
        """修复代码问题"""
        pass

class LangChainAIClient(AIClient):
    """LangChain AI客户端基类（需要Python >=3.9和LangChain）"""
    
    def __init__(self, chat_model):
        """
        初始化 LangChain AI 客户端
        注意：此功能需要Python >=3.9和相应的LangChain包
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain不可用，请升级到Python >=3.9并安装LangChain")
        
        self.chat_model = chat_model
        logger.info(f"LangChain AI客户端初始化成功，使用模型: {type(chat_model).__name__}")
    
    def fix_code_issue(self, issue: SonarIssue, file_content: str) -> Optional[str]:
        """使用 LangChain 修复代码问题"""
        try:
            # 构建消息
            messages = self._create_messages(issue, file_content)
            
            # 调用模型
            response = self.chat_model.invoke(messages)
            
            # 提取修复后的内容
            fixed_content = response.content.strip()
            
            # 移除可能的代码块标记
            fixed_content = self._clean_code_blocks(fixed_content)
            
            return fixed_content
            
        except Exception as e:
            logger.error(f"LangChain修复代码失败: {e}")
            return None
    
    def _create_messages(self, issue: SonarIssue, file_content: str):
        """创建 LangChain 消息"""
        system_prompt = self._get_system_prompt()
        human_prompt = self._create_human_prompt(issue, file_content)
        
        return [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
    
    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return (
            "你是一名资深代码修复专家，擅长根据SonarQube检测结果修复代码中的Critical级别问题。"
            "你的目标是只修复指定的问题，保持代码原有风格和业务逻辑，输出高质量、可运行的修复后完整代码。"
            "请严格遵循以下要求："
            "1. 只修复指定的SonarQube问题，不要改动无关代码"
            "2. 保持代码原有的业务逻辑和代码风格"
            "3. 修复后的代码需符合最佳实践和安全规范"
            "4. 只输出修复后的完整代码文件内容，不要添加解释、注释或标记"
            "5. 确保修复后的代码语法正确且可以正常运行"
        )
    
    def _create_human_prompt(self, issue: SonarIssue, file_content: str) -> str:
        """创建用户提示词"""
        return f"""请修复以下代码中的SonarQube Critical问题：

【问题详情】
- 规则代码: {issue.rule}
- 严重程度: {issue.severity}
- 问题描述: {issue.message}
- 文件位置: {issue.get_location_info()}
- 问题类型: {issue.type}

【待修复的代码文件】
```{getattr(issue, 'language', 'text')}
{file_content}
```

【修复要求】
请分析上述SonarQube检测出的问题，并对代码进行精确修复。只返回修复后的完整代码文件内容，不要包含任何解释文字或代码块标记。
"""
    
    def _clean_code_blocks(self, content: str) -> str:
        """清理代码块标记"""
        if content.startswith("```"):
            lines = content.split('\n')
            if len(lines) > 2:
                # 移除开头和结尾的```行
                content = '\n'.join(lines[1:-1])
        return content

class EnhancedOpenAIClient(AIClient):
    """增强版OpenAI客户端 - 使用优化的提示词"""
    
    def __init__(self, api_key: str, model: str = "gpt-4", base_url: str = None):
        try:
            import openai
            self.client = openai.OpenAI(
                api_key=api_key,
                base_url=base_url
            )
            self.model = model
            logger.info(f"增强版OpenAI客户端初始化成功，使用模型: {model}")
        except ImportError:
            raise ImportError("请安装openai库: poetry add openai")
        except Exception as e:
            logger.error(f"增强版OpenAI客户端初始化失败: {e}")
            raise
    
    def fix_code_issue(self, issue: SonarIssue, file_content: str) -> Optional[str]:
        """使用增强提示词修复代码问题"""
        try:
            # 使用分离的系统提示词和用户提示词
            system_prompt = self._get_system_prompt()
            human_prompt = self._create_human_prompt(issue, file_content)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": human_prompt}
                ],
                temperature=0.1,
                max_tokens=4000
            )
            
            fixed_content = response.choices[0].message.content.strip()
            
            # 清理代码块标记
            fixed_content = self._clean_code_blocks(fixed_content)
            
            return fixed_content
            
        except Exception as e:
            logger.error(f"增强版OpenAI修复代码失败: {e}")
            return None
    
    def _get_system_prompt(self) -> str:
        """获取系统提示词 - 专门针对Claude 4.0优化"""
        return (
            "你是一名资深代码修复专家，擅长根据SonarQube检测结果修复代码中的Critical级别问题。"
            "你的目标是只修复指定的问题，保持代码原有风格和业务逻辑，输出高质量、可运行的修复后完整代码。"
            "请严格遵循以下要求："
            "1. 只修复指定的SonarQube问题，不要改动无关代码"
            "2. 保持代码原有的业务逻辑和代码风格"
            "3. 修复后的代码需符合最佳实践和安全规范"
            "4. 只输出修复后的完整代码文件内容，不要添加解释、注释或标记"
            "5. 确保修复后的代码语法正确且可以正常运行"
        )
    
    def _create_human_prompt(self, issue: SonarIssue, file_content: str) -> str:
        """创建用户提示词 - 结构化和详细化"""
        return f"""请修复以下代码中的SonarQube Critical问题：

【问题详情】
- 规则代码: {issue.rule}
- 严重程度: {issue.severity}
- 问题描述: {issue.message}
- 文件位置: {issue.get_location_info()}
- 问题类型: {issue.type}

【待修复的代码文件】
```{getattr(issue, 'language', 'text')}
{file_content}
```

【修复要求】
请分析上述SonarQube检测出的问题，并对代码进行精确修复。只返回修复后的完整代码文件内容，不要包含任何解释文字或代码块标记。
"""
    
    def _clean_code_blocks(self, content: str) -> str:
        """清理代码块标记"""
        if content.startswith("```"):
            lines = content.split('\n')
            if len(lines) > 2:
                # 移除开头和结尾的```行
                content = '\n'.join(lines[1:-1])
        return content

class EnhancedAnthropicClient(AIClient):
    """增强版Anthropic客户端 - 使用优化的提示词"""
    
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = model
            logger.info(f"增强版Anthropic客户端初始化成功，使用模型: {model}")
        except ImportError:
            raise ImportError("请安装anthropic库: poetry add anthropic")
        except Exception as e:
            logger.error(f"增强版Anthropic客户端初始化失败: {e}")
            raise
    
    def fix_code_issue(self, issue: SonarIssue, file_content: str) -> Optional[str]:
        """使用增强提示词修复代码问题"""
        try:
            # 使用专门为Claude优化的提示词
            prompt = self._create_claude_prompt(issue, file_content)
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            fixed_content = response.content[0].text.strip()
            
            # 清理代码块标记
            fixed_content = self._clean_code_blocks(fixed_content)
            
            return fixed_content
            
        except Exception as e:
            logger.error(f"增强版Anthropic修复代码失败: {e}")
            return None
    
    def _create_claude_prompt(self, issue: SonarIssue, file_content: str) -> str:
        """创建专门为Claude优化的提示词"""
        return f"""你是一名资深代码修复专家，擅长根据SonarQube检测结果修复代码中的Critical级别问题。

请修复以下代码中的SonarQube Critical问题：

【问题信息】
- 规则代码: {issue.rule}
- 严重程度: {issue.severity} 
- 问题描述: {issue.message}
- 文件位置: {issue.get_location_info()}
- 问题类型: {issue.type}

【当前代码文件】
```{getattr(issue, 'language', 'text')}
{file_content}
```

【修复指南】
1. 仔细分析SonarQube检测出的具体问题
2. 只修复指定的问题，保持其他代码不变
3. 确保修复后的代码符合最佳实践
4. 保持原有的业务逻辑和代码风格

请只返回修复后的完整代码文件内容，不要添加任何解释或代码块标记。
"""
    
    def _clean_code_blocks(self, content: str) -> str:
        """清理代码块标记"""
        if content.startswith("```"):
            lines = content.split('\n')
            if len(lines) > 2:
                content = '\n'.join(lines[1:-1])
        return content

class AIClientFactory:
    """AI客户端工厂"""
    
    @staticmethod
    def create_client() -> AIClient:
        """根据配置创建AI客户端"""
        provider = Config.AI_PROVIDER.lower()
        
        if provider == 'openai':
            Config.validate_ai_config()
            return EnhancedOpenAIClient(
                api_key=Config.OPENAI_API_KEY,
                model=Config.AI_MODEL,
                base_url=Config.OPENAI_BASE_URL
            )
        
        elif provider == 'anthropic':
            Config.validate_ai_config()
            return EnhancedAnthropicClient(
                api_key=Config.ANTHROPIC_API_KEY,
                model=Config.AI_MODEL
            )
        
        else:
            raise ValueError(f"不支持的AI提供商: {provider}")

    @staticmethod
    def create_langchain_client() -> AIClient:
        """创建基于LangChain的AI客户端（需要Python >=3.9）"""
        if not LANGCHAIN_AVAILABLE:
            raise ImportError(
                "LangChain不可用。需要Python >=3.9和LangChain库。\n"
                "当前使用增强版标准客户端，已包含优化的提示词。"
            )
        
        # TODO: 在Python >=3.9环境中实现LangChain客户端
        raise NotImplementedError("LangChain客户端需要Python >=3.9，请使用标准增强版客户端")

class CodeFixer:
    """代码修复器"""
    
    def __init__(self):
        self.ai_client = AIClientFactory.create_client()
    
    def fix_issue(self, issue: SonarIssue, file_path: str) -> Optional[Dict[str, Any]]:
        """修复单个问题"""
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            logger.info(f"正在修复问题: {issue.key} in {file_path}")
            
            # 使用AI修复代码
            fixed_content = self.ai_client.fix_code_issue(issue, original_content)
            
            if not fixed_content:
                logger.error(f"AI修复失败: {issue.key}")
                return None
            
            # 检查是否有实际修改
            if fixed_content.strip() == original_content.strip():
                logger.info(f"代码无需修改: {issue.key}")
                return None
            
            return {
                'issue': issue,
                'file_path': file_path,
                'original_content': original_content,
                'fixed_content': fixed_content,
                'diff': self._generate_diff(original_content, fixed_content)
            }
            
        except Exception as e:
            logger.error(f"修复问题失败 {issue.key}: {e}")
            return None
    
    def _generate_diff(self, original: str, fixed: str) -> str:
        """生成代码差异"""
        import difflib
        
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            fixed.splitlines(keepends=True),
            fromfile='原始代码',
            tofile='修复后代码',
            lineterm=''
        )
        
        return ''.join(diff)
    
    def fix_multiple_issues(self, issues: List[SonarIssue], repository_path: str) -> List[Dict[str, Any]]:
        """修复多个问题"""
        fixes = []
        
        # 按文件分组问题
        issues_by_file = {}
        for issue in issues:
            file_path = os.path.join(repository_path, issue.get_file_path())
            if file_path not in issues_by_file:
                issues_by_file[file_path] = []
            issues_by_file[file_path].append(issue)
        
        # 逐文件修复
        for file_path, file_issues in issues_by_file.items():
            if not os.path.exists(file_path):
                logger.warning(f"文件不存在: {file_path}")
                continue
            
            for issue in file_issues:
                fix_result = self.fix_issue(issue, file_path)
                if fix_result:
                    fixes.append(fix_result)
        
        return fixes
