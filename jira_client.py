from jira import JIRA
import logging
from typing import List, Dict, Any, Optional
from models import JiraTask, SonarIssue
from config import Config

logger = logging.getLogger(__name__)

class JiraClient:
    """Jira API客户端"""
    
    def __init__(self, server: str, username: str, password: str):
        self.server = server
        self.username = username
        
        try:
            self.jira = JIRA(
                server=server,
                basic_auth=(username, password)
            )
            logger.info("Jira客户端初始化成功")
        except Exception as e:
            logger.error(f"Jira客户端初始化失败: {e}")
            raise
    
    def create_issue(self, task: JiraTask) -> Optional[str]:
        """创建Jira问题"""
        issue_dict = {
            'project': {'key': task.project_key},
            'summary': task.summary,
            'description': task.description,
            'issuetype': {'name': task.issue_type},
            'priority': {'name': task.priority}
        }
        
        try:
            # 创建问题
            new_issue = self.jira.create_issue(fields=issue_dict)
            
            # 添加标签
            if task.labels:
                new_issue.update(labels=task.labels)
            
            logger.info(f"成功创建Jira任务: {new_issue.key} - {task.summary}")
            return new_issue.key
            
        except Exception as e:
            logger.error(f"创建Jira任务失败: {e}")
            logger.error(f"任务信息: {task.summary}")
            return None
    
    def create_issues_from_sonar(self, sonar_issues: List[SonarIssue], project_key: str) -> List[str]:
        """从SonarQube问题批量创建Jira任务"""
        created_issues = []
        
        for i, sonar_issue in enumerate(sonar_issues, 1):
            logger.info(f"创建第 {i}/{len(sonar_issues)} 个Jira任务...")
            
            # 检查是否已存在相同的任务（基于summary）
            if self._issue_exists(sonar_issue, project_key):
                logger.info(f"跳过已存在的任务: {sonar_issue.key}")
                continue
            
            # 创建Jira任务
            jira_task = JiraTask.from_sonar_issue(sonar_issue, project_key)
            issue_key = self.create_issue(jira_task)
            
            if issue_key:
                created_issues.append(issue_key)
        
        logger.info(f"总共创建了 {len(created_issues)} 个Jira任务")
        return created_issues
    
    def _issue_exists(self, sonar_issue: SonarIssue, project_key: str) -> bool:
        """检查是否已存在相同的Jira任务"""
        try:
            # 使用SonarQube问题的key作为搜索条件
            jql = f'project = {project_key} AND summary ~ "{sonar_issue.key}"'
            issues = self.jira.search_issues(jql, maxResults=1)
            return len(issues) > 0
        except Exception as e:
            logger.warning(f"检查任务是否存在时出错: {e}")
            return False
    
    def test_connection(self) -> bool:
        """测试Jira连接"""
        try:
            # 尝试获取当前用户信息
            current_user = self.jira.current_user()
            logger.info(f"Jira连接测试成功，当前用户: {current_user}")
            return True
        except Exception as e:
            logger.error(f"Jira连接测试失败: {e}")
            return False
    
    def get_project_info(self, project_key: str) -> Optional[Dict[str, Any]]:
        """获取项目信息"""
        try:
            project = self.jira.project(project_key)
            return {
                'key': project.key,
                'name': project.name,
                'lead': project.lead.displayName if project.lead else None,
                'description': getattr(project, 'description', '')
            }
        except Exception as e:
            logger.error(f"获取Jira项目信息失败: {e}")
            return None
