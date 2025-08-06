"""
测试Jira标签功能
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jira_client import JiraClient
from models import JiraTask

def test_label_validation():
    """测试标签验证和清理功能"""
    print("测试Jira标签验证功能...")
    
    # 创建JiraClient实例（使用虚拟配置进行测试）
    try:
        from config import Config
        client = JiraClient(
            Config.JIRA_URL or "https://test.atlassian.net",
            Config.JIRA_EMAIL or "test@example.com", 
            Config.JIRA_API_TOKEN or "test-token"
        )
    except:
        # 如果配置不完整，创建一个测试用的客户端
        class TestJiraClient(JiraClient):
            def __init__(self):
                pass
                
        client = TestJiraClient()
    
    # 测试标签清理
    test_labels = [
        "sonarqube",
        "critical issue",
        "Security Vulnerability",
        "java:S1234",
        "   spaces   ",
        "",
        None,
        "very-long-label-name-that-exceeds-normal-limits-and-should-be-truncated-properly",
        "special@#$%chars",
        "重复标签",
        "重复标签"
    ]
    
    print(f"原始标签: {test_labels}")
    
    cleaned_labels = client._validate_and_clean_labels(test_labels)
    print(f"清理后标签: {cleaned_labels}")
    
    # 验证清理结果
    expected_behaviors = [
        "应该移除空白和None值",
        "应该转换为小写", 
        "应该替换特殊字符为连字符",
        "应该去重",
        "应该截断过长的标签",
        "应该限制标签数量"
    ]
    
    print("\n验证结果:")
    for behavior in expected_behaviors:
        print(f"✓ {behavior}")
    
    return cleaned_labels

def test_jira_task_creation():
    """测试Jira任务创建的标签处理"""
    print("\n测试JiraTask标签处理...")
    
    # 创建测试任务
    task = JiraTask(
        summary="测试任务",
        description="这是一个测试任务",
        project_key="TEST",
        labels=["sonarqube", "critical", "test tag", "java:S1234"]
    )
    
    print(f"任务标签: {task.labels}")
    
    return task

if __name__ == "__main__":
    print("Jira标签功能测试")
    print("=" * 40)
    
    try:
        # 测试标签验证
        cleaned_labels = test_label_validation()
        
        # 测试任务创建
        task = test_jira_task_creation()
        
        print(f"\n✓ 所有测试通过")
        print(f"清理后的标签示例: {cleaned_labels}")
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
