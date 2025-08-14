"""
Tests for data models
"""
import pytest
from models import JiraTask, SonarIssue


class TestSonarIssue:
    """Test SonarIssue model"""

    def test_from_sonar_response(self):
        """Test creating SonarIssue from API response"""
        response_data = {
            "key": "TEST-123",
            "component": "test:src/main.py",
            "project": "test-project",
            "rule": "python:S1234",
            "severity": "CRITICAL",
            "message": "Test issue message",
            "textRange": {"startLine": 10},
            "creationDate": "2024-01-01T00:00:00Z",
            "updateDate": "2024-01-01T00:00:00Z",
            "status": "OPEN",
            "type": "BUG",
            "tags": ["security", "performance"],
        }

        issue = SonarIssue.from_sonar_response(response_data)

        assert issue.key == "TEST-123"
        assert issue.component == "test:src/main.py"
        assert issue.severity == "CRITICAL"
        assert issue.line == 10
        assert issue.tags == ["security", "performance"]

    def test_get_file_path(self):
        """Test getting file path from component"""
        issue = SonarIssue(
            key="TEST-123",
            component="project:src/main.py",
            project="test",
            rule="test",
            severity="CRITICAL",
            message="test",
            line=1,
            creation_date="2024-01-01",
            update_date="2024-01-01",
            status="OPEN",
            type="BUG",
            debt=None,
            effort=None,
            tags=[],
        )

        file_path = issue.get_file_path()
        assert file_path == "src/main.py"

    def test_get_location_info(self):
        """Test getting location information"""
        issue = SonarIssue(
            key="TEST-123",
            component="project:src/main.py",
            project="test",
            rule="test",
            severity="CRITICAL",
            message="test",
            line=10,
            creation_date="2024-01-01",
            update_date="2024-01-01",
            status="OPEN",
            type="BUG",
            debt=None,
            effort=None,
            tags=[],
        )

        location = issue.get_location_info()
        assert location == "src/main.py:10"


class TestJiraTask:
    """Test JiraTask model"""

    def test_from_sonar_issue(self):
        """Test creating JiraTask from SonarIssue"""
        sonar_issue = SonarIssue(
            key="SONAR-123",
            component="project:src/main.py",
            project="test-project",
            rule="python:S1234",
            severity="CRITICAL",
            message="Critical security issue",
            line=10,
            creation_date="2024-01-01T00:00:00Z",
            update_date="2024-01-01T00:00:00Z",
            status="OPEN",
            type="VULNERABILITY",
            debt="30min",
            effort="1h",
            tags=["security"],
        )

        jira_task = JiraTask.from_sonar_issue(sonar_issue, "PROJ")

        assert jira_task.project_key == "PROJ"
        assert "Critical security issue" in jira_task.description
        assert "src/main.py:10" in jira_task.description
        assert "CRITICAL" in jira_task.description
        assert "python:S1234" in jira_task.description
        assert "security" in jira_task.labels
