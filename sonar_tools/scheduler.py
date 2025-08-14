#!/usr/bin/env python3
"""
定时任务调度器
使用cron表达式定时执行SonarQube到Jira的任务创建
"""

import logging
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

from .core.config import Config
from .main import SonarToJiraProcessor

logger = Config.setup_logging(__name__)


class TaskScheduler:
    """任务调度器"""

    def __init__(self):
        """初始化调度器"""
        # 检查croniter依赖
        if croniter is None:
            raise ImportError("croniter库未安装，请运行: pip install croniter")

        # 设置日志
        Config.setup_logging()

        self.cron_expression = Config.SCHEDULER_CRON_EXPRESSION
        self.timezone = Config.SCHEDULER_TIMEZONE
        self.enabled = Config.SCHEDULER_ENABLED

        self.running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

        # 任务统计
        self.total_runs = 0
        self.successful_runs = 0
        self.failed_runs = 0
        self.start_time = None

        logger.info("任务调度器初始化完成")
        self._log_scheduler_config()

    def _log_scheduler_config(self):
        """记录调度器配置信息"""
        logger.info("调度器配置信息:")
        logger.info(f"  - 调度器状态: {'启用' if self.enabled else '禁用'}")
        logger.info(f"  - Cron表达式: {self.cron_expression}")
        logger.info(f"  - 时区设置: {self.timezone}")

        if self.enabled:
            # 计算下次执行时间
            next_run = self._get_next_run_time()
            if next_run:
                logger.info(f"  - 下次执行时间: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")

    def _validate_cron_expression(self) -> bool:
        """验证cron表达式格式"""
        try:
            croniter(self.cron_expression)
            return True
        except Exception as e:
            logger.error(f"无效的cron表达式 '{self.cron_expression}': {e}")
            return False

    def _get_next_run_time(self) -> Optional[datetime]:
        """获取下次执行时间"""
        try:
            cron = croniter(self.cron_expression, datetime.now())
            return cron.get_next(datetime)
        except Exception as e:
            logger.error(f"计算下次执行时间失败: {e}")
            return None

    def _execute_task(self) -> Dict[str, Any]:
        """执行主任务"""
        logger.info("开始执行定时任务...")

        execution_start = datetime.now()
        result = {
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
            self.successful_runs += 1

            logger.info("定时任务执行成功")

            # 记录任务统计信息
            if "total_jira_tasks_created" in task_results:
                logger.info(f"本次创建JIRA任务: {task_results['total_jira_tasks_created']} 个")

        except Exception as e:
            result["error"] = str(e)
            self.failed_runs += 1
            logger.error(f"定时任务执行失败: {e}")

        finally:
            result["end_time"] = datetime.now()
            result["duration"] = result["end_time"] - execution_start
            self.total_runs += 1

            logger.info(f"任务执行耗时: {result['duration']}")

        return result

    def _scheduler_loop(self):
        """调度器主循环"""
        logger.info("调度器主循环启动")

        while not self.stop_event.is_set():
            try:
                # 计算距离下次执行的时间
                next_run = self._get_next_run_time()
                if not next_run:
                    logger.error("无法计算下次执行时间，调度器停止")
                    break

                current_time = datetime.now()
                sleep_seconds = (next_run - current_time).total_seconds()

                if sleep_seconds > 0:
                    logger.debug(f"距离下次执行还有 {sleep_seconds:.0f} 秒")

                    # 使用事件等待，支持提前中断
                    if self.stop_event.wait(sleep_seconds):
                        logger.info("收到停止信号，退出调度循环")
                        break

                # 执行任务
                if not self.stop_event.is_set():
                    self._execute_task()

            except Exception as e:
                logger.error(f"调度器循环异常: {e}")
                # 出错后等待1分钟再继续
                if not self.stop_event.wait(60):
                    continue
                break

        logger.info("调度器主循环结束")

    def start(self):
        """启动调度器"""
        if not self.enabled:
            logger.warning("调度器未启用，请设置 SCHEDULER_ENABLED=true")
            return False

        if not self._validate_cron_expression():
            return False

        if self.running:
            logger.warning("调度器已在运行中")
            return False

        logger.info("启动任务调度器...")

        self.running = True
        self.start_time = datetime.now()
        self.stop_event.clear()

        # 启动调度器线程
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_loop, name="TaskScheduler", daemon=True
        )
        self.scheduler_thread.start()

        logger.info("任务调度器已启动")
        return True

    def stop(self):
        """停止调度器"""
        if not self.running:
            logger.info("调度器未在运行")
            return

        logger.info("正在停止任务调度器...")

        self.running = False
        self.stop_event.set()

        # 等待调度器线程结束
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=10)

        logger.info("任务调度器已停止")

    def get_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        status = {
            "enabled": self.enabled,
            "running": self.running,
            "cron_expression": self.cron_expression,
            "timezone": self.timezone,
            "total_runs": self.total_runs,
            "successful_runs": self.successful_runs,
            "failed_runs": self.failed_runs,
            "start_time": self.start_time,
            "next_run_time": None,
        }

        if self.running:
            status["next_run_time"] = self._get_next_run_time()

        return status

    def run_once(self) -> Dict[str, Any]:
        """立即执行一次任务（不影响定时调度）"""
        logger.info("手动执行任务...")
        return self._execute_task()


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
        if not scheduler.enabled:
            logger.info("调度器未启用")
            logger.info("要启用调度器，请在.env文件中设置 SCHEDULER_ENABLED=true")

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
                    if status["next_run_time"]:
                        logger.debug(
                            f"调度器运行中，下次执行: "
                            f"{status['next_run_time'].strftime('%Y-%m-%d %H:%M:%S')}"
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
