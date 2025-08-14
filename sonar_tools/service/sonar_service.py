#!/usr/bin/env python3
"""
SonarQube业务服务
处理与SonarQube相关的业务逻辑
"""

from typing import Any, Dict, List, Optional

from sonar_tools.core.config import Config
from sonar_tools.core.models import SonarIssue
from sonar_tools.utils.project_db import ProjectStatusDB

logger = Config.setup_logging(__name__)


class SonarService:
    """SonarQube业务服务类"""

    def __init__(self, project_db: ProjectStatusDB = None):
        """
        初始化SonarQube服务

        Args:
            project_db: 项目数据库实例，如果不提供将自动创建
        """
        self.project_db = project_db if project_db else ProjectStatusDB()

    def create_sonar_issue_record(
        self,
        sonar_issue: SonarIssue,
        jira_task_key: str,
        jira_project_key: str,
    ) -> bool:
        """
        创建SonarQube问题记录

        Args:
            sonar_issue: SonarQube问题对象
            jira_task_key: Jira任务Key
            jira_project_key: Jira项目Key

        Returns:
            bool: 创建成功返回True，失败返回False
        """
        try:
            existing_record = self.project_db.get_task_basic_info(sonar_issue.key)

            if existing_record:
                # 如果已有记录但缺少Jira信息，则更新
                if not existing_record.get("jira_task_key") and not existing_record.get(
                    "jira_project_key"
                ):
                    success = self.project_db.update_task_jira_info(
                        sonar_issue_key=sonar_issue.key,
                        jira_task_key=jira_task_key,
                        jira_project_key=jira_project_key,
                    )
                    if success:
                        logger.info(
                            f"更新SonarQube问题Jira信息: {sonar_issue.key} -> {jira_task_key}"
                        )
                        return True
                else:
                    # 已有完整记录，直接返回成功
                    logger.info(
                        f"SonarQube问题记录已存在: {sonar_issue.key} -> {existing_record.get('jira_task_key')}"
                    )
                    return True
            # 如果没有记录或更新失败，创建新记录
            self.project_db.record_created_task(
                sonar_issue_key=sonar_issue.key,
                jira_task_key=jira_task_key,
                jira_project_key=jira_project_key,
                sonar_project_key=sonar_issue.project,
            )

            logger.info(f"创建SonarQube问题记录: {sonar_issue.key} -> {jira_task_key}")
            return True

        except Exception as e:
            logger.error(f"创建SonarQube问题记录失败: {e}")
            return False

    def is_issue_jira_task_created(self, sonar_issue_key: str) -> bool:
        """
        检查SonarQube问题是否已创建Jira任务

        Args:
            sonar_issue_key: SonarQube问题Key

        Returns:
            bool: 已创建返回True，未创建返回False
        """
        try:
            return self.project_db.is_task_created(sonar_issue_key)

        except Exception as e:
            logger.error(f"检查Jira任务创建状态失败: {e}")
            return False

    def add_issue_mr_record(
        self,
        sonar_issue_key: str,
        mr_url: str,
        mr_id: str = None,
        git_project_id: str = None,
        mr_title: str = None,
        mr_description: str = None,
        branch_name: str = None,
        source_branch: str = None,
        target_branch: str = None,
        mr_status: str = "created",
    ) -> bool:
        """
        添加问题的MR提交记录

        Args:
            sonar_issue_key: SonarQube问题Key
            mr_url: MR地址
            mr_id: MR的内部ID
            git_project_id: Git项目ID
            mr_title: MR标题
            mr_description: MR描述
            branch_name: 分支名称
            source_branch: 源分支
            target_branch: 目标分支
            mr_status: MR状态 (created, merged, closed, rejected)

        Returns:
            bool: 添加成功返回True，失败返回False
        """
        try:
            # 检查是否有create_mr_record方法
            if hasattr(self.project_db, "create_mr_record"):
                success = self.project_db.create_mr_record(
                    sonar_issue_key=sonar_issue_key,
                    mr_url=mr_url,
                    mr_id=mr_id,
                    git_project_id=git_project_id,
                    mr_title=mr_title,
                    mr_description=mr_description,
                    branch_name=branch_name,
                    source_branch=source_branch,
                    target_branch=target_branch,
                    mr_status=mr_status,
                )

                if success and hasattr(self.project_db, "update_mr_status"):
                    # 同时更新主表中的MR状态
                    self.project_db.update_mr_status(
                        sonar_issue_key=sonar_issue_key,
                        mr_status=mr_status,
                        mr_url=mr_url,
                    )

                logger.info(f"添加MR记录: {sonar_issue_key} -> {mr_url}")
                return success
            else:
                logger.warning("数据库不支持MR记录功能")
                return False

        except Exception as e:
            logger.error(f"添加MR记录失败: {e}")
            return False

    def is_issue_need_fix(self, sonar_issue_key: str) -> Dict[str, Any]:
        """
        检查问题是否需要修复

        判断逻辑：有且仅有如下情况，issue需要被修复
        1. 未找到 issue 记录
        2. 找到 issue 记录但未找到 mr 记录
        3. 找到 issue 记录也找到 mr 记录，但 mr 被驳回

        Args:
            sonar_issue_key: SonarQube问题Key

        Returns:
            Dict: 包含需要修复的判断结果和相关信息
            {
                "need_fix": bool,  # 是否需要修复
                "reason": str,     # 判断原因
                "current_status": Dict,  # 当前状态信息
                "latest_mr": Dict,  # 最新MR信息
                "action_required": str  # 建议的操作
            }
        """
        try:
            # 情况1：检查问题是否已创建记录
            if not self.project_db.is_task_created(sonar_issue_key):
                # 先创建一条记录，jira字段设为null
                try:
                    self.project_db.record_created_task(
                        sonar_issue_key=sonar_issue_key,
                        jira_task_key=None,
                        jira_project_key=None,
                        sonar_project_key=None,
                    )
                    logger.info(f"为问题创建初始记录: {sonar_issue_key}")
                except Exception as e:
                    logger.error(f"创建初始记录失败: {e}")

                return {
                    "need_fix": True,
                    "reason": "未找到 issue 记录，已创建初始记录",
                    "current_status": None,
                    "latest_mr": None,
                    "action_required": "创建问题记录并开始修复流程",
                }

            # 已找到 issue 记录，获取详细状态
            issue_status = None
            latest_mr = None

            if hasattr(self.project_db, "get_latest_mr_record"):
                latest_mr = self.project_db.get_latest_mr_record(sonar_issue_key)

            # 情况2：找到 issue 记录但未找到 mr 记录
            if not latest_mr:
                return {
                    "need_fix": True,
                    "reason": "找到 issue 记录但未找到 mr 记录",
                    "current_status": issue_status or {"has_task": True},
                    "latest_mr": None,
                    "action_required": "开始修复并创建MR",
                }

            # 情况3：找到 issue 记录也找到 mr 记录，检查是否被驳回
            if latest_mr.get("mr_status") == "rejected":
                return {
                    "need_fix": True,
                    "reason": f"找到 issue 记录也找到 mr 记录，但 mr 被驳回: {latest_mr.get('rejection_reason', '未知原因')}",
                    "current_status": issue_status or {"has_task": True},
                    "latest_mr": latest_mr,
                    "action_required": "根据驳回原因重新修复并提交新MR",
                }

            # 其他情况：已有记录且MR未被驳回，无需修复
            mr_status = latest_mr.get("mr_status", "unknown")
            return {
                "need_fix": False,
                "reason": f"找到 issue 记录和 mr 记录，MR状态为: {mr_status}",
                "current_status": issue_status or {"has_task": True},
                "latest_mr": latest_mr,
                "action_required": (
                    "无需操作"
                    if mr_status in ["merged", "closed"]
                    else "等待MR处理结果"
                ),
            }

        except Exception as e:
            logger.error(f"检查问题是否需要修复失败: {e}")
            return {
                "need_fix": True,
                "reason": f"检查过程中发生错误: {e}",
                "current_status": None,
                "latest_mr": None,
                "action_required": "检查系统状态并重试",
            }

    def update_mr_status(
        self, sonar_issue_key: str, mr_status: str, mr_url: str = None
    ) -> bool:
        """
        更新问题的MR状态

        Args:
            sonar_issue_key: SonarQube问题Key
            mr_status: MR状态 (pending, created, merged, closed, rejected)
            mr_url: MR地址

        Returns:
            bool: 更新成功返回True，失败返回False
        """
        try:
            if hasattr(self.project_db, "update_mr_status"):
                self.project_db.update_mr_status(sonar_issue_key, mr_status, mr_url)
                logger.info(f"更新MR状态: {sonar_issue_key} -> {mr_status}")
                return True
            else:
                logger.warning("数据库不支持MR状态更新功能")
                return False

        except Exception as e:
            logger.error(f"更新MR状态失败: {e}")
            return False

    def update_mr_record_status(
        self, mr_url: str, mr_status: str, rejection_reason: str = None
    ) -> bool:
        """
        更新MR记录状态

        Args:
            mr_url: MR地址
            mr_status: 新的MR状态 (created, merged, closed, rejected)
            rejection_reason: 如果被驳回，记录驳回原因

        Returns:
            bool: 更新成功返回True，失败返回False
        """
        try:
            if hasattr(self.project_db, "update_mr_record_status"):
                success = self.project_db.update_mr_record_status(
                    mr_url, mr_status, rejection_reason
                )

                if success:
                    logger.info(f"更新MR记录状态: {mr_url} -> {mr_status}")
                    if rejection_reason:
                        logger.info(f"驳回原因: {rejection_reason}")

                return success
            else:
                logger.warning("数据库不支持MR记录状态更新功能")
                return False

        except Exception as e:
            logger.error(f"更新MR记录状态失败: {e}")
            return False

    def get_issue_status(self, sonar_issue_key: str) -> Optional[Dict[str, Any]]:
        """
        获取问题状态信息

        Args:
            sonar_issue_key: SonarQube问题Key

        Returns:
            Optional[Dict]: 问题状态信息，如果不存在返回None
        """
        try:
            if hasattr(self.project_db, "get_issue_status"):
                return self.project_db.get_issue_status(sonar_issue_key)
            else:
                # 基本功能：只能检查是否已创建任务
                if self.project_db.is_task_created(sonar_issue_key):
                    return {"has_task": True}
                return None

        except Exception as e:
            logger.error(f"获取问题状态失败: {e}")
            return None

    def get_mr_records(self, sonar_issue_key: str) -> List[Dict[str, Any]]:
        """
        获取问题的所有MR记录

        Args:
            sonar_issue_key: SonarQube问题Key

        Returns:
            List[Dict]: MR记录列表
        """
        try:
            if hasattr(self.project_db, "get_mr_records"):
                return self.project_db.get_mr_records(sonar_issue_key)
            else:
                logger.warning("数据库不支持MR记录查询功能")
                return []

        except Exception as e:
            logger.error(f"获取MR记录失败: {e}")
            return []

    def get_rejected_mrs(self) -> List[Dict[str, Any]]:
        """
        获取所有被驳回的MR记录

        Returns:
            List[Dict]: 被驳回的MR记录列表
        """
        try:
            if hasattr(self.project_db, "get_rejected_mrs"):
                return self.project_db.get_rejected_mrs()
            else:
                logger.warning("数据库不支持被驳回MR查询功能")
                return []

        except Exception as e:
            logger.error(f"获取被驳回MR列表失败: {e}")
            return []

    def get_issues_need_refix(self) -> List[Dict[str, Any]]:
        """
        获取需要重新修复的问题列表（被驳回的MR对应的问题）

        Returns:
            List[Dict]: 需要重新修复的问题信息列表
        """
        try:
            rejected_mrs = self.get_rejected_mrs()
            issues_need_refix = []

            for mr in rejected_mrs:
                sonar_issue_key = mr.get("sonar_issue_key")
                if sonar_issue_key:
                    # 检查是否是最新被驳回的MR
                    latest_mr = self.project_db.get_latest_mr_record(sonar_issue_key)
                    if (
                        latest_mr
                        and latest_mr.get("mr_status") == "rejected"
                        and latest_mr.get("mr_url") == mr.get("mr_url")
                    ):
                        issue_info = {
                            "sonar_issue_key": sonar_issue_key,
                            "sonar_project_key": mr.get("sonar_project_key"),
                            "jira_task_key": mr.get("jira_task_key"),
                            "latest_rejected_mr": latest_mr,
                            "rejection_reason": latest_mr.get("rejection_reason"),
                            "rejected_time": latest_mr.get("updated_time"),
                        }
                        issues_need_refix.append(issue_info)

            return issues_need_refix

        except Exception as e:
            logger.error(f"获取需要重新修复的问题列表失败: {e}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取SonarQube问题处理统计信息

        Returns:
            Dict: 统计信息
        """
        try:
            task_stats = self.project_db.get_task_statistics()
            rejected_mrs = self.get_rejected_mrs()
            issues_need_refix = self.get_issues_need_refix()

            # 基本统计信息
            result = {
                "task_statistics": task_stats,
                "rejected_mr_count": len(rejected_mrs),
                "issues_need_refix_count": len(issues_need_refix),
                "summary": {
                    "total_issues": task_stats.get("total_tasks", 0),
                },
            }

            # 如果支持扩展状态，添加详细统计
            if "fix_status_stats" in task_stats:
                fix_stats = task_stats.get("fix_status_stats", [])
                result["summary"].update(
                    {
                        "pending_fix": sum(
                            s.get("count", 0)
                            for s in fix_stats
                            if s.get("status") == "pending"
                        ),
                        "in_progress": sum(
                            s.get("count", 0)
                            for s in fix_stats
                            if s.get("status") == "in_progress"
                        ),
                        "fixed": sum(
                            s.get("count", 0)
                            for s in fix_stats
                            if s.get("status") == "fixed"
                        ),
                        "failed": sum(
                            s.get("count", 0)
                            for s in fix_stats
                            if s.get("status") == "failed"
                        ),
                    }
                )
            else:
                # 基本模式：无法提供详细状态统计
                result["summary"].update(
                    {
                        "pending_fix": "N/A",
                        "in_progress": "N/A",
                        "fixed": "N/A",
                        "failed": "N/A",
                    }
                )

            return result

        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
