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
    SONARQUBE_PROJECT_KEY = os.getenv('SONARQUBE_PROJECT_KEY')
    
    # Jira配置
    JIRA_URL = os.getenv('JIRA_URL')
    JIRA_EMAIL = os.getenv('JIRA_EMAIL')
    JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')
    JIRA_PROJECT_KEY = os.getenv('JIRA_PROJECT_KEY')
    
    # Git配置
    GIT_REPOSITORY_PATH = os.getenv('GIT_REPOSITORY_PATH')
    GIT_REMOTE_URL = os.getenv('GIT_REMOTE_URL')
    GIT_USERNAME = os.getenv('GIT_USERNAME')
    GIT_TOKEN = os.getenv('GIT_TOKEN')
    
    # GitLab配置（用于创建Merge Request）
    GITLAB_URL = os.getenv('GITLAB_URL')
    GITLAB_TOKEN = os.getenv('GITLAB_TOKEN')
    GITLAB_PROJECT_ID = os.getenv('GITLAB_PROJECT_ID')
    
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
            cls.SONARQUBE_PROJECT_KEY,
            cls.JIRA_URL,
            cls.JIRA_EMAIL,
            cls.JIRA_API_TOKEN,
            cls.JIRA_PROJECT_KEY
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
        git_configs = [
            cls.GIT_REPOSITORY_PATH,
            cls.GIT_REMOTE_URL,
            cls.GIT_USERNAME,
            cls.GIT_TOKEN
        ]
        
        missing_configs = [config for config in git_configs if not config]
        
        if missing_configs:
            raise ValueError(f"缺少Git配置: {missing_configs}")
        
        return True
