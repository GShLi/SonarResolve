import re
from jira import JIRA
import logging
from typing import List, Dict, Any, Optional
from ..core.models import JiraTask, SonarIssue
from ..core.config import Config

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
        
        # 如果有标签，直接在创建时添加
        if task.labels:
            # 验证和清理标签
            valid_labels = self._validate_and_clean_labels(task.labels)
            if valid_labels:
                issue_dict['labels'] = valid_labels
        
        try:
            # 创建问题
            new_issue = self.jira.create_issue(fields=issue_dict)
            
            # 如果创建时标签添加失败，尝试后续添加
            if task.labels and not hasattr(new_issue.fields, 'labels'):
                try:
                    self._add_labels_to_issue(new_issue, task.labels)
                except Exception as label_error:
                    logger.warning(f"后续添加标签失败: {label_error}")
            
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
    
    def _add_labels_to_issue(self, issue, labels: List[str]):
        """为issue添加标签的辅助方法"""
        try:
            # 过滤并清理标签
            valid_labels = [label.strip().replace(' ', '-') for label in labels if label and label.strip()]
            
            if not valid_labels:
                return
            
            # 方法1: 直接更新
            try:
                issue.update(fields={'labels': valid_labels})
                logger.debug(f"成功添加标签: {valid_labels}")
                return
            except Exception as e1:
                logger.debug(f"方法1失败: {e1}")
            
            # 方法2: 获取现有标签后合并
            try:
                fresh_issue = self.jira.issue(issue.key)
                current_labels = []
                if hasattr(fresh_issue.fields, 'labels') and fresh_issue.fields.labels:
                    current_labels = [label.name if hasattr(label, 'name') else str(label) 
                                    for label in fresh_issue.fields.labels]
                
                # 合并标签，去重
                all_labels = list(set(current_labels + valid_labels))
                fresh_issue.update(fields={'labels': all_labels})
                logger.debug(f"成功合并添加标签: {all_labels}")
                return
            except Exception as e2:
                logger.debug(f"方法2失败: {e2}")
            
            # 方法3: 使用REST API直接更新
            try:
                update_data = {
                    "fields": {
                        "labels": valid_labels
                    }
                }
                self.jira._session.put(
                    f"{self.jira._options['server']}/rest/api/2/issue/{issue.key}",
                    json=update_data
                )
                logger.debug(f"通过REST API成功添加标签: {valid_labels}")
            except Exception as e3:
                logger.warning(f"所有添加标签方法都失败: {e3}")
                
        except Exception as e:
            logger.error(f"添加标签时发生未预期错误: {e}")
    
    def _validate_and_clean_labels(self, labels: List[str]) -> List[str]:
        """验证和清理标签"""
        if not labels:
            return []
        
        valid_labels = []
        for label in labels:
            if not label or not isinstance(label, str):
                continue
                
            # 清理标签：去空格、转小写、替换特殊字符
            cleaned_label = label.strip().lower()
            
            # 替换空格和特殊字符为连字符
            cleaned_label = re.sub(r'[^\w\-]', '-', cleaned_label)
            
            # 移除多余的连字符
            cleaned_label = re.sub(r'-+', '-', cleaned_label)
            
            # 移除开头和结尾的连字符
            cleaned_label = cleaned_label.strip('-')
            
            # 检查长度限制（Jira标签通常有长度限制）
            if len(cleaned_label) > 50:
                cleaned_label = cleaned_label[:50]
            
            # 确保不为空且不重复
            if cleaned_label and cleaned_label not in valid_labels:
                valid_labels.append(cleaned_label)
        
        return valid_labels[:10]  # 限制标签数量，避免过多
    
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
