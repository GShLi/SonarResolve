"""
LangChain客户端 - 通过LiteLLM代理连接OpenAI
"""

import json
from typing import Any, Dict

from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from sonar_tools.core.config import Config

logger = Config.setup_logging(__name__)


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
                HumanMessage(content=user_message),
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
            分析结果字典，包含问题分析和范围信息
        """
        from sonar_tools.ai.prompts import PromptTemplates

        try:
            # 构建分析提示词
            system_prompt = PromptTemplates.get_analysis_system_prompt()
            user_prompt = PromptTemplates.build_analysis_prompt(issue_data)

            # 发送请求
            response = self.chat(system_prompt, user_prompt)

            # 尝试解析JSON响应
            try:
                result = json.loads(response)

                # 验证并增强范围分析结果
                if "scope" in result:
                    scope_info = result["scope"]

                    # 如果AI识别出是函数内部问题，记录相关信息
                    if scope_info.get("is_function_internal"):
                        logger.info(
                            f"检测到函数内部问题: {issue_data.get('key', 'Unknown')}, "
                            f"函数: {scope_info.get('function_name', 'Unknown')}"
                        )

                        # 记录函数范围估算
                        start_line = scope_info.get("estimated_function_start_line")
                        end_line = scope_info.get("estimated_function_end_line")
                        if start_line and end_line:
                            logger.info(f"估算函数范围: {start_line}-{end_line} 行")

                logger.info(f"成功分析问题: {issue_data.get('key', 'Unknown')}")
                return result

            except json.JSONDecodeError:
                logger.warning("AI响应不是有效JSON，返回文本响应")
                return {
                    "analysis": {
                        "issue_type": "解析错误",
                        "root_cause": "AI响应格式错误",
                        "risk_level": "未知",
                    },
                    "scope": {
                        "scope_type": "unknown",
                        "is_function_internal": False,
                        "function_name": None,
                        "context_analysis": "JSON解析失败，无法进行范围分析",
                    },
                    "raw_response": response,
                }

        except Exception as e:
            logger.error(f"分析代码问题失败: {e}")
            return {
                "analysis": {
                    "issue_type": "分析失败",
                    "root_cause": str(e),
                    "risk_level": "未知",
                },
                "scope": {
                    "scope_type": "unknown",
                    "is_function_internal": False,
                    "function_name": None,
                    "context_analysis": f"分析异常: {e}",
                },
                "error": str(e),
            }

    def analyze_function_scope(
        self, file_path: str, issue_line: int, language: str
    ) -> Dict[str, Any]:
        """
        精确分析函数范围

        Args:
            file_path: 文件路径
            issue_line: 问题所在行号
            language: 编程语言

        Returns:
            函数范围分析结果
        """
        try:
            from pathlib import Path

            # 读取完整文件内容
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                logger.warning(f"文件不存在: {file_path}")
                return {"success": False, "error": "文件不存在"}

            with open(file_path_obj, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # 构建函数范围分析提示词
            system_prompt = """你是一个专业的代码结构分析专家。你的任务是分析给定文件中特定行号所在函数的精确边界。

请分析文件内容，找到包含指定行号的函数，并确定该函数的确切开始和结束行号。

你必须以JSON格式回复：
{
  "success": true/false,
  "function_found": true/false,
  "function_name": "函数名称",
  "start_line": "函数开始行号(1-based)",
  "end_line": "函数结束行号(1-based)",
  "function_signature": "函数签名",
  "scope_type": "function/method/lambda/closure",
  "analysis_notes": "分析说明"
}

请确保行号准确，这将用于精确的代码修复操作。"""

            # 构建包含行号的文件内容
            numbered_content = ""
            for i, line in enumerate(lines, 1):
                marker = " <<<< ISSUE LINE" if i == issue_line else ""
                numbered_content += f"{i:4d}: {line.rstrip()}{marker}\n"

            user_prompt = f"""请分析以下{language}代码文件，找到第{issue_line}行所在的函数边界：

## 任务
- 目标行号: {issue_line}
- 编程语言: {language}
- 文件路径: {file_path}

## 完整文件内容（带行号）
```{language}
{numbered_content}
```

