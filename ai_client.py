import os
import logging
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from models import SonarIssue
from config import Config

logger = logging.getLogger(__name__)

class AIClient(ABC):
    """AI客户端抽象基类"""
    
    @abstractmethod
    def fix_code_issue(self, issue: SonarIssue, file_content: str) -> Optional[str]:
        """修复代码问题"""
        pass

class OpenAIClient(AIClient):
    """OpenAI客户端"""
    
    def __init__(self, api_key: str, model: str = "gpt-4", base_url: str = None):
        try:
            import openai
            self.client = openai.OpenAI(
                api_key=api_key,
                base_url=base_url
            )
            self.model = model
            logger.info(f"OpenAI客户端初始化成功，使用模型: {model}")
        except ImportError:
            raise ImportError("请安装openai库: pip install openai")
        except Exception as e:
            logger.error(f"OpenAI客户端初始化失败: {e}")
            raise
    
    def fix_code_issue(self, issue: SonarIssue, file_content: str) -> Optional[str]:
        """使用OpenAI修复代码问题"""
        try:
            prompt = self._create_fix_prompt(issue, file_content)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的代码审查和修复专家。请根据SonarQube的检测结果修复代码问题，只返回修复后的完整文件内容，不要添加任何解释或标记。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1
            )
            
            fixed_content = response.choices[0].message.content.strip()
            
            # 移除可能的代码块标记
            if fixed_content.startswith("```"):
                lines = fixed_content.split('\n')
                if len(lines) > 2:
                    # 移除开头和结尾的```行
                    fixed_content = '\n'.join(lines[1:-1])
            
            return fixed_content
            
        except Exception as e:
            logger.error(f"OpenAI修复代码失败: {e}")
            return None
    
    def _create_fix_prompt(self, issue: SonarIssue, file_content: str) -> str:
        """创建修复提示词"""
        return f"""
请修复以下代码中的SonarQube Critical问题：

**问题信息：**
- 规则: {issue.rule}
- 严重程度: {issue.severity}
- 问题描述: {issue.message}
- 文件位置: {issue.get_location_info()}
- 问题类型: {issue.type}

**当前文件内容：**
```
{file_content}
```

**修复要求：**
1. 只修复指定的SonarQube问题，不要改动其他代码
2. 保持代码的原有逻辑和功能
3. 确保修复后的代码符合最佳实践
4. 返回修复后的完整文件内容
5. 不要添加任何解释或注释，只返回修复后的代码

请返回修复后的完整文件内容：
"""

class AnthropicClient(AIClient):
    """Anthropic Claude客户端"""
    
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = model
            logger.info(f"Anthropic客户端初始化成功，使用模型: {model}")
        except ImportError:
            raise ImportError("请安装anthropic库: pip install anthropic")
        except Exception as e:
            logger.error(f"Anthropic客户端初始化失败: {e}")
            raise
    
    def fix_code_issue(self, issue: SonarIssue, file_content: str) -> Optional[str]:
        """使用Anthropic修复代码问题"""
        try:
            prompt = self._create_fix_prompt(issue, file_content)
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            fixed_content = response.content[0].text.strip()
            
            # 移除可能的代码块标记
            if fixed_content.startswith("```"):
                lines = fixed_content.split('\n')
                if len(lines) > 2:
                    fixed_content = '\n'.join(lines[1:-1])
            
            return fixed_content
            
        except Exception as e:
            logger.error(f"Anthropic修复代码失败: {e}")
            return None
    
    def _create_fix_prompt(self, issue: SonarIssue, file_content: str) -> str:
        """创建修复提示词"""
        return f"""
你是一个专业的代码审查和修复专家。请根据SonarQube的检测结果修复代码问题。

**问题信息：**
- 规则: {issue.rule}
- 严重程度: {issue.severity}
- 问题描述: {issue.message}
- 文件位置: {issue.get_location_info()}
- 问题类型: {issue.type}

**当前文件内容：**
```
{file_content}
```

**修复要求：**
1. 只修复指定的SonarQube问题，不要改动其他代码
2. 保持代码的原有逻辑和功能
3. 确保修复后的代码符合最佳实践
4. 返回修复后的完整文件内容
5. 不要添加任何解释或注释，只返回修复后的代码

请返回修复后的完整文件内容：
"""

class AIClientFactory:
    """AI客户端工厂"""
    
    @staticmethod
    def create_client() -> AIClient:
        """根据配置创建AI客户端"""
        provider = Config.AI_PROVIDER.lower()
        
        if provider == 'openai':
            Config.validate_ai_config()
            return OpenAIClient(
                api_key=Config.OPENAI_API_KEY,
                model=Config.AI_MODEL,
                base_url=Config.OPENAI_BASE_URL
            )
        
        elif provider == 'anthropic':
            Config.validate_ai_config()
            return AnthropicClient(
                api_key=Config.ANTHROPIC_API_KEY,
                model=Config.AI_MODEL
            )
        
        else:
            raise ValueError(f"不支持的AI提供商: {provider}")

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
