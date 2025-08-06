"""
核心功能模块

包含主要的业务逻辑：
- config: 配置管理
- models: 数据模型
- project_discovery: 项目发现和匹配
- main: 主要处理逻辑
- auto_fix: AI自动修复
"""

from .config import Config
from .models import SonarIssue, JiraTask
from .project_discovery import ProjectDiscovery, ProjectMapping

__all__ = ["Config", "SonarIssue", "JiraTask", "ProjectDiscovery", "ProjectMapping"]
