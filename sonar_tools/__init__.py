"""
SonarQube自动修复与Jira集成工具

这是一个强大的Python工具，能够自动从SonarQube获取Critical级别的问题，
使用AI进行代码修复，并集成Git和Jira工作流。

主要功能：
- 智能项目发现和匹配
- SonarQube问题分析
- Jira任务自动创建
- AI代码自动修复
- Git工作流集成
- GitLab Merge Request自动创建
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from sonar_tools.clients.jira_client import JiraClient

# 客户端导入
from sonar_tools.clients.sonarqube_client import SonarQubeClient

# 核心组件导入
from sonar_tools.core.config import Config
from sonar_tools.core.models import JiraTask, SonarIssue

__all__ = [
    # 版本信息
    "__version__",
    "__author__",
    "__email__",
    # 核心组件
    "Config",
    "SonarIssue",
    "JiraTask",
    # 客户端
    "SonarQubeClient",
    "JiraClient",
]
