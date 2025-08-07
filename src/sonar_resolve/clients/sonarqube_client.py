import requests
import logging
from typing import List, Dict, Any
from urllib.parse import urljoin
from src.sonar_resolve.core.models import SonarIssue

logger = logging.getLogger(__name__)

class SonarQubeClient:
    """SonarQube API客户端"""
    
    def __init__(self, url: str, token: str):
        self.base_url = url.rstrip('/')
        self.token = token
        self.session = requests.Session()
        self.session.auth = (token, '')
        
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """发送API请求"""
        url = urljoin(self.base_url + '/', f'api/{endpoint}')
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"SonarQube API请求失败: {e}")
            raise
    
    def get_critical_issues(self, project_key: str = None, page_size: int = 500) -> List[SonarIssue]:
        """
        获取Critical级别的问题
        
        Args:
            project_key: 项目Key，如果为None则获取所有项目的Critical问题
            page_size: 每页大小
            
        Returns:
            SonarIssue对象列表
        """
        issues = []
        page = 1
        
        while True:
            params = {
                'severities': 'CRITICAL',
                'statuses': 'OPEN,CONFIRMED,REOPENED',
                'ps': page_size,
                'p': page
            }
            
            # 如果指定了项目，则只查询该项目
            if project_key:
                params['componentKeys'] = project_key
                logger.info(f"获取项目 {project_key} 第 {page} 页的Critical问题...")
            else:
                logger.info(f"获取所有项目第 {page} 页的Critical问题...")
            
            try:
                response = self._make_request('issues/search', params)
                
                # 转换为SonarIssue对象
                page_issues = [
                    SonarIssue.from_sonar_response(issue_data) 
                    for issue_data in response.get('issues', [])
                ]
                
                issues.extend(page_issues)
                
                # 检查是否还有更多页面
                total = response.get('total', 0)
                current_count = len(issues)
                
                if project_key:
                    logger.info(f"项目 {project_key} 已获取 {current_count}/{total} 个Critical问题")
                else:
                    logger.info(f"已获取 {current_count}/{total} 个Critical问题")
                
                if current_count >= total:
                    break
                
                page += 1
                
            except Exception as e:
                logger.error(f"获取Critical问题失败: {e}")
                raise
        
        if project_key:
            logger.info(f"项目 {project_key} 总共获取到 {len(issues)} 个Critical问题")
        else:
            logger.info(f"所有项目总共获取到 {len(issues)} 个Critical问题")
        return issues
    
    def get_project_info(self, project_key: str) -> Dict[str, Any]:
        """获取项目信息"""
        params = {'project': project_key}
        
        try:
            response = self._make_request('components/show', params)
            return response.get('component', {})
        except Exception as e:
            logger.error(f"获取项目信息失败: {e}")
            raise
    
    def test_connection(self) -> bool:
        """测试SonarQube连接"""
        try:
            self._make_request('system/status')
            logger.info("SonarQube连接测试成功")
            return True
        except Exception as e:
            logger.error(f"SonarQube连接测试失败: {e}")
            return False
