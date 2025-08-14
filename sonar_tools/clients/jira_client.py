import re
from typing import Any, Dict, List, Optional

from jira import JIRA

from sonar_tools.core.config import Config
from sonar_tools.core.models import JiraTask, SonarIssue
from sonar_tools.service.sonar_service import SonarService

logger = Config.setup_logging(__name__)


class JiraClient:
    """Jira API客户端"""

    def __init__(self, server: str, token: str):
        self.server = server
        self.sonar_service = SonarService()
        try:
            self.jira = JIRA(
                server=server,
                token_auth=token,
            )
            logger.info("Jira客户端初始化成功")
        except Exception as e:
            logger.error(f"Jira客户端初始化失败: {e}")
            raise

    def create_issue(self, task: JiraTask) -> Optional[str]:
        """创建Jira问题"""
        issue_dict = {
            "project": {"key": task.project_key},
            "summary": task.summary,
            "description": task.description,
            "issuetype": {"name": task.issue_type},
            "priority": {"name": task.priority},
        }

        # 如果有标签，直接在创建时添加
        if task.labels:
            # 验证和清理标签
            valid_labels = self._validate_and_clean_labels(task.labels)
            if valid_labels:
                issue_dict["labels"] = valid_labels

        try:
            # 创建问题
            new_issue = self.jira.create_issue(fields=issue_dict)

            # 如果创建时标签添加失败，尝试后续添加
            if task.labels and not hasattr(new_issue.fields, "labels"):
                try:
                    self._add_labels_to_issue(new_issue, task.labels)
                except Exception as label_error:
                    logger.warning(f"后续添加标签失败: {label_error}")

            logger.info(f"成功创建Jira任务: {new_issue.key} - {task.summary}")
            return new_issue.key

        except Exception as e:
            logger.error(f"创建Jira任务失败: {e}")
            logger.error(f"任务信息: {task.summary}")
            return None

    def create_issues_from_sonar(
        self, sonar_issues: List[SonarIssue], project_key: str
    ) -> List[str]:
        """从SonarQube问题批量创建Jira任务"""
        created_issues = []
        max_tasks = Config.JIRA_MAX_TASKS_PER_RUN

        # 检查是否设置了任务限制
        if max_tasks > 0:
            logger.info(f"设置了单次创建任务限制: {max_tasks} 个任务")
        else:
            logger.info("未设置任务创建限制")

        for i, sonar_issue in enumerate(sonar_issues, 1):
            # 检查是否达到任务创建限制
            if max_tasks > 0 and len(created_issues) >= max_tasks:
                logger.warning(f"已达到单次创建任务限制 ({max_tasks} 个)，停止创建更多任务")
                logger.info(f"剩余 {len(sonar_issues) - i + 1} 个问题将在下次运行时处理")
                break

            logger.info(f"创建第 {i}/{len(sonar_issues)} 个Jira任务...")

            # 检查是否已存在相同的任务（优先从SQLite缓存查询）
            if self._issue_exists(sonar_issue, project_key):
                logger.info(f"跳过已存在的任务: {sonar_issue.key}")
                continue

            # 创建Jira任务
            jira_task = JiraTask.from_sonar_issue(sonar_issue, project_key)
            issue_key = self.create_issue(jira_task)

            if issue_key:
                created_issues.append(issue_key)

                # 将新创建的任务记录到SQLite缓存
                if self.sonar_service:
                    try:
                        self.sonar_service.create_sonar_issue_record(
                            sonar_issue=sonar_issue,
                            jira_task_key=issue_key,
                            jira_project_key=project_key,
                        )
                        logger.debug(f"已记录新创建任务到缓存: {sonar_issue.key} -> {issue_key}")
                    except Exception as e:
                        logger.warning(f"记录新创建任务到缓存失败: {e}")

        logger.info(f"总共创建了 {len(created_issues)} 个Jira任务")
        return created_issues

    def _add_labels_to_issue(self, issue, labels: List[str]):
        """为issue添加标签的辅助方法"""
        try:
            # 过滤并清理标签
            valid_labels = [
                label.strip().replace(" ", "-")
                for label in labels
                if label and label.strip()
            ]

            if not valid_labels:
                return

            # 方法1: 直接更新
            try:
                issue.update(fields={"labels": valid_labels})
                logger.debug(f"成功添加标签: {valid_labels}")
                return
            except Exception as e1:
                logger.debug(f"方法1失败: {e1}")

            # 方法2: 获取现有标签后合并
            try:
                fresh_issue = self.jira.issue(issue.key)
                current_labels = []
                if hasattr(fresh_issue.fields, "labels") and fresh_issue.fields.labels:
                    current_labels = [
                        label.name if hasattr(label, "name") else str(label)
                        for label in fresh_issue.fields.labels
                    ]

                # 合并标签，去重
                all_labels = list(set(current_labels + valid_labels))
                fresh_issue.update(fields={"labels": all_labels})
                logger.debug(f"成功合并添加标签: {all_labels}")
                return
            except Exception as e2:
                logger.debug(f"方法2失败: {e2}")

            # 方法3: 使用REST API直接更新
            try:
                update_data = {"fields": {"labels": valid_labels}}
                self.jira._session.put(
                    f"{self.jira._options['server']}/rest/api/2/issue/{issue.key}",
                    json=update_data,
                )
                logger.debug(f"通过REST API成功添加标签: {valid_labels}")
            except Exception as e3:
                logger.warning(f"所有添加标签方法都失败: {e3}")

        except Exception as e:
            logger.error(f"添加标签时发生未预期错误: {e}")

    def _validate_and_clean_labels(self, labels: List[str]) -> List[str]:
        """验证和清理标签"""
        if not labels:
            return []

        valid_labels = []
        for label in labels:
            if not label or not isinstance(label, str):
                continue

            # 清理标签：去空格、转小写、替换特殊字符
            cleaned_label = label.strip().lower()

            # 替换空格和特殊字符为连字符
            cleaned_label = re.sub(r"[^\w\-]", "-", cleaned_label)

            # 移除多余的连字符
            cleaned_label = re.sub(r"-+", "-", cleaned_label)

            # 移除开头和结尾的连字符
            cleaned_label = cleaned_label.strip("-")

            # 检查长度限制（Jira标签通常有长度限制）
            if len(cleaned_label) > 50:
                cleaned_label = cleaned_label[:50]

            # 确保不为空且不重复
            if cleaned_label and cleaned_label not in valid_labels:
                valid_labels.append(cleaned_label)

        return valid_labels[:10]  # 限制标签数量，避免过多

    def _issue_exists(self, sonar_issue: SonarIssue, project_key: str) -> bool:
        """检查是否已存在相同的Jira任务（优先从SQLite缓存查询）"""
        try:
            # 1. 首先从SQLite缓存中查询任务是否已创建
            if self.sonar_service:
                logger.debug(f"从缓存中查询任务 {sonar_issue.key} 是否已创建...")
                if self.sonar_service.is_issue_jira_task_created(sonar_issue.key):
                    logger.info(f"从缓存中发现任务已存在: {sonar_issue.key}")
                    return True
                logger.debug(f"缓存中未找到任务 {sonar_issue.key}，将查询Jira API...")

            # 2. 如果缓存中没有记录，从Jira API查询
            logger.debug(f"向Jira API查询任务 {sonar_issue.key} 是否存在...")
            # 在description中查询SonarQube问题的key，使用精确匹配
            # 假设description中包含类似 "SonarQube问题: ISSUE-KEY" 的格式
            jql = f'project = {project_key} AND (description ~ "{sonar_issue.key}" OR summary ~ "{sonar_issue.key}")'
            issues = self.jira.search_issues(jql, maxResults=5)

            # 进一步验证找到的任务是否真的对应这个SonarQube问题
            task_exists = False
            existing_task = None

            for issue in issues:
                # 检查description或summary中是否包含完整的SonarQube问题key
                description = getattr(issue.fields, "description", "") or ""
                summary = getattr(issue.fields, "summary", "") or ""

                if sonar_issue.key in description or sonar_issue.key in summary:
                    task_exists = True
                    existing_task = issue
                    logger.debug(f"在任务 {issue.key} 中找到SonarQube问题 {sonar_issue.key}")
                    break

            if task_exists:
                logger.info(f"Jira API查询发现任务已存在: {sonar_issue.key}")

                # 如果从Jira API发现任务存在，但缓存中没有记录，补充记录到缓存
                if self.sonar_service and existing_task:
                    try:
                        self.sonar_service.create_sonar_issue_record(
                            sonar_issue=sonar_issue,
                            jira_task_key=existing_task.key,
                            jira_project_key=project_key,
                        )
                        logger.debug(
                            f"已补充任务记录到缓存: {sonar_issue.key} -> {existing_task.key}"
                        )
                    except Exception as e:
                        logger.debug(f"补充任务记录到缓存失败: {e}")
            else:
                logger.debug(f"Jira API查询确认任务不存在: {sonar_issue.key}")

            return task_exists

        except Exception as e:
            logger.warning(f"检查任务是否存在时出错: {e}")
            return False

    def test_connection(self) -> bool:
        """测试Jira连接"""
        try:
            # 尝试获取当前用户信息
            current_user = self.jira.current_user()
            logger.info(f"Jira连接测试成功，当前用户: {current_user}")
            return True
        except Exception as e:
            logger.error(f"Jira连接测试失败: {e}")
            logger.info("Some long log message that exceeds 88 characters ...")

    def get_project_info(self, project_key: str) -> Optional[Dict[str, Any]]:
        """获取项目信息"""
        try:
            project = self.jira.project(project_key)
            return {
                "key": project.key,
                "name": project.name,
                "lead": project.lead.displayName if project.lead else None,
                "description": getattr(project, "description", ""),
            }
        except Exception as e:
            logger.error(f"获取Jira项目信息失败: {e}")
            return None

    def get_all_projects(self) -> List[Dict[str, Any]]:
        """获取所有Jira项目"""
        try:
            projects = self.jira.projects()
            project_list = []

            for project in projects:
                project_list.append(
                    {
                        "key": project.key,
                        "name": project.name,
                        "id": project.id,
                        "lead": (
                            project.lead.displayName
                            if hasattr(project, "lead") and project.lead
                            else None
                        ),
                    }
                )

            logger.info(f"获取到 {len(project_list)} 个Jira项目")
            return project_list

        except Exception as e:
            logger.error(f"获取Jira项目列表失败: {e}")
            return []

    def create_project(
        self, key: str, name: str, project_type: str = "software", lead: str = None
    ) -> bool:
        """
        创建Jira项目

        Args:
            key: 项目key
            name: 项目名称
            project_type: 项目类型，默认为'software'
            lead: 项目负责人，默认为当前用户

        Returns:
            bool: 创建是否成功
        """
        try:
            # 检查项目是否已存在
            try:
                existing_project = self.jira.project(key)
                if existing_project:
                    logger.info(f"项目 {key} 已存在，跳过创建")
                    return True
            except Exception:
                # 项目不存在，继续创建
                pass

            # 如果没有指定负责人，使用当前用户
            if not lead:
                try:
                    current_user = self.jira.current_user()
                    lead = current_user
                except Exception as e:
                    logger.warning(f"无法获取当前用户作为项目负责人: {e}")
                    # 尝试使用配置中的用户名
                    lead = Config.JIRA_PROJECT_LEAD

            logger.info(f"使用标准软件项目类型创建项目: {key}")

            # 尝试使用JIRA库的create_project方法（简化参数）
            self.jira.create_project(key=key, name=name, assignee=lead)
            logger.info(f"成功创建Jira项目: {key} - {name}")
            return True

        except Exception as e:
            logger.error(f"创建Jira项目失败: {e}")
            return False

    def project_exists(self, project_key: str) -> bool:
        """检查项目是否存在"""
        try:
            self.jira.project(project_key)
            return True
        except Exception:
            return False