请仔细分析代码结构，确定第{issue_line}行所在函数的精确边界，并以JSON格式返回结果。"""

            # 发送请求
            response = self.chat(system_prompt, user_prompt)

            # 解析响应
            try:
                result = json.loads(response)

                if result.get("success") and result.get("function_found"):
                    logger.info(
                        f"成功分析函数范围: {result.get('function_name')} "
                        f"({result.get('start_line')}-{result.get('end_line')})"
                    )
                else:
                    logger.warning(f"未找到函数或分析失败: {file_path}:{issue_line}")

                return result

            except json.JSONDecodeError:
                logger.warning("函数范围分析响应不是有效JSON")
                return {
                    "success": False,
                    "function_found": False,
                    "error": "JSON解析失败",
                    "raw_response": response,
                }

        except Exception as e:
            logger.error(f"函数范围分析失败: {e}")
            return {"success": False, "function_found": False, "error": str(e)}

    def fix_code_issue(
        self, issue_data: Dict[str, Any], analysis_result: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        修复代码问题

        Args:
            issue_data: SonarQube问题数据
            analysis_result: 分析结果（可选）

        Returns:
            修复结果字典
        """
        from sonar_tools.ai.prompts import PromptTemplates

        try:
            # 构建修复提示词
            system_prompt = PromptTemplates.get_fix_system_prompt()
            user_prompt = PromptTemplates.build_fix_prompt(issue_data, analysis_result)

            # 发送请求
            response = self.chat(system_prompt, user_prompt)

            # 尝试解析JSON响应
            try:
                result = json.loads(response)

                # 验证新的代码结构
                if "fixed_code" in result and isinstance(result["fixed_code"], dict):
                    logger.info(
                        f"成功生成拆分格式修复方案: {issue_data.get('key', 'Unknown')}"
                    )
                    fixed_code_info = result["fixed_code"]
                    logger.debug(
                        f"导入代码: {len(fixed_code_info.get('imports', ''))} 字符"
                    )
                    logger.debug(
                        f"函数代码: {len(fixed_code_info.get('function_code', ''))} 字符"
                    )
                else:
                    logger.info(f"成功生成修复方案: {issue_data.get('key', 'Unknown')}")

                return result
            except json.JSONDecodeError:
                logger.warning("AI修复响应不是有效JSON，返回文本响应")
                return {
                    "solution": {
                        "strategy": "解析错误",
                        "changes": "AI响应格式错误",
                        "impact": "未知",
                    },
                    "fixed_code": {"imports": "", "function_code": "", "full_code": ""},
                    "raw_response": response,
                }

        except Exception as e:
            logger.error(f"修复代码问题失败: {e}")
            return {
                "solution": {
                    "strategy": "修复失败",
                    "changes": str(e),
                    "impact": "未知",
                },
                "fixed_code": {"imports": "", "function_code": "", "full_code": ""},
                "error": str(e),
            }

    def validate_fix(
        self, original_code: str, fixed_code: str, issue_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        验证修复质量

        Args:
            original_code: 原始代码
            fixed_code: 修复后代码
            issue_data: 问题数据

        Returns:
            验证结果字典
        """
        from sonar_tools.ai.prompts import PromptTemplates

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
                    "raw_response": response,
                }

        except Exception as e:
            logger.error(f"验证修复失败: {e}")
            return {
                "overall_score": 0,
                "compliance_check": False,
                "quality_grade": "F",
                "error": str(e),
            }

    def apply_code_fix(
        self, original_content: str, fixed_code_data: Any, issue_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        使用AI智能应用代码修复

        Args:
            original_content: 原始文件内容
            fixed_code_data: AI生成的修复代码（可能是字符串或包含拆分结构的字典）
            issue_data: SonarQube问题数据

        Returns:
            应用结果字典，包含修改后的文件内容
        """
        from sonar_tools.ai.prompts import PromptTemplates

        try:
            # 构建代码应用提示词
            system_prompt = PromptTemplates.get_code_application_system_prompt()
            user_prompt = PromptTemplates.build_code_application_prompt(
                original_content, fixed_code_data, issue_data
            )

            # 发送请求
            response = self.chat(system_prompt, user_prompt)

            # 尝试解析JSON响应
            try:
                result = json.loads(response)
                logger.info(f"AI成功应用代码修复: {issue_data.get('key', 'Unknown')}")

                # 验证返回的内容
                if result.get("success") and result.get("modified_content"):
                    logger.info(f"应用策略: {result.get('strategy_used')}")
                    logger.info(f"信心等级: {result.get('confidence')}/10")
                    if result.get("warnings"):
                        logger.warning(f"AI应用警告: {result.get('warnings')}")
                    return result
                else:
                    logger.error("AI无法应用修复代码")
                    return {
                        "success": False,
                        "strategy_used": "应用失败",
                        "modified_content": original_content,
                        "changes_summary": "AI无法确定如何应用修复",
                        "confidence": 0,
                        "warnings": ["AI应用失败"],
                        "raw_response": response,
                    }

            except json.JSONDecodeError:
                logger.warning("AI代码应用响应不是有效JSON")
                return {
                    "success": False,
                    "strategy_used": "JSON解析失败",
                    "modified_content": original_content,
                    "changes_summary": "AI响应格式错误",
                    "confidence": 0,
                    "warnings": ["JSON解析失败"],
                    "raw_response": response,
                }

        except Exception as e:
            logger.error(f"AI代码应用失败: {e}")
            return {
                "success": False,
                "strategy_used": "异常失败",
                "modified_content": original_content,
                "changes_summary": f"异常: {e}",
                "confidence": 0,
                "warnings": [f"系统异常: {e}"],
                "error": str(e),
            }

    def generate_commit_info(
        self, issue_data: Dict[str, Any], fix_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成提交信息和MR描述

        Args:
            issue_data: 问题数据
            fix_result: 修复结果

        Returns:
            提交信息字典
        """
        from sonar_tools.ai.prompts import PromptTemplates

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
                        "footer": "",
                    },
                    "merge_request": {
                        "title": f"自动修复: {issue_data.get('rule', 'SonarQube问题')}",
                        "description": "SonarQube Critical问题自动修复",
                        "labels": ["代码质量", "SonarQube", "自动修复"],
                    },
                    "raw_response": response,
                }

        except Exception as e:
            logger.error(f"生成提交信息失败: {e}")
            return {
                "commit": {
                    "type": "fix",
                    "scope": "sonar",
                    "subject": "修复SonarQube问题",
                    "body": "SonarQube Critical问题自动修复",
                    "footer": "",
                },
                "error": str(e),
            }

    def test_connection(self) -> bool:
        """测试AI连接"""
        try:
            response = self.chat(
                "你是一个代码助手。", "请回复'连接成功'来确认连接正常。"
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
