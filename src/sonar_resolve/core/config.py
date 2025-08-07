import os
from typing import Dict, Any
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """配置管理类"""

    # SonarQube配置
    SONARQUBE_URL = os.getenv('SONARQUBE_URL')
    SONARQUBE_TOKEN = os.getenv('SONARQUBE_TOKEN')

    # Jira配置
    JIRA_URL = os.getenv('JIRA_URL')
    JIRA_PROJECT_LEAD = os.getenv('JIRA_PROJECT_LEAD')
    JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')
    JIRA_TASK_PREFIX = os.getenv('JIRA_TASK_PREFIX', '[质量管理]')

    # GitLab配置（用于仓库管理和Merge Request）
    GITLAB_URL = os.getenv('GITLAB_URL')
    GITLAB_TOKEN = os.getenv('GITLAB_TOKEN')

    # Git仓库配置
    GIT_REPOSITORY_PATH = os.getenv('GIT_REPOSITORY_PATH', '.')

    # 本地工作目录配置
    LOCAL_WORKSPACE = os.getenv('LOCAL_WORKSPACE', './workspace')

    # AI模型配置
    AI_PROVIDER = os.getenv('AI_PROVIDER', 'openai')  # openai, anthropic, azure
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    AI_MODEL = os.getenv('AI_MODEL', 'gpt-4')

    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    @classmethod
    def validate_config(cls) -> bool:
        """验证配置是否完整"""
        required_configs = [
            cls.SONARQUBE_URL,
            cls.SONARQUBE_TOKEN,
            cls.JIRA_URL,
            cls.JIRA_PROJECT_LEAD,
            cls.JIRA_API_TOKEN
        ]

        missing_configs = [config for config in required_configs if not config]

        if missing_configs:
            raise ValueError(f"缺少必要配置: {missing_configs}")

        return True

    @classmethod
    def validate_ai_config(cls) -> bool:
        """验证AI配置"""
        if cls.AI_PROVIDER == 'openai' and not cls.OPENAI_API_KEY:
            raise ValueError("使用OpenAI时需要配置OPENAI_API_KEY")

        if cls.AI_PROVIDER == 'anthropic' and not cls.ANTHROPIC_API_KEY:
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
