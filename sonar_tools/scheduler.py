#!/usr/bin/env python3
"""
定时任务调度器
使用cron表达式定时执行SonarQube到Jira的任务创建
"""

import signal
import sys
import threading
import time
from datetime import datetime
from typing import Any, Dict, Optional

try:
    from croniter import croniter
except ImportError:
    croniter = None

from sonar_tools.ai.ai_code_fixer import AICodeFixer
from sonar_tools.core.config import Config
from sonar_tools.main import SonarToJiraProcessor
from sonar_tools.service.mr_sync_service import MRStatusSyncService

logger = Config.setup_logging(__name__)


class TaskScheduler:
    """多任务调度器"""

    def __init__(self):
        """初始化调度器"""
        # 检查croniter依赖
        if croniter is None:
            raise ImportError("croniter库未安装，请运行: pip install croniter")

        # 设置日志
        Config.setup_logging()

        # 主任务配置
        self.main_task_enabled = Config.SCHEDULER_ENABLED
        self.main_task_cron = Config.SCHEDULER_CRON_EXPRESSION

        # MR同步任务配置
        self.mr_sync_enabled = Config.MR_SYNC_ENABLED
        self.mr_sync_cron = Config.MR_SYNC_CRON_EXPRESSION

        # AI代码修复任务配置
        self.ai_fixer_enabled = Config.AI_FIXER_ENABLED
        self.ai_fixer_cron = Config.AI_FIXER_CRON_EXPRESSION

        self.timezone = Config.SCHEDULER_TIMEZONE

        self.running = False
        self.scheduler_threads: Dict[str, threading.Thread] = {}
        self.stop_event = threading.Event()

        # 任务统计
        self.task_stats = {
            "main_task": {
                "total_runs": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "last_run": None,
                "next_run": None,
            },
            "mr_sync": {
                "total_runs": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "last_run": None,
                "next_run": None,
            },
            "ai_fixer": {
                "total_runs": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "last_run": None,
                "next_run": None,
            },
        }

        self.start_time = None

        logger.info("多任务调度器初始化完成")
        self._log_scheduler_config()

    def _log_scheduler_config(self):
        """记录调度器配置信息"""
        logger.info("调度器配置信息:")
        logger.info(f"  - 主任务状态: {'启用' if self.main_task_enabled else '禁用'}")
        if self.main_task_enabled:
            logger.info(f"    - Cron表达式: {self.main_task_cron}")
            next_run = self._get_next_run_time(self.main_task_cron)
            if next_run:
                logger.info(
                    f"    - 下次执行时间: {next_run.strftime('%Y-%m-%d %H:%M:%S')}"
                )

        logger.info(f"  - MR同步任务状态: {'启用' if self.mr_sync_enabled else '禁用'}")
        if self.mr_sync_enabled:
            logger.info(f"    - Cron表达式: {self.mr_sync_cron}")
            next_run = self._get_next_run_time(self.mr_sync_cron)
            if next_run:
                logger.info(
                    f"    - 下次执行时间: {next_run.strftime('%Y-%m-%d %H:%M:%S')}"
                )

        logger.info(
            f"  - AI代码修复任务状态: {'启用' if self.ai_fixer_enabled else '禁用'}"
        )
        if self.ai_fixer_enabled:
            logger.info(f"    - Cron表达式: {self.ai_fixer_cron}")
            next_run = self._get_next_run_time(self.ai_fixer_cron)
            if next_run:
                logger.info(
                    f"    - 下次执行时间: {next_run.strftime('%Y-%m-%d %H:%M:%S')}"
                )

        logger.info(f"  - 时区设置: {self.timezone}")

    def _validate_cron_expression(self, cron_expr: str) -> bool:
        """验证cron表达式格式"""
        try:
            croniter(cron_expr)
            return True
        except Exception as e:
            logger.error(f"无效的cron表达式 '{cron_expr}': {e}")
            return False

    def _get_next_run_time(self, cron_expr: str) -> Optional[datetime]:
        """获取下次执行时间"""
        try:
            cron = croniter(cron_expr, datetime.now())
            return cron.get_next(datetime)
        except Exception as e:
            logger.error(f"计算下次执行时间失败: {e}")
            return None

    def _execute_main_task(self) -> Dict[str, Any]:
        """执行主任务"""
        logger.info("开始执行主任务...")

        execution_start = datetime.now()
        result = {
            "task_name": "main_task",
            "start_time": execution_start,
            "success": False,
            "error": None,
            "results": None,
        }

        try:
            # 创建处理器并执行任务
            processor = SonarToJiraProcessor()

            # 测试连接
            if not processor.test_connections():
                raise Exception("连接测试失败")

            # 处理Critical问题
            task_results = processor.process_critical_issues()

            result["success"] = True
            result["results"] = task_results

            # 记录成功统计
            self.task_stats["main_task"]["successful_runs"] += 1

            logger.info("主任务执行成功")

            # 记录任务统计信息
            if "total_jira_tasks_created" in task_results:
                logger.info(
                    f"本次创建JIRA任务: {task_results['total_jira_tasks_created']} 个"
                )

        except Exception as e:
            result["error"] = str(e)
            self.task_stats["main_task"]["failed_runs"] += 1
            logger.error(f"主任务执行失败: {e}")

        finally:
            result["end_time"] = datetime.now()
            result["duration"] = result["end_time"] - execution_start
            self.task_stats["main_task"]["total_runs"] += 1
            self.task_stats["main_task"]["last_run"] = execution_start

            logger.info(f"主任务执行耗时: {result['duration']}")

        return result

    def _execute_mr_sync_task(self) -> Dict[str, Any]:
        """执行MR状态同步任务"""
        logger.info("开始执行MR状态同步任务...")

        execution_start = datetime.now()
        result = {
            "task_name": "mr_sync",
            "start_time": execution_start,
            "success": False,
            "error": None,
            "results": None,
        }

        try:
            # 创建MR同步服务并执行任务
            mr_sync_service = MRStatusSyncService()

            # 测试GitLab连接
            if not mr_sync_service.test_gitlab_connection():
                raise Exception("GitLab连接测试失败")

            # 同步MR状态
            sync_results = mr_sync_service.sync_mr_status()

            result["success"] = sync_results.get("success", False)
            result["results"] = sync_results

            if result["success"]:
                # 记录成功统计
                self.task_stats["mr_sync"]["successful_runs"] += 1
                logger.info("MR状态同步任务执行成功")

                # 记录同步统计信息
                updated_mrs = sync_results.get("updated_mrs", 0)
                total_mrs = sync_results.get("total_mrs", 0)
                logger.info(f"本次同步MR: {total_mrs} 个检查，{updated_mrs} 个更新")
            else:
                result["error"] = sync_results.get("error", "未知错误")
                raise Exception(result["error"])

        except Exception as e:
            result["error"] = str(e)
            self.task_stats["mr_sync"]["failed_runs"] += 1
            logger.error(f"MR状态同步任务执行失败: {e}")

        finally:
            result["end_time"] = datetime.now()
            result["duration"] = result["end_time"] - execution_start
            self.task_stats["mr_sync"]["total_runs"] += 1
            self.task_stats["mr_sync"]["last_run"] = execution_start

            logger.info(f"MR状态同步任务执行耗时: {result['duration']}")

        return result

    def _execute_ai_fixer_task(self) -> Dict[str, Any]:
        """执行AI代码修复任务"""
        logger.info("开始执行AI代码修复任务...")

        execution_start = datetime.now()
        result = {
            "task_name": "ai_fixer",
            "start_time": execution_start,
            "success": False,
            "error": None,
            "results": None,
        }

        try:
            # 创建AI代码修复器并执行任务
            ai_fixer = AICodeFixer()

            # 测试连接
            if not ai_fixer.test_connection():
                raise Exception("AI代码修复器连接测试失败")

            # 处理Critical问题
            success = ai_fixer.process_critical_issues(
                max_issues=Config.AI_FIXER_MAX_ISSUES
            )

            result["success"] = success
            if success:
                # 记录成功统计
                self.task_stats["ai_fixer"]["successful_runs"] += 1
                logger.info("AI代码修复任务执行成功")

                # 记录任务统计信息（这里可以从ai_fixer获取更详细的统计信息）
                result["results"] = {
                    "message": "AI代码修复任务完成",
                    "max_issues": Config.AI_FIXER_MAX_ISSUES,
                }
            else:
                raise Exception("AI代码修复任务执行失败")

        except Exception as e:
            result["error"] = str(e)
            self.task_stats["ai_fixer"]["failed_runs"] += 1
            logger.error(f"AI代码修复任务执行失败: {e}")

        finally:
            result["end_time"] = datetime.now()
            result["duration"] = result["end_time"] - execution_start
            self.task_stats["ai_fixer"]["total_runs"] += 1
            self.task_stats["ai_fixer"]["last_run"] = execution_start

            logger.info(f"AI代码修复任务执行耗时: {result['duration']}")

        return result

    def _task_scheduler_loop(self, task_name: str, cron_expr: str, task_executor):
        """单个任务的调度循环"""
        logger.info(f"任务 [{task_name}] 调度循环启动")

        while not self.stop_event.is_set():
            try:
                # 计算距离下次执行的时间
                next_run = self._get_next_run_time(cron_expr)
                if not next_run:
                    logger.error(f"任务 [{task_name}] 无法计算下次执行时间，停止调度")
                    break

                # 更新下次执行时间
                if task_name in self.task_stats:
                    self.task_stats[task_name]["next_run"] = next_run

                current_time = datetime.now()
                sleep_seconds = (next_run - current_time).total_seconds()

                if sleep_seconds > 0:
                    logger.debug(
                        f"任务 [{task_name}] 距离下次执行还有 {sleep_seconds:.0f} 秒"
                    )

                    # 使用事件等待，支持提前中断
                    if self.stop_event.wait(sleep_seconds):
                        logger.info(f"任务 [{task_name}] 收到停止信号，退出调度循环")
                        break

                # 执行任务
                if not self.stop_event.is_set():
                    task_executor()

            except Exception as e:
                logger.error(f"任务 [{task_name}] 调度循环异常: {e}")
                # 出错后等待1分钟再继续
                if not self.stop_event.wait(60):
                    continue
                break

        logger.info(f"任务 [{task_name}] 调度循环结束")

    def start(self):
        """启动调度器"""
        # 验证任务配置
        tasks_to_start = []

        if self.main_task_enabled:
            if not self._validate_cron_expression(self.main_task_cron):
                logger.error("主任务cron表达式验证失败")
                return False
            tasks_to_start.append(
                ("main_task", self.main_task_cron, self._execute_main_task)
            )

        if self.mr_sync_enabled:
            if not self._validate_cron_expression(self.mr_sync_cron):
                logger.error("MR同步任务cron表达式验证失败")
                return False
            tasks_to_start.append(
                ("mr_sync", self.mr_sync_cron, self._execute_mr_sync_task)
            )

        if self.ai_fixer_enabled:
            if not self._validate_cron_expression(self.ai_fixer_cron):
                logger.error("AI代码修复任务cron表达式验证失败")
                return False
            tasks_to_start.append(
                ("ai_fixer", self.ai_fixer_cron, self._execute_ai_fixer_task)
            )

        if not tasks_to_start:
            logger.warning("没有启用的任务，请检查配置")
            return False

        if self.running:
            logger.warning("调度器已在运行中")
            return False

        logger.info(f"启动多任务调度器，共 {len(tasks_to_start)} 个任务...")

        self.running = True
        self.start_time = datetime.now()
        self.stop_event.clear()

        # 启动各个任务的调度线程
        for task_name, cron_expr, task_executor in tasks_to_start:
            thread = threading.Thread(
                target=self._task_scheduler_loop,
                args=(task_name, cron_expr, task_executor),
                name=f"TaskScheduler-{task_name}",
                daemon=True,
            )
            thread.start()
            self.scheduler_threads[task_name] = thread
            logger.info(f"任务 [{task_name}] 调度线程已启动")

        logger.info("多任务调度器已启动")
        return True

    def stop(self):
        """停止调度器"""
        if not self.running:
            logger.info("调度器未在运行")
            return

        logger.info("正在停止多任务调度器...")

        self.running = False
        self.stop_event.set()

        # 等待所有调度器线程结束
        for task_name, thread in self.scheduler_threads.items():
            if thread and thread.is_alive():
                logger.info(f"等待任务 [{task_name}] 线程结束...")
                thread.join(timeout=10)

        self.scheduler_threads.clear()
        logger.info("多任务调度器已停止")

    def get_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        # 更新下次执行时间
        if self.running:
            for task_name in self.task_stats:
                if task_name == "main_task" and self.main_task_enabled:
                    self.task_stats[task_name]["next_run"] = self._get_next_run_time(
                        self.main_task_cron
                    )
                elif task_name == "mr_sync" and self.mr_sync_enabled:
                    self.task_stats[task_name]["next_run"] = self._get_next_run_time(
                        self.mr_sync_cron
                    )
                elif task_name == "ai_fixer" and self.ai_fixer_enabled:
                    self.task_stats[task_name]["next_run"] = self._get_next_run_time(
                        self.ai_fixer_cron
                    )

        status = {
            "running": self.running,
            "start_time": self.start_time,
            "tasks": {
                "main_task": {
                    "enabled": self.main_task_enabled,
                    "cron_expression": self.main_task_cron,
                    "stats": self.task_stats["main_task"],
                },
                "mr_sync": {
                    "enabled": self.mr_sync_enabled,
                    "cron_expression": self.mr_sync_cron,
                    "stats": self.task_stats["mr_sync"],
                },
                "ai_fixer": {
                    "enabled": self.ai_fixer_enabled,
                    "cron_expression": self.ai_fixer_cron,
                    "stats": self.task_stats["ai_fixer"],
                },
            },
            "timezone": self.timezone,
        }

        return status

    def run_once(self, task_name: str = "main_task") -> Dict[str, Any]:
        """
        立即执行一次指定任务（不影响定时调度）

        Args:
            task_name: 任务名称，'main_task'、'mr_sync' 或 'ai_fixer'
        """
        logger.info(f"手动执行任务: {task_name}")

        if task_name == "main_task":
            return self._execute_main_task()
        elif task_name == "mr_sync":
            return self._execute_mr_sync_task()
        elif task_name == "ai_fixer":
            return self._execute_ai_fixer_task()
        else:
            return {
                "success": False,
                "error": f"未知的任务名称: {task_name}",
                "task_name": task_name,
            }


