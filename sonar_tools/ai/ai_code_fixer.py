"""
AI代码修复器
集成LangChain、SonarQube和GitLab，实现自动代码修复
"""

import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..clients.git_client import AutoFixProcessor, GitClient, GitLabManager
from ..clients.sonarqube_client import SonarQubeClient
from ..core.config import Config
from ..core.models import SonarIssue
from ..clients.langchain_client import LangChainClient

logger = logging.getLogger(__name__)


class AICodeFixer:
    """AI代码自动修复器"""

    def __init__(self):
        """初始化AI代码修复器"""
        self.config = Config
        self._validate_config()
        self._initialize_clients()

    def _validate_config(self):
        """验证配置"""
        self.config.validate_ai_config()
        self.config.validate_gitlab_config()

    def _initialize_clients(self):
        """初始化客户端"""
        try:
            # 初始化SonarQube客户端
            self.sonar_client = SonarQubeClient(
                self.config.SONARQUBE_URL,
                self.config.SONARQUBE_TOKEN
            )

            # 初始化Git相关客户端
            self.git_client = GitClient()

            # 初始化AI客户端
            self.ai_client = LangChainClient()

            logger.info("所有客户端初始化成功")

        except Exception as e:
            logger.error(f"客户端初始化失败: {e}")
            raise

    def process_critical_issues(self, project_key: str = None) -> bool:
        """
        处理Critical问题
        
        Args:
            project_key: 可选的项目Key，如果不提供则处理所有项目
            
        Returns:
            处理是否成功
        """
        try:
            # 获取Critical问题
            issues = self.sonar_client.get_critical_issues(project_key)
            if not issues:
                logger.info("没有发现Critical问题")
                return True

            # 按项目分组处理问题
            issues_by_project = self._group_issues_by_project(issues)
            
            for project_name, project_issues in issues_by_project.items():
                self._process_project_issues(project_name, project_issues)

            return True

        except Exception as e:
            logger.error(f"处理Critical问题失败: {e}")
            return False

    def _group_issues_by_project(self, issues: List[SonarIssue]) -> Dict[str, List[SonarIssue]]:
        """按项目分组问题"""
        issues_by_project = {}
        
        for issue in issues:
            project_name = issue.project
            if project_name not in issues_by_project:
                issues_by_project[project_name] = []
            issues_by_project[project_name].append(issue)
            
        return issues_by_project

    def _process_project_issues(self, project_name: str, issues: List[SonarIssue]) -> bool:
        """处理单个项目的问题"""
        try:
            logger.info(f"开始处理项目 {project_name} 的问题，共 {len(issues)} 个")

            # 准备Git仓库
            success, repo_path, repo_info = self.git_client.prepare_repository_for_project(project_name)
            if not success or not repo_path or not repo_info:
                logger.error(f"准备Git仓库失败: {project_name}")
                return False

            # 创建GitLab MR管理器
            gitlab_manager = GitLabManager(repo_info["id"])

            # 创建修复分支
            branch_name = f"fix/sonar-critical-{int(time.time())}"
            if not self.git_client.create_branch(repo_path, branch_name):
                logger.error("创建修复分支失败")
                return False

            # 处理每个问题
            modified_files = []
            for issue in issues:
                if self._fix_single_issue(issue, repo_path):
                    relative_path = issue.component.split(":")[-1]  # 获取相对路径
                    modified_files.append(relative_path)

            if not modified_files:
                logger.warning("没有文件被修复")
                return False

            # 提交更改
            commit_info = self._generate_commit_info(issues)
            if not self.git_client.commit_changes(repo_path, modified_files, commit_info["commit_message"]):
                logger.error("提交更改失败")
                return False

            # 推送分支
            if not self.git_client.push_branch(repo_path, branch_name):
                logger.error("推送分支失败")
                return False

            # 创建Merge Request
            mr_result = gitlab_manager.create_merge_request(
                project_id=repo_info["id"],
                source_branch=branch_name,
                target_branch=repo_info["default_branch"],
                title=commit_info["mr_title"],
                description=commit_info["mr_description"],
                labels=["SonarQube", "Critical-Fix", "AI-Generated"]
            )

            if not mr_result:
                logger.error("创建Merge Request失败")
                return False

            logger.info(f"成功创建Merge Request: {mr_result['url']}")
            return True

        except Exception as e:
            logger.error(f"处理项目问题失败: {e}")
            return False

    def _fix_single_issue(self, issue: SonarIssue, repo_path: Path) -> bool:
        """修复单个问题"""
        try:
            logger.info(f"开始修复问题: {issue.key}")

            # 准备问题数据
            issue_data = {
                "key": issue.key,
                "rule": issue.rule,
                "message": issue.message,
                "component": issue.component,
                "project": issue.project,
                "severity": issue.severity,
                "line": issue.line,
                "code_snippet": issue.code_snippet,
                "rule_info": issue.rule_info
            }

            # 分析问题
            analysis_result = self.ai_client.analyze_code_issue(issue_data)
            if not analysis_result:
                logger.error(f"问题分析失败: {issue.key}")
                return False

            # 生成修复方案
            fix_result = self.ai_client.fix_code_issue(issue_data, analysis_result)
            if not fix_result or "fixed_code" not in fix_result:
                logger.error(f"生成修复方案失败: {issue.key}")
                return False

            # 验证修复
            validation_result = self.ai_client.validate_fix(
                issue.code_snippet,
                fix_result["fixed_code"],
                issue_data
            )

            if not validation_result.get("compliance_check", False):
                logger.error(f"修复验证失败: {issue.key}")
                return False

            # 应用修复
            relative_path = issue.component.split(":")[-1]  # 获取相对路径
            file_path = repo_path / relative_path

            # 构建修复数据，包含所有必要信息
            fix_data = {
                "file_path": relative_path,
                "fixed_code": fix_result["fixed_code"],
                "code_snippet": issue.code_snippet,
                "line": issue.line,
                "language": issue_data.get("language", ""),
                "issue_key": issue.key,
                "rule": issue.rule
            }

            if self._apply_fix(file_path, fix_data):
                logger.info(f"成功修复问题: {issue.key}")
                return True
            else:
                logger.error(f"应用修复失败: {issue.key}")
                return False

        except Exception as e:
            logger.error(f"修复问题失败 {issue.key}: {e}")
            return False

    def _generate_commit_info(self, issues: List[SonarIssue]) -> Dict[str, str]:
        """生成提交信息"""
        issue_count = len(issues)
        rules = {issue.rule for issue in issues}
        
        commit_message = f"fix: 修复 {issue_count} 个SonarQube Critical问题\n\n"
        commit_message += "修复的规则:\n" + "\n".join(f"- {rule}" for rule in rules)
        
        mr_description = (
            f"# AI自动修复报告\n\n"
            f"本MR修复了 {issue_count} 个SonarQube Critical问题。\n\n"
            f"## 修复的问题\n"
        )
        
        for issue in issues:
            mr_description += f"\n### {issue.rule}\n"
            mr_description += f"- 问题描述: {issue.message}\n"
            mr_description += f"- 文件: {issue.component}\n"
            mr_description += f"- 行数: {issue.line}\n"
        
        mr_description += "\n\n请仔细review修改内容。"
        
        return {
            "commit_message": commit_message,
            "mr_title": f"fix(sonar): 修复 {issue_count} 个Critical问题",
            "mr_description": mr_description
        }

    def test_connection(self) -> bool:
        """测试所有连接"""
        try:
            # 测试SonarQube连接
            if not self.sonar_client.test_connection():
                logger.error("SonarQube连接测试失败")
                return False

            # 测试AI连接
            if not self.ai_client.test_connection():
                logger.error("AI连接测试失败")
                return False

            logger.info("所有连接测试成功")
            return True

        except Exception as e:
            logger.error(f"连接测试失败: {e}")
            return False

    def process_project_fixes(self, project_name: str, fixes: list) -> bool:
        """处理项目的自动修复"""
        # 准备仓库
        (
            success,
            local_path,
            repo_info,
        ) = self.git_client.prepare_repository_for_project(project_name)

        if not success:
            logger.error(f"无法准备项目仓库: {project_name}")
            return False

        # 创建修复分支
        branch_name = f"fix/sonar-issues-{int(time.time())}"
        if not self.git_client.create_branch(local_path, branch_name):
            logger.error("创建修复分支失败")
            return False

        # 应用修复
        modified_files = []
        for fix in fixes:
            file_path = local_path / fix["file_path"]
            if self._apply_fix(file_path, fix):
                modified_files.append(fix["file_path"])

        if not modified_files:
            logger.warning("没有文件被修改")
            return False

        # 提交更改
        commit_message = "自动修复SonarQube Critical问题\n\n修复的文件:\n" + "\n".join(
            f"- {f}" for f in modified_files
        )

        if not self.git_client.commit_changes(local_path, modified_files, commit_message):
            logger.error("提交更改失败")
            return False

        # 推送分支
        if not self.git_client.push_branch(local_path, branch_name):
            logger.error("推送分支失败")
            return False

        logger.info(f"自动修复完成，分支: {branch_name}")
        return True

    def _apply_fix(self, file_path: Path, fix: dict) -> bool:
        """应用单个修复"""
        try:
            if not file_path.exists():
                logger.error(f"文件不存在: {file_path}")
                return False

            # 读取文件内容
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 智能应用修复
            if self._apply_smart_fix(file_path, content, fix):
                logger.info(f"应用修复成功: {file_path}")
                return True
            else:
                logger.error(f"应用修复失败: {file_path}")
                return False

        except Exception as e:
            logger.error(f"应用修复失败 {file_path}: {e}")
            return False

    def _apply_smart_fix(self, file_path: Path, content: str, fix: dict) -> bool:
        """智能应用代码修复（支持AI应用和传统方法）"""
        # TODO: 该方法需要重写
        try:
            # 获取修复信息
            fixed_code = fix.get("fixed_code", "").strip()
            if not fixed_code:
                logger.error("没有有效的修复代码")
                return False

            # 首先尝试AI智能应用（推荐方式）
            if self._try_ai_application(file_path, content, fix):
                return True
            
            logger.info("AI应用失败，回退到传统修复策略")
            
            # 回退到传统的多策略修复方法
            strategies = []

            for strategy in strategies:
                try:
                    new_content = strategy(content, fix)
                    if new_content and new_content != content:
                        # 写回文件
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(new_content)
                        logger.info(f"使用策略 {strategy.__name__} 修复成功")
                        return True
                except Exception as e:
                    logger.debug(f"修复策略 {strategy.__name__} 失败: {e}")
                    continue

            logger.error("所有修复策略都失败了")
            return False

        except Exception as e:
            logger.error(f"智能修复失败: {e}")
            return False

    def _try_ai_application(self, file_path: Path, content: str, fix: dict) -> bool:
        """尝试使用AI智能应用修复"""
        try:
            # 检查是否启用AI应用
            from ..core.config import Config
            if not getattr(Config, 'AI_APPLY_FIXES', True):
                logger.debug("AI应用修复已禁用")
                return False

            fixed_code = fix.get("fixed_code", "")
            
            # 构造问题数据
            issue_data = {
                "component": str(file_path),
                "line": fix.get("line", 0),
                "language": fix.get("language", self._detect_language(file_path)),
                "message": fix.get("message", "SonarQube Critical issue"),
                "code_snippet": fix.get("code_snippet", ""),
                "key": fix.get("key", f"issue_{file_path.name}")
            }
            
            # 使用AI应用修复
            result = self.ai_client.apply_code_fix(content, fixed_code, issue_data)
            
            if result.get("success") and result.get("modified_content"):
                confidence = result.get("confidence", 0)
                threshold = getattr(Config, 'AI_APPLY_CONFIDENCE_THRESHOLD', 7)
                
                if confidence >= threshold:  # 使用配置的信心阈值
                    # 写回文件
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(result["modified_content"])
                    
                    logger.info(f"AI应用修复成功 - 策略: {result.get('strategy_used')}, 信心: {confidence}/10")
                    if result.get("warnings"):
                        logger.warning(f"AI应用警告: {', '.join(result['warnings'])}")
                    
                    return True
                else:
                    logger.warning(f"AI应用信心不足: {confidence}/10 < {threshold}，使用传统方法")
                    return False
            else:
                logger.debug(f"AI应用失败: {result.get('changes_summary', 'Unknown reason')}")
                return False
                
        except ImportError:
            logger.debug("AI组件未可用，使用传统修复方法")
            return False
        except Exception as e:
            logger.debug(f"AI应用异常: {e}")
            return False

    def _detect_language(self, file_path: Path) -> str:
        """根据文件扩展名检测编程语言"""
        extension = file_path.suffix.lower()
        language_map = {
            '.py': 'python',
            '.java': 'java',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.cs': 'csharp',
            '.cpp': 'cpp',
            '.c': 'c',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.kt': 'kotlin',
            '.scala': 'scala'
        }
        return language_map.get(extension, 'unknown')
