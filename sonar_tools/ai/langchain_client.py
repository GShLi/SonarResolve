"""
LangChain客户端 - 通过LiteLLM代理连接OpenAI
"""

import json
import logging
from typing import Any, Dict, Optional

from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from ..core.config import Config

logger = logging.getLogger(__name__)


class LangChainClient:
    """LangChain客户端，通过LiteLLM代理连接大模型"""
    
    def __init__(self):
        """初始化LangChain客户端"""
        self.config = Config
        self._validate_config()
        self._initialize_client()
    
    def _validate_config(self):
        """验证配置"""
        if not self.config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY 未配置")
        
        if not self.config.OPENAI_BASE_URL:
            logger.warning("OPENAI_BASE_URL 未配置，将使用默认OpenAI API")
    
    def _initialize_client(self):
        """初始化LangChain ChatOpenAI客户端"""
        try:
            # 配置参数
            client_config = {
                "model": self.config.AI_MODEL,
                "temperature": self.config.AI_TEMPERATURE,
                "max_tokens": self.config.AI_MAX_TOKENS,
                "api_key": self.config.OPENAI_API_KEY,
            }
            
            # 如果配置了自定义BASE_URL（LiteLLM代理），则使用
            if self.config.OPENAI_BASE_URL:
                client_config["base_url"] = self.config.OPENAI_BASE_URL
                logger.info(f"使用自定义API端点: {self.config.OPENAI_BASE_URL}")
            
            self.llm = ChatOpenAI(**client_config)
            
            logger.info(
                f"LangChain客户端初始化成功 - 模型: {self.config.AI_MODEL}, "
                f"温度: {self.config.AI_TEMPERATURE}"
            )
            
        except Exception as e:
            logger.error(f"LangChain客户端初始化失败: {e}")
            raise
    
    def chat(self, system_message: str, user_message: str) -> str:
        """
        发送聊天请求
        
        Args:
            system_message: 系统提示词
            user_message: 用户消息
            
        Returns:
            AI响应内容
        """
        try:
            messages = [
                SystemMessage(content=system_message),
                HumanMessage(content=user_message)
            ]
            
            logger.debug(f"发送AI请求 - 模型: {self.config.AI_MODEL}")
            response = self.llm.invoke(messages)
            
            content = response.content.strip()
            logger.debug(f"AI响应长度: {len(content)} 字符")
            
            return content
            
        except Exception as e:
            logger.error(f"AI请求失败: {e}")
            raise
    
    def analyze_code_issue(self, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析代码问题
        
        Args:
            issue_data: 包含SonarQube问题信息的字典
            
        Returns:
            分析结果字典
        """
        from .prompts import PromptTemplates
        
        try:
            # 构建分析提示词
            system_prompt = PromptTemplates.get_analysis_system_prompt()
            user_prompt = PromptTemplates.build_analysis_prompt(issue_data)
            
            # 发送请求
            response = self.chat(system_prompt, user_prompt)
            
            # 尝试解析JSON响应
            try:
                result = json.loads(response)
                logger.info(f"成功分析问题: {issue_data.get('key', 'Unknown')}")
                return result
            except json.JSONDecodeError:
                logger.warning("AI响应不是有效JSON，返回文本响应")
                return {
                    "analysis": {
                        "issue_type": "解析错误",
                        "root_cause": "AI响应格式错误",
                        "risk_level": "未知"
                    },
                    "raw_response": response
                }
                
        except Exception as e:
            logger.error(f"分析代码问题失败: {e}")
            return {
                "analysis": {
                    "issue_type": "分析失败", 
                    "root_cause": str(e),
                    "risk_level": "未知"
                },
                "error": str(e)
            }
    
    def fix_code_issue(self, issue_data: Dict[str, Any], analysis_result: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        修复代码问题
        
        Args:
            issue_data: SonarQube问题数据
            analysis_result: 分析结果（可选）
            
        Returns:
            修复结果字典
        """
        from .prompts import PromptTemplates
        
        try:
            # 构建修复提示词
            system_prompt = PromptTemplates.get_fix_system_prompt()
            user_prompt = PromptTemplates.build_fix_prompt(issue_data, analysis_result)
            
            # 发送请求
            response = self.chat(system_prompt, user_prompt)
            
            # 尝试解析JSON响应
            try:
                result = json.loads(response)
                logger.info(f"成功生成修复方案: {issue_data.get('key', 'Unknown')}")
                return result
            except json.JSONDecodeError:
                logger.warning("AI修复响应不是有效JSON，返回文本响应")
                return {
                    "solution": {
                        "strategy": "解析错误",
                        "changes": "AI响应格式错误",
                        "impact": "未知"
                    },
                    "fixed_code": "",
                    "raw_response": response
                }
                
        except Exception as e:
            logger.error(f"修复代码问题失败: {e}")
            return {
                "solution": {
                    "strategy": "修复失败",
                    "changes": str(e), 
                    "impact": "未知"
                },
                "error": str(e)
            }
    
    def validate_fix(self, original_code: str, fixed_code: str, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证修复质量
        
        Args:
            original_code: 原始代码
            fixed_code: 修复后代码
            issue_data: 问题数据
            
        Returns:
            验证结果字典
        """
        from .prompts import PromptTemplates
        
        try:
            # 构建验证提示词
            system_prompt = PromptTemplates.get_validation_system_prompt()
            user_prompt = PromptTemplates.build_validation_prompt(
                original_code, fixed_code, issue_data
            )
            
            # 发送请求
            response = self.chat(system_prompt, user_prompt)
            
            # 尝试解析JSON响应
            try:
                result = json.loads(response)
                logger.info(f"成功验证修复: {issue_data.get('key', 'Unknown')}")
                return result
            except json.JSONDecodeError:
                logger.warning("AI验证响应不是有效JSON，返回文本响应")
                return {
                    "overall_score": 0,
                    "compliance_check": False,
                    "quality_grade": "F",
                    "raw_response": response
                }
                
        except Exception as e:
            logger.error(f"验证修复失败: {e}")
            return {
                "overall_score": 0,
                "compliance_check": False,
                "quality_grade": "F",
                "error": str(e)
            }
    
    def generate_commit_info(self, issue_data: Dict[str, Any], fix_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成提交信息和MR描述
        
        Args:
            issue_data: 问题数据
            fix_result: 修复结果
            
        Returns:
            提交信息字典
        """
        from .prompts import PromptTemplates
        
        try:
            # 构建提交信息生成提示词
            system_prompt = PromptTemplates.get_commit_system_prompt()
            user_prompt = PromptTemplates.build_commit_prompt(issue_data, fix_result)
            
            # 发送请求
            response = self.chat(system_prompt, user_prompt)
            
            # 尝试解析JSON响应
            try:
                result = json.loads(response)
                logger.info(f"成功生成提交信息: {issue_data.get('key', 'Unknown')}")
                return result
            except json.JSONDecodeError:
                logger.warning("AI提交信息响应不是有效JSON，返回默认信息")
                return {
                    "commit": {
                        "type": "fix",
                        "scope": "sonar",
                        "subject": f"修复SonarQube问题 {issue_data.get('rule', 'Unknown')}",
                        "body": "SonarQube Critical问题自动修复",
                        "footer": ""
                    },
                    "merge_request": {
                        "title": f"自动修复: {issue_data.get('rule', 'SonarQube问题')}",
                        "description": "SonarQube Critical问题自动修复",
                        "labels": ["代码质量", "SonarQube", "自动修复"]
                    },
                    "raw_response": response
                }
                
        except Exception as e:
            logger.error(f"生成提交信息失败: {e}")
            return {
                "commit": {
                    "type": "fix",
                    "scope": "sonar", 
                    "subject": f"修复SonarQube问题",
                    "body": "SonarQube Critical问题自动修复",
                    "footer": ""
                },
                "error": str(e)
            }
    
    def test_connection(self) -> bool:
        """测试AI连接"""
        try:
            response = self.chat(
                "你是一个代码助手。",
                "请回复'连接成功'来确认连接正常。"
            )
            
            if "连接成功" in response or "成功" in response:
                logger.info("AI连接测试成功")
                return True
            else:
                logger.warning(f"AI连接测试响应异常: {response}")
                return False
                
        except Exception as e:
            logger.error(f"AI连接测试失败: {e}")
            return False
