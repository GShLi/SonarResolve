"""
客户端模块

包含与外部服务交互的客户端类：
- SonarQubeClient: SonarQube API客户端
- JiraClient: Jira API客户端  
- AIClient: AI服务客户端
"""

from .sonarqube_client import SonarQubeClient
from .jira_client import JiraClient
from .ai_client import AIClient

__all__ = ["SonarQubeClient", "JiraClient", "AIClient"]
