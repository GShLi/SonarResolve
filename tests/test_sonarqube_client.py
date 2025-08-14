"""
Tests for SonarQube client functionality
"""
from unittest.mock import Mock, patch

import pytest
from models import SonarIssue
from sonarqube_client import SonarQubeClient


class TestSonarQubeClient:
    """Test SonarQube client functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.client = SonarQubeClient("https://test.sonar.com", "test-token")

    @patch("sonarqube_client.requests.Session.get")
    def test_connection_success(self, mock_get):
        """Test successful connection to SonarQube"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"status": "UP"}
        mock_get.return_value = mock_response

        result = self.client.test_connection()
        assert result is True

    @patch("sonarqube_client.requests.Session.get")
    def test_connection_failure(self, mock_get):
        """Test failed connection to SonarQube"""
        mock_get.side_effect = Exception("Connection failed")

        result = self.client.test_connection()
        assert result is False

    @patch("sonarqube_client.requests.Session.get")
    def test_get_critical_issues(self, mock_get):
        """Test getting critical issues"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "total": 1,
            "issues": [
                {
                    "key": "TEST-123",
                    "component": "test:src/main.py",
                    "project": "test-project",
                    "rule": "python:S1234",
                    "severity": "CRITICAL",
                    "message": "Test issue",
                    "textRange": {"startLine": 10},
                    "creationDate": "2024-01-01T00:00:00Z",
                    "updateDate": "2024-01-01T00:00:00Z",
                    "status": "OPEN",
                    "type": "BUG",
                    "tags": ["security"],
                }
            ],
        }
        mock_get.return_value = mock_response

        issues = self.client.get_critical_issues("test-project")

        assert len(issues) == 1
        assert isinstance(issues[0], SonarIssue)
        assert issues[0].key == "TEST-123"
        assert issues[0].severity == "CRITICAL"
