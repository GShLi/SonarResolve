import os
from typing import Any, Dict

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """配置管理类"""

    # SonarQube配置
    SONARQUBE_URL = os.getenv("SONARQUBE_URL")
    SONARQUBE_TOKEN = os.getenv("SONARQUBE_TOKEN")
    SONARQUBE_FETCH_CODE_SNIPPET = (
        os.getenv("SONARQUBE_FETCH_CODE_SNIPPET", "true").lower() == "true"
    )

    # Jira配置
    JIRA_URL = os.getenv("JIRA_URL")
    JIRA_PROJECT_LEAD = os.getenv("JIRA_PROJECT_LEAD")
    JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
    JIRA_TASK_PREFIX = os.getenv("JIRA_TASK_PREFIX", "[质量管理]")
    JIRA_INCLUDE_CODE_SNIPPET = (
        os.getenv("JIRA_INCLUDE_CODE_SNIPPET", "true").lower() == "true"
    )
    JIRA_CODE_CONTEXT_LINES = int(os.getenv("JIRA_CODE_CONTEXT_LINES", "3"))
    # 单次运行创建JIRA任务的最大数量限制（0表示无限制）
    JIRA_MAX_TASKS_PER_RUN = int(os.getenv("JIRA_MAX_TASKS_PER_RUN", "50"))

    # GitLab配置（用于仓库管理和Merge Request）
    GITLAB_URL = os.getenv("GITLAB_URL")
    GITLAB_TOKEN = os.getenv("GITLAB_TOKEN")

    # Git仓库配置
    GIT_REPOSITORY_PATH = os.getenv("GIT_REPOSITORY_PATH", ".")

    # 本地工作目录配置
    LOCAL_WORKSPACE = os.getenv("LOCAL_WORKSPACE", "./workspace")

    # AI模型配置
    AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")  # openai, anthropic, azure
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")  # LiteLLM代理地址
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    AI_MODEL = os.getenv("AI_MODEL", "gpt-4")
    AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.1"))
    AI_MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS", "4000"))

    # AI自动修复配置
    AI_AUTO_FIX_ENABLED = os.getenv("AI_AUTO_FIX_ENABLED", "false").lower() == "true"
    AI_CODE_CONTEXT_LINES = int(os.getenv("AI_CODE_CONTEXT_LINES", "10"))
    AI_MAX_RETRIES = int(os.getenv("AI_MAX_RETRIES", "3"))

    # AI代码应用配置
    AI_APPLY_FIXES = (
        os.getenv("AI_APPLY_FIXES", "true").lower() == "true"
    )  # 是否使用AI智能应用修复
    AI_APPLY_CONFIDENCE_THRESHOLD = int(
        os.getenv("AI_APPLY_CONFIDENCE_THRESHOLD", "7")
    )  # AI应用信心阈值(1-10)
    AI_FALLBACK_TO_TRADITIONAL = (
        os.getenv("AI_FALLBACK_TO_TRADITIONAL", "true").lower() == "true"
    )  # AI失败时是否回退传统方法

    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    # 确保日志文件存储在项目根目录的 logs 目录中
    _project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    )
    LOG_FILE_PATH = os.getenv(
        "LOG_FILE_PATH", os.path.join(_project_root, "logs", "sonar_resolve.log")
    )
    LOG_MAX_SIZE = int(os.getenv("LOG_MAX_SIZE", "10"))  # MB
    LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    LOG_FORMAT = os.getenv(
        "LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # 数据库配置
    # 确保数据库文件存储在项目根目录的 db 目录中
    DATABASE_PATH = os.getenv(
        "DATABASE_PATH", os.path.join(_project_root, "db", "project_status.db")
    )
    DATABASE_BACKUP = os.getenv("DATABASE_BACKUP", "false").lower() == "true"

    # 调度器配置
    # Cron表达式配置，默认每天凌晨2点执行 (分 时 日 月 周)
    SCHEDULER_CRON_EXPRESSION = os.getenv("SCHEDULER_CRON_EXPRESSION", "0 2 * * *")
    # 是否启用调度器
    SCHEDULER_ENABLED = os.getenv("SCHEDULER_ENABLED", "false").lower() == "true"
    # 调度器时区
    SCHEDULER_TIMEZONE = os.getenv("SCHEDULER_TIMEZONE", "Asia/Shanghai")

    # MR状态同步配置
    # MR状态同步的Cron表达式，默认每10分钟执行一次
    MR_SYNC_CRON_EXPRESSION = os.getenv("MR_SYNC_CRON_EXPRESSION", "*/10 * * * *")
    # 是否启用MR状态同步
    MR_SYNC_ENABLED = os.getenv("MR_SYNC_ENABLED", "true").lower() == "true"
    # MR状态同步时查询最近几天的MR
    MR_SYNC_DAYS_BACK = int(os.getenv("MR_SYNC_DAYS_BACK", "7"))

    @classmethod
    def validate_config(cls) -> bool:
        """验证配置是否完整"""
        required_configs = [
            cls.SONARQUBE_URL,
            cls.SONARQUBE_TOKEN,
            cls.JIRA_URL,
            cls.JIRA_PROJECT_LEAD,
            cls.JIRA_API_TOKEN,
        ]

        missing_configs = [config for config in required_configs if not config]

        if missing_configs:
            raise ValueError(f"缺少必要配置: {missing_configs}")

        return True

    @classmethod
    def validate_ai_config(cls) -> bool:
        """验证AI配置"""
        if cls.AI_PROVIDER == "openai" and not cls.OPENAI_API_KEY:
            raise ValueError("使用OpenAI时需要配置OPENAI_API_KEY")

        if cls.AI_PROVIDER == "anthropic" and not cls.ANTHROPIC_API_KEY:
            raise ValueError("使用Anthropic时需要配置ANTHROPIC_API_KEY")

        return True

    @classmethod
    def validate_git_config(cls) -> bool:
        """验证Git配置"""
        # Git仓库路径是可选的，使用默认值即可
        return True

    @classmethod
    def validate_gitlab_config(cls) -> bool:
        """验证GitLab配置"""
        if not cls.GITLAB_URL or not cls.GITLAB_TOKEN:
            raise ValueError("GitLab自动仓库管理需要配置GITLAB_URL和GITLAB_TOKEN")
        return True

    @classmethod
    def setup_logging(cls):
        """设置日志配置"""
        import logging
        import logging.handlers
        from pathlib import Path

        # 确保日志目录存在
        log_file_path = Path(cls.LOG_FILE_PATH)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)

        # 设置日志级别
        numeric_level = getattr(logging, cls.LOG_LEVEL.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f"Invalid log level: {cls.LOG_LEVEL}")

        # 配置根日志器
        root_logger = logging.getLogger()
        root_logger.setLevel(numeric_level)

        # 清除现有的处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # 文件处理器（带轮转）
        file_handler = logging.handlers.RotatingFileHandler(
            log_file_path,
            maxBytes=cls.LOG_MAX_SIZE * 1024 * 1024,  # 转换为字节
            backupCount=cls.LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(logging.Formatter(cls.LOG_FORMAT))

        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(logging.Formatter(cls.LOG_FORMAT))

        # 添加处理器
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

        return root_logger

    @classmethod
    def get_log_info(cls) -> Dict[str, Any]:
        """获取日志配置信息"""
        from pathlib import Path

        log_file_path = Path(cls.LOG_FILE_PATH)

        return {
            "log_file_path": str(log_file_path.absolute()),
            "log_directory": str(log_file_path.parent.absolute()),
            "log_level": cls.LOG_LEVEL,
            "log_max_size_mb": cls.LOG_MAX_SIZE,
            "log_backup_count": cls.LOG_BACKUP_COUNT,
            "log_format": cls.LOG_FORMAT,
            "log_file_exists": log_file_path.exists(),
            "log_directory_exists": log_file_path.parent.exists(),
        }
