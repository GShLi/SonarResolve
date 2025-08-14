#!/usr/bin/env python3
"""
MR状态同步服务
定时从GitLab同步MR状态并更新数据库
"""

from datetime import datetime
from typing import Any, Dict, Optional

from ..clients.git_client import GitLabClient
from ..core.config import Config
from ..utils.project_db import ProjectStatusDB

logger = Config.setup_logging(__name__)


class MRStatusSyncService:
    """MR状态同步服务"""

    def __init__(self, project_db: ProjectStatusDB = None):
        """
        初始化MR状态同步服务

        Args:
            project_db: 项目数据库实例，如果不提供将自动创建
        """
        self.project_db = project_db if project_db else ProjectStatusDB()

        try:
            self.gitlab_client = GitLabClient()
        except Exception as e:
            logger.error(f"GitLab客户端初始化失败: {e}")
            self.gitlab_client = None

    def sync_mr_status(self, days_back: int = None) -> Dict[str, Any]:
        """
        同步MR状态

        Args:
            days_back: 同步最近几天的MR，默认使用配置值

        Returns:
            同步结果统计
        """
        if not self.gitlab_client:
            logger.error("GitLab客户端未初始化，无法同步MR状态")
            return {
                "success": False,
                "error": "GitLab客户端未初始化",
                "total_mrs": 0,
                "updated_mrs": 0,
                "failed_mrs": 0,
            }

        if days_back is None:
            days_back = Config.MR_SYNC_DAYS_BACK

        sync_start = datetime.now()
        logger.info(f"开始同步MR状态，查询最近 {days_back} 天的MR")

        try:
            # 获取需要同步的MR记录
            pending_mrs = self.project_db.get_pending_mr_records(days_back)

            if not pending_mrs:
                logger.info("没有需要同步的MR记录")
                return {
                    "success": True,
                    "total_mrs": 0,
                    "updated_mrs": 0,
                    "failed_mrs": 0,
                    "sync_duration": datetime.now() - sync_start,
                }

            logger.info(f"找到 {len(pending_mrs)} 个待同步的MR")

            # 准备MR数据列表（包含项目ID和MR ID）
            mr_data_list = []
            for mr in pending_mrs:
                mr_data_list.append(
                    {
                        "mr_url": mr["mr_url"],
                        "git_project_id": mr.get("git_project_id"),
                        "mr_id": mr.get("mr_id"),
                    }
                )

            # 批量获取MR状态（优先使用项目ID和MR ID）
            mr_status_data = self.gitlab_client.batch_get_merge_request_status_by_ids(
                mr_data_list
            )

            # 准备更新数据
            mr_updates = []
            updated_count = 0
            failed_count = 0

            for mr in pending_mrs:
                mr_url = mr["mr_url"]
                current_status = mr["mr_status"]

                if mr_url not in mr_status_data:
                    logger.warning(f"无法获取MR状态: {mr_url}")
                    failed_count += 1
                    continue

                gitlab_mr_data = mr_status_data[mr_url]
                gitlab_state = gitlab_mr_data.get("state", "").lower()

                # 映射GitLab状态到我们的状态
                new_status = self._map_gitlab_state_to_our_status(gitlab_state)

                if new_status and new_status != current_status:
                    update_data = {
                        "mr_url": mr_url,
                        "mr_status": new_status,
                        "rejection_reason": None,
                    }

                    # 如果是closed状态，尝试判断是否被拒绝
                    if new_status == "closed":
                        merge_status = gitlab_mr_data.get("merge_status")
                        if merge_status and merge_status.lower() != "can_be_merged":
                            update_data["rejection_reason"] = (
                                f"MR被关闭，合并状态: {merge_status}"
                            )

                    mr_updates.append(update_data)
                    updated_count += 1

                    logger.debug(
                        f"MR状态变更: {mr_url} {current_status} -> {new_status}"
                    )

            # 批量更新数据库
            if mr_updates:
                actual_updated = self.project_db.batch_update_mr_status(mr_updates)
                logger.info(
                    f"数据库更新完成，预期更新 {len(mr_updates)} 条，实际更新 {actual_updated} 条"
                )
            else:
                logger.info("没有MR状态需要更新")

            sync_duration = datetime.now() - sync_start

            result = {
                "success": True,
                "total_mrs": len(pending_mrs),
                "updated_mrs": len(mr_updates),
                "failed_mrs": failed_count,
                "sync_duration": sync_duration,
                "details": {
                    "checked_mr_count": len(pending_mrs),
                    "gitlab_response_count": len(mr_status_data),
                    "database_updates": len(mr_updates),
                },
            }

            logger.info(f"MR状态同步完成: {result}")
            return result

        except Exception as e:
            logger.error(f"MR状态同步失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "total_mrs": 0,
                "updated_mrs": 0,
                "failed_mrs": 0,
                "sync_duration": datetime.now() - sync_start,
            }

    def _map_gitlab_state_to_our_status(self, gitlab_state: str) -> Optional[str]:
        """
        映射GitLab状态到我们的状态

        Args:
            gitlab_state: GitLab的MR状态

        Returns:
            我们系统中的状态，如果不需要更新返回None
        """
        state_mapping = {
            "opened": "created",  # GitLab的opened对应我们的created
            "merged": "merged",  # 已合并
            "closed": "closed",  # 已关闭（可能被拒绝）
        }

        return state_mapping.get(gitlab_state.lower())

    def get_sync_statistics(self) -> Dict[str, Any]:
        """
        获取同步相关的统计信息

        Returns:
            统计信息
        """
        try:
            # 获取最近的MR记录统计
            pending_mrs = self.project_db.get_pending_mr_records(
                Config.MR_SYNC_DAYS_BACK
            )

            # 按状态分组统计
            status_stats = {}
            for mr in pending_mrs:
                status = mr["mr_status"]
                status_stats[status] = status_stats.get(status, 0) + 1

            return {
                "total_pending_mrs": len(pending_mrs),
                "status_distribution": status_stats,
                "sync_config": {
                    "enabled": Config.MR_SYNC_ENABLED,
                    "cron_expression": Config.MR_SYNC_CRON_EXPRESSION,
                    "days_back": Config.MR_SYNC_DAYS_BACK,
                },
                "gitlab_client_available": self.gitlab_client is not None,
            }

        except Exception as e:
            logger.error(f"获取同步统计失败: {e}")
            return {"error": str(e)}

    def test_gitlab_connection(self) -> bool:
        """
        测试GitLab连接

        Returns:
            连接是否成功
        """
        if not self.gitlab_client:
            return False

        try:
            # 尝试获取当前用户信息来测试连接
            self.gitlab_client.gitlab_client.auth()
            current_user = self.gitlab_client.gitlab_client.user
            logger.info(f"GitLab连接测试成功，当前用户: {current_user.name}")
            return True
        except Exception as e:
            logger.error(f"GitLab连接测试失败: {e}")
            return False
