"""
AI代码修复器
集成LangChain、SonarQube和GitLab，实现自动代码修复
"""

import time
from pathlib import Path
from typing import Dict, List

from ..clients.git_client import GitClient, GitLabClient
from ..clients.langchain_client import LangChainClient
from ..clients.sonarqube_client import SonarQubeClient
from sonar_tools.core.config import Config
from sonar_tools.core.models import SonarIssue
from ..service.sonar_service import SonarService

logger = Config.setup_logging(__name__)


class AICodeFixer:
    """AI代码自动修复器"""

    def __init__(self):
        """初始化AI代码修复器"""
        self.config = Config
        self._validate_config()
        self._initialize_clients()
        self.sonar_service = SonarService()

    def _validate_config(self):
        """验证配置"""
        self.config.validate_ai_config()
        self.config.validate_gitlab_config()

    def _initialize_clients(self):
        """初始化客户端"""
        try:
            # 初始化SonarQube客户端
            self.sonar_client = SonarQubeClient(
                self.config.SONARQUBE_URL, self.config.SONARQUBE_TOKEN
            )

            # 初始化Git相关客户端
            self.git_client = GitClient()

            # 创建GitLab MR管理器
            self.gitlab_client = GitLabClient()

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

    def _group_issues_by_project(
        self, issues: List[SonarIssue]
    ) -> Dict[str, List[SonarIssue]]:
        """按项目分组问题"""
        issues_by_project = {}

        for issue in issues:
            project_name = issue.project
            if project_name not in issues_by_project:
                issues_by_project[project_name] = []
            issues_by_project[project_name].append(issue)

        return issues_by_project

    def _process_project_issues(
        self, project_name: str, issues: List[SonarIssue]
    ) -> bool:
        """处理单个项目的问题"""
        try:
            logger.info(f"开始处理项目 {project_name} 的问题，共 {len(issues)} 个")

            # 准备Git仓库
            (
                success,
                repo_path,
                repo_info,
            ) = self.git_client.prepare_repository_for_project(project_name)
            if not success or not repo_path or not repo_info:
                logger.error(f"准备Git仓库失败: {project_name}")
                return False

            # 处理每个问题，为每个问题创建独立的MR
            successful_fixes = 0
            for issue in issues:
                # 先检查问题是否需要修复
                fix_check_result = self.sonar_service.is_issue_need_fix(issue.key)

                if not fix_check_result.get("need_fix", True):
                    logger.info(
                        f"跳过问题 {issue.key}: {fix_check_result.get('reason', '无需修复')}"
                    )
                    continue

                logger.info(
                    f"确认需要修复问题 {issue.key}: {fix_check_result.get('reason', '需要修复')}"
                )

                if self._fix_single_issue_with_mr(issue, repo_path, repo_info):
                    successful_fixes += 1
                else:
                    logger.error(f"修复问题失败: {issue.key}")
                    # 继续处理下一个问题，不中断整个流程

            if successful_fixes == 0:
                logger.warning("没有问题被成功修复")
                return False

            logger.info(f"成功修复并创建MR的问题数量: {successful_fixes}/{len(issues)}")
            return True

        except Exception as e:
            logger.error(f"处理项目问题失败: {e}")
            return False

    def _fix_single_issue_with_mr(
        self, issue: SonarIssue, repo_path: Path, repo_info: dict
    ) -> bool:
        """
        修复单个问题并为其创建独立的MR

        Args:
            issue: SonarQube问题
            repo_path: 仓库路径
            repo_info: 仓库信息

        Returns:
            修复和MR创建是否成功
        """
        branch_name = None
        try:
            logger.info(f"开始为问题创建独立修复分支: {issue.key}")

            # 为每个问题创建独立的分支
            branch_name = f"fix/sonar-{issue.key.replace(':', '-')}-{int(time.time())}"

            # 确保在主分支上
            if not self.git_client.checkout_branch(
                repo_path, repo_info["default_branch"]
            ):
                logger.error(f"切换到主分支失败: {repo_info['default_branch']}")
                return False

            # 拉取最新代码
            if not self.git_client.pull_latest(repo_path):
                logger.error("拉取最新代码失败")
                return False

            # 创建新分支
            if not self.git_client.create_branch(repo_path, branch_name):
                logger.error(f"创建分支失败: {branch_name}")
                return False

            # 修复问题
            if not self._fix_single_issue(issue, repo_path):
                logger.error(f"修复问题失败: {issue.key}")
                return False

            # 提交修复
            relative_path = issue.component.split(":")[-1]
            commit_message = self._generate_single_issue_commit_message(issue)

            if not self.git_client.commit_changes(
                repo_path, [relative_path], commit_message
            ):
                logger.error(f"提交修复失败: {issue.key}")
                return False

            # 推送分支
            if not self.git_client.push_branch(repo_path, branch_name):
                logger.error(f"推送分支失败: {branch_name}")
                return False

            # 创建MR
            mr_info = self._generate_single_issue_mr_info(issue)
            mr_result = self.gitlab_client.create_merge_request(
                project_id=repo_info["id"],
                source_branch=branch_name,
                target_branch=repo_info["default_branch"],
                title=mr_info["title"],
                description=mr_info["description"],
                labels=["SonarQube", "Critical-Fix", "AI-Generated", issue.rule],
            )

            # 判断MR创建结果
            if mr_result:
                logger.info(f"成功为问题 {issue.key} 创建MR: {mr_result['url']}")

                # 创建MR记录
                try:
                    mr_record_success = self.sonar_service.add_issue_mr_record(
                        sonar_issue_key=issue.key,
                        mr_url=mr_result["url"],
                        mr_iid=mr_result.get("iid"),
                        mr_title=mr_info["title"],
                        mr_description=mr_info["description"],
                        branch_name=branch_name,
                        source_branch=branch_name,
                        target_branch=repo_info["default_branch"],
                        mr_status="created",
                    )

                    if mr_record_success:
                        logger.info(
                            f"成功创建MR记录: {issue.key} -> {mr_result['url']}"
                        )
                    else:
                        logger.warning(f"MR记录创建失败，但MR已成功创建: {issue.key}")

                except Exception as record_error:
                    logger.error(f"创建MR记录时发生异常: {record_error}")
                    # 不影响主流程，MR已经创建成功

                return True
            else:
                logger.error(f"创建MR失败: {issue.key}")
                return False

        except Exception as e:
            logger.error(f"为问题 {issue.key} 创建独立MR失败: {e}")
            return False
        finally:
            # 无论成功还是失败，都清理本地分支
            if branch_name:
                try:
                    self._cleanup_branch(
                        repo_path, branch_name, repo_info["default_branch"]
                    )
                except Exception as cleanup_error:
                    logger.warning(f"分支清理过程中发生异常: {cleanup_error}")
                    # 不影响主流程的返回结果

    def _cleanup_branch(
        self, repo_path: Path, branch_name: str, default_branch: str
    ) -> bool:
        """
        清理本地分支

        Args:
            repo_path: 仓库路径
            branch_name: 要清理的分支名称
            default_branch: 默认分支名称

        Returns:
            清理是否成功
        """
        try:
            logger.info(f"开始清理本地分支: {branch_name}")

            # 切换到默认分支
            if not self.git_client.checkout_branch(repo_path, default_branch):
                logger.warning(f"切换到默认分支失败: {default_branch}")
                return False

            # 删除本地分支
            if self.git_client.delete_branch(repo_path, branch_name):
                logger.info(f"成功清理本地分支: {branch_name}")
                return True
            else:
                logger.warning(f"清理本地分支失败: {branch_name}")
                return False

        except Exception as e:
            logger.warning(f"清理分支异常: {e}")
            return False

    def _fix_single_issue(self, issue: SonarIssue, repo_path: Path) -> bool:
        """修复单个问题"""
        try:
            logger.info(f"开始修复问题: {issue.key}")

            # 准备问题数据
            relative_path = issue.component.split(":")[-1]  # 获取相对路径
            full_file_path = repo_path / relative_path

            issue_data = {
                "key": issue.key,
                "rule": issue.rule,
                "message": issue.message,
                "component": issue.component,
                "project": issue.project,
                "severity": issue.severity,
                "line": issue.line,
                "code_snippet": issue.code_snippet,
                "rule_info": issue.rule_info,
                "language": self._detect_language(full_file_path),
            }

            # 分析问题
            analysis_result = self.ai_client.analyze_code_issue(issue_data)
            if not analysis_result:
                logger.error(f"问题分析失败: {issue.key}")
                return False

            # 如果分析结果显示是函数内部问题，进行精确的函数范围分析
            scope_info = analysis_result.get("scope", {})
            function_scope = None

            if scope_info.get("is_function_internal") and full_file_path.exists():
                logger.info(f"检测到函数内部问题，进行精确范围分析: {issue.key}")
                function_scope = self.ai_client.analyze_function_scope(
                    str(full_file_path), issue.line, issue_data["language"]
                )

                if function_scope.get("success") and function_scope.get(
                    "function_found"
                ):
                    logger.info(
                        f"精确函数范围: {function_scope.get('function_name')} "
                        f"({function_scope.get('start_line')}-{function_scope.get('end_line')})"
                    )

                    # 将函数范围信息添加到问题数据中
                    issue_data["function_scope"] = function_scope
                else:
                    logger.warning(f"精确函数范围分析失败: {issue.key}")

            # 生成修复方案
            fix_result = self.ai_client.fix_code_issue(issue_data, analysis_result)
            if not fix_result or "fixed_code" not in fix_result:
                logger.error(f"生成修复方案失败: {issue.key}")
                return False

            # 验证修复
            fixed_code_data = fix_result.get("fixed_code")
            if not fixed_code_data:
                logger.error(f"修复方案中没有修复代码: {issue.key}")
                return False

            # 处理新旧代码格式的兼容性
            if isinstance(fixed_code_data, dict):
                # 新格式：拆分的代码结构
                validation_code = fixed_code_data.get(
                    "full_code"
                ) or fixed_code_data.get("function_code", "")
            else:
                # 旧格式：字符串
                validation_code = str(fixed_code_data)

            validation_result = self.ai_client.validate_fix(
                issue.code_snippet, validation_code, issue_data
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
                "fixed_code": fixed_code_data,  # 保持原始格式
                "code_snippet": issue.code_snippet,
                "line": issue.line,
                "language": issue_data.get("language", ""),
                "issue_key": issue.key,
                "rule": issue.rule,
                "function_scope": function_scope,  # 添加函数范围信息
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
            "mr_description": mr_description,
        }

    def _generate_single_issue_commit_message(self, issue: SonarIssue) -> str:
        """生成单个问题的提交信息"""
        commit_message = f"fix(sonar): 修复 {issue.rule} 问题\n\n"
        commit_message += f"- 问题描述: {issue.message}\n"
        commit_message += f"- 文件: {issue.component}\n"
        commit_message += f"- 行数: {issue.line}\n"
        commit_message += f"- 严重程度: {issue.severity}\n"
        commit_message += f"- Issue Key: {issue.key}\n\n"
        commit_message += "通过AI自动分析和修复生成"
        return commit_message

    def _generate_single_issue_mr_info(self, issue: SonarIssue) -> Dict[str, str]:
        """生成单个问题的MR信息"""

        # 获取规则的友好名称
        rule_name = (
            issue.rule_info.get("name", issue.rule) if issue.rule_info else issue.rule
        )

        title = f"fix(sonar): 修复 {issue.rule} - {rule_name}"

        description = f"""# SonarQube问题修复

## 问题概述
- **Issue Key**: `{issue.key}`
- **规则**: `{issue.rule}`
- **严重程度**: `{issue.severity}`
- **问题描述**: {issue.message}

## 修复详情
- **文件**: `{issue.component}`
- **行数**: {issue.line}
- **修复方式**: AI自动分析和修复

## 规则说明"""

        # 添加规则详细信息
        if issue.rule_info:
            description += f"""
- **规则名称**: {issue.rule_info.get('name', 'N/A')}
- **规则类型**: {issue.rule_info.get('type', 'N/A')}
- **标签**: {', '.join(issue.rule_info.get('tags', []))}

### 规则描述
{issue.rule_info.get('htmlDesc', '无详细描述')}
"""
        else:
            description += "\n- 无可用的规则详细信息"

        description += f"""

## 代码变更
此MR包含针对以下代码片段的修复：

```
{issue.code_snippet}
```

## 验证建议
1. 检查修复代码是否符合编码规范
2. 验证修复是否解决了SonarQube报告的问题
3. 确认没有引入新的问题或副作用
4. 运行相关的单元测试

---
*本MR由AI自动生成，请仔细审查修改内容。*
"""

        return {
            "title": title,
            "description": description,
        }

    def _commit_single_issue_fix(
        self, repo_path: Path, issue: SonarIssue, modified_file: str
    ) -> bool:
        """提交单个问题的修复"""
        try:
            commit_message = f"fix(sonar): 修复 {issue.rule} 问题\n\n"
            commit_message += f"- 文件: {issue.component}\n"
            commit_message += f"- 行数: {issue.line}\n"
            commit_message += f"- 问题: {issue.message}\n"
            commit_message += f"- Issue Key: {issue.key}"

            if not self.git_client.commit_changes(
                repo_path, [modified_file], commit_message
            ):
                logger.error(f"提交问题 {issue.key} 的修复失败")
                return False

            logger.info(f"成功提交问题 {issue.key} 的修复")
            return True

        except Exception as e:
            logger.error(f"提交单个问题修复失败 {issue.key}: {e}")
            return False

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

        if not self.git_client.commit_changes(
            local_path, modified_files, commit_message
        ):
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
        try:
            # 获取修复信息
            fixed_code_data = fix.get("fixed_code")
            if not fixed_code_data:
                logger.error("没有有效的修复代码")
                return False

            # 检查是否有精确的函数范围信息
            function_scope = fix.get("function_scope")
            if (
                function_scope
                and function_scope.get("success")
                and function_scope.get("function_found")
                and isinstance(fixed_code_data, dict)
                and fixed_code_data.get("function_code")
            ):
                # 使用精确函数替换策略
                if self._apply_function_replacement(file_path, content, fix):
                    logger.info("使用精确函数替换策略修复成功")
                    return True
                else:
                    logger.warning("精确函数替换失败，尝试其他策略")

            # 处理新旧代码格式
            if isinstance(fixed_code_data, dict):
                # 新格式：拆分的代码结构
                logger.info("检测到拆分格式的修复代码")
                imports_code = fixed_code_data.get("imports", "")
                function_code = fixed_code_data.get("function_code", "")
                # full_code = fixed_code_data.get("full_code", "")

                if imports_code:
                    logger.info(f"包含导入语句: {len(imports_code)} 字符")
                if function_code:
                    logger.info(f"包含函数代码: {len(function_code)} 字符")
            else:
                # 旧格式：字符串
                fixed_code_data = str(fixed_code_data).strip()
                if not fixed_code_data:
                    logger.error("修复代码为空")
                    return False

            # 尝试AI智能应用（备用方式）
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

    def _apply_function_replacement(
        self, file_path: Path, content: str, fix: dict
    ) -> bool:
        """使用精确函数范围进行直接替换"""
        try:
            function_scope = fix.get("function_scope")
            fixed_code_data = fix.get("fixed_code")

            if not function_scope or not isinstance(fixed_code_data, dict):
                return False

            start_line = function_scope.get("start_line")
            end_line = function_scope.get("end_line")
            function_code = fixed_code_data.get("function_code")
            imports_code = fixed_code_data.get("imports", "")

            if not start_line or not end_line or not function_code:
                logger.error("函数范围信息不完整")
                return False

            logger.info(f"使用精确函数替换: 第{start_line}-{end_line}行")

            # 按行分割文件内容
            lines = content.splitlines(keepends=True)

            # 验证行号范围
            if start_line < 1 or end_line > len(lines) or start_line > end_line:
                logger.error(
                    f"函数范围无效: {start_line}-{end_line} (文件共{len(lines)}行)"
                )
                return False

            # 构建新的文件内容
            new_lines = []

            # 保留函数前的内容
            new_lines.extend(lines[: start_line - 1])

            # 处理导入语句
            if imports_code.strip() and imports_code.strip() != "# 无需新增导入":
                # 找到合适的位置插入导入语句
                import_insert_line = self._find_import_insert_position(lines)
                if import_insert_line is not None and import_insert_line < start_line:
                    # 如果导入位置在函数之前，需要调整
                    logger.info(f"在第{import_insert_line+1}行添加导入语句")
                    # 这里需要更复杂的逻辑来处理导入，暂时跳过
                else:
                    logger.info("将导入语句添加到函数代码中")

            # 添加修复后的函数代码
            if not function_code.endswith("\n"):
                function_code += "\n"
            new_lines.append(function_code)

            # 保留函数后的内容
            new_lines.extend(lines[end_line:])

            # 生成新的文件内容
            new_content = "".join(new_lines)

            # 写回文件
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            logger.info(f"成功替换函数内容: {function_scope.get('function_name')}")
            return True

        except Exception as e:
            logger.error(f"精确函数替换失败: {e}")
            return False

    def _find_import_insert_position(self, lines: list) -> int:
        """找到插入导入语句的合适位置"""
        try:
            # 简单策略：找到最后一个import语句的位置
            last_import_line = -1

            for i, line in enumerate(lines):
                stripped = line.strip()
                if (
                    stripped.startswith("import ")
                    or stripped.startswith("from ")
                    or stripped.startswith("#")
                    and "import" in stripped
                ):
                    last_import_line = i
                elif stripped and not stripped.startswith("#"):
                    # 遇到非注释的实际代码，停止搜索
                    break

            if last_import_line >= 0:
                return last_import_line + 1
            else:
                # 如果没有找到导入语句，在文件开头插入
                # 跳过shebang和编码声明
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    if not (
                        stripped.startswith("#")
                        and (
                            "!" in stripped
                            or "coding" in stripped
                            or "encoding" in stripped
                        )
                    ):
                        return i
                return 0

        except Exception as e:
            logger.debug(f"查找导入位置失败: {e}")
            return None

    def _try_ai_application(self, file_path: Path, content: str, fix: dict) -> bool:
        """尝试使用AI智能应用修复"""
        try:
            # 检查是否启用AI应用
            from sonar_tools.core.config import Config

            if not getattr(Config, "AI_APPLY_FIXES", True):
                logger.debug("AI应用修复已禁用")
                return False

            fixed_code_data = fix.get("fixed_code")
            if not fixed_code_data:
                logger.error("没有修复代码数据")
                return False

            # 构造问题数据
            issue_data = {
                "component": str(file_path),
                "line": fix.get("line", 0),
                "language": fix.get("language", self._detect_language(file_path)),
                "message": fix.get("message", "SonarQube Critical issue"),
                "code_snippet": fix.get("code_snippet", ""),
                "key": fix.get("key", f"issue_{file_path.name}"),
            }

            # 使用AI应用修复
            result = self.ai_client.apply_code_fix(content, fixed_code_data, issue_data)

            if result.get("success") and result.get("modified_content"):
                confidence = result.get("confidence", 0)
                threshold = getattr(Config, "AI_APPLY_CONFIDENCE_THRESHOLD", 7)

                if confidence >= threshold:  # 使用配置的信心阈值
                    # 写回文件
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(result["modified_content"])

                    logger.info(
                        f"AI应用修复成功 - 策略: {result.get('strategy_used')}, 信心: {confidence}/10"
                    )
                    if result.get("warnings"):
                        logger.warning(f"AI应用警告: {', '.join(result['warnings'])}")

                    return True
                else:
                    logger.warning(
                        f"AI应用信心不足: {confidence}/10 < {threshold}，使用传统方法"
                    )
                    return False
            else:
                logger.debug(
                    f"AI应用失败: {result.get('changes_summary', 'Unknown reason')}"
                )
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
            ".py": "python",
            ".java": "java",
            ".js": "javascript",
            ".ts": "typescript",
            ".cs": "csharp",
            ".cpp": "cpp",
            ".c": "c",
            ".php": "php",
            ".rb": "ruby",
            ".go": "go",
            ".rs": "rust",
            ".kt": "kotlin",
            ".scala": "scala",
        }
        return language_map.get(extension, "unknown")
