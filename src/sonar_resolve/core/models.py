from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class SonarIssue:
    """SonarQube问题数据模型"""
    key: str
    component: str
    project: str
    rule: str
    severity: str
    message: str
    line: Optional[int]
    creation_date: str
    update_date: str
    status: str
    type: str
    debt: Optional[str]
    effort: Optional[str]
    tags: List[str]

    @classmethod
    def from_sonar_response(cls, issue_data: Dict[str, Any]) -> 'SonarIssue':
        """从SonarQube API响应创建SonarIssue对象"""
        text_range = issue_data.get('textRange', {})

        return cls(
            key=issue_data.get('key', ''),
            component=issue_data.get('component', ''),
            project=issue_data.get('project', ''),
            rule=issue_data.get('rule', ''),
            severity=issue_data.get('severity', ''),
            message=issue_data.get('message', ''),
            line=text_range.get('startLine') if text_range else None,
            creation_date=issue_data.get('creationDate', ''),
            update_date=issue_data.get('updateDate', ''),
            status=issue_data.get('status', ''),
            type=issue_data.get('type', ''),
            debt=issue_data.get('debt'),
            effort=issue_data.get('effort'),
            tags=issue_data.get('tags', [])
        )

    def get_file_path(self) -> str:
        """获取文件路径（去除项目前缀）"""
        if ':' in self.component:
            return self.component.split(':', 1)[1]
        return self.component

    def get_location_info(self) -> str:
        """获取位置信息"""
        file_path = self.get_file_path()
        if self.line:
            return f"{file_path}:{self.line}"
        return file_path


@dataclass
class JiraTask:
    """Jira任务数据模型"""
    summary: str
    description: str
    project_key: str
    issue_type: str = "Task"
    priority: str = "High"
    labels: List[str] = None

    def __post_init__(self):
        if self.labels is None:
            self.labels = []

    @classmethod
    def from_sonar_issue(cls, sonar_issue: SonarIssue, project_key: str) -> 'JiraTask':
        """从SonarQube问题创建Jira任务"""
        summary = f"[SonarQube Critical] {sonar_issue.rule}: {sonar_issue.get_file_path()}"

        description = f"""
*SonarQube Critical Issue 自动创建任务*

*问题描述:*
{sonar_issue.message}

*受影响文件:*
{sonar_issue.get_location_info()}

*问题严重等级:*
{sonar_issue.severity}

*相关项目:*
{sonar_issue.project}

*规则:*
{sonar_issue.rule}

*问题类型:*
{sonar_issue.type}

*创建时间:*
{sonar_issue.creation_date}

*SonarQube链接:*
{sonar_issue.key}

*标签:*
{', '.join(sonar_issue.tags) if sonar_issue.tags else '无'}
        """.strip()

        labels = ["sonarqube", "critical", "automated"] + sonar_issue.tags

        return cls(
            summary=summary,
            description=description,
            project_key=project_key,
            issue_type="Task",
            priority="High",
            labels=labels
        )