def signal_handler(signum, frame):
    """信号处理器"""
    logger.info(f"收到信号 {signum}，正在关闭调度器...")
    if hasattr(signal_handler, "scheduler"):
        signal_handler.scheduler.stop()
    sys.exit(0)


def main():
    """主函数"""
    logger.info("SonarQube到Jira任务调度器启动")

    try:
        # 创建调度器
        scheduler = TaskScheduler()

        # 注册信号处理器
        signal_handler.scheduler = scheduler
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # 检查是否启用调度器
        if (
            not scheduler.main_task_enabled
            and not scheduler.mr_sync_enabled
            and not scheduler.ai_fixer_enabled
        ):
            logger.info("调度器未启用")
            logger.info(
                "要启用调度器，请在.env文件中设置 SCHEDULER_ENABLED=true、MR_SYNC_ENABLED=true 或 AI_FIXER_ENABLED=true"
            )

            # 提供手动执行选项
            response = input("是否要立即执行一次任务？(y/n): ").lower()
            if response in ["y", "yes"]:
                result = scheduler.run_once()
                if result["success"]:
                    logger.info("手动任务执行成功")
                else:
                    logger.error(f"手动任务执行失败: {result['error']}")

            return

        # 启动调度器
        if scheduler.start():
            logger.info("调度器启动成功，按 Ctrl+C 停止")

            # 显示状态信息
            while scheduler.running:
                try:
                    time.sleep(60)  # 每分钟显示一次状态

                    status = scheduler.get_status()

                    # 显示各个任务的下次执行时间
                    if status["running"]:
                        task_info = []

                        if status["tasks"]["main_task"]["enabled"]:
                            main_next = status["tasks"]["main_task"]["stats"][
                                "next_run"
                            ]
                            if main_next:
                                task_info.append(
                                    f"主任务: {main_next.strftime('%Y-%m-%d %H:%M:%S')}"
                                )

                        if status["tasks"]["mr_sync"]["enabled"]:
                            mr_next = status["tasks"]["mr_sync"]["stats"]["next_run"]
                            if mr_next:
                                task_info.append(
                                    f"MR同步: {mr_next.strftime('%Y-%m-%d %H:%M:%S')}"
                                )

                        if task_info:
                            logger.debug(
                                f"调度器运行中，下次执行时间 - {', '.join(task_info)}"
                            )

                except KeyboardInterrupt:
                    break

        else:
            logger.error("调度器启动失败")
            sys.exit(1)

    except Exception as e:
        logger.error(f"调度器异常: {e}")
        sys.exit(1)

    finally:
        logger.info("调度器程序结束")


if __name__ == "__main__":
    main()
