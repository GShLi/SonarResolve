import requests
import logging
import re
from typing import List, Dict, Any
from urllib.parse import urljoin
from src.sonar_resolve.core.models import SonarIssue
from src.sonar_resolve.core.config import Config

logger = logging.getLogger(__name__)


class SonarQubeClient:
    """SonarQube API客户端"""

    def __init__(self, url: str, token: str):
        self.base_url = url.rstrip('/')
        self.token = token
        self.session = requests.Session()
        self.session.auth = (token, '')
    
    def _clean_html_tags(self, text: str) -> str:
        """清理HTML标签"""
        if not text:
            return ''
        
        # 移除HTML标签
        clean_text = re.sub(r'<[^>]+>', '', text)
        
        # 解码常见的HTML实体
        html_entities = {
            '&lt;': '<',
            '&gt;': '>',
            '&amp;': '&',
            '&quot;': '"',
            '&#39;': "'",
            '&nbsp;': ' '
        }
        
        for entity, char in html_entities.items():
            clean_text = clean_text.replace(entity, char)
        
        return clean_text

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

                # 转换为SonarIssue对象，并根据配置获取代码片段
                page_issues = []
                for issue_data in response.get('issues', []):
                    # 创建SonarIssue对象
                    sonar_issue = SonarIssue.from_sonar_response(issue_data)

                    # 根据配置决定是否获取代码片段
                    if Config.SONARQUBE_FETCH_CODE_SNIPPET:
                        code_snippet = self.get_issue_code_snippet(issue_data)
                        sonar_issue.code_snippet = code_snippet

                    page_issues.append(sonar_issue)

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

    def get_source_code(self, component_key: str, from_line: int = None, to_line: int = None) -> List[str]:
        """
        获取组件的源代码
        
        Args:
            component_key: 组件Key（文件路径）
            from_line: 起始行号
            to_line: 结束行号
            
        Returns:
            源代码行列表
        """
        params = {'key': component_key}

        if from_line is not None:
            params['from'] = from_line
        if to_line is not None:
            params['to'] = to_line

        try:
            response = self._make_request('sources/show', params)
            sources = response.get('sources', [])
            
            # 调试信息
            logger.debug(f"获取源代码 {component_key}: 返回 {len(sources)} 行")
            if sources and len(sources) > 0:
                logger.debug(f"第一行格式示例: {type(sources[0])}: {sources[0]}")

            # 提取代码行
            code_lines = []
            for source_line in sources:
                try:
                    # source_line 是一个数组：[行号, 包含HTML标签的代码字符串]
                    if isinstance(source_line, list) and len(source_line) >= 2:
                        line_number = source_line[0]
                        code_content = self._clean_html_tags(source_line[1])
                    elif isinstance(source_line, dict):
                        # 备用处理：如果是字典格式
                        line_number = source_line.get('line', 0)
                        code_content = self._clean_html_tags(source_line.get('code', ''))
                    else:
                        # 其他格式的备用处理
                        line_number = 0
                        code_content = str(source_line)
                    
                    code_lines.append(f"{line_number:4d}: {code_content}")
                    
                except Exception as parse_error:
                    logger.debug(f"解析源代码行失败: {parse_error}, source_line: {source_line}")
                    # 添加错误行但不中断处理
                    code_lines.append(f"   ?: {str(source_line)}")

            return code_lines

        except Exception as e:
            logger.warning(f"获取源代码失败 {component_key}: {e}")
            return []

    def get_issue_code_snippet(self, issue_data: Dict[str, Any], context_lines: int = 3) -> str:
        """
        获取问题相关的代码片段
        
        Args:
            issue_data: SonarQube问题数据
            context_lines: 上下文行数
            
        Returns:
            格式化的代码片段
        """
        try:
            component_key = issue_data.get('component', '')
            text_range = issue_data.get('textRange', {})

            if not text_range:
                return "无具体行号信息"

            start_line = text_range.get('startLine', 0)
            if not start_line:
                return "无具体行号信息"

            # 计算获取代码的范围
            from_line = max(1, start_line - context_lines)
            to_line = start_line + context_lines

            # 获取源代码
            code_lines = self.get_source_code(component_key, from_line, to_line)

            if not code_lines:
                return "无法获取源代码"

            # 标记问题所在行
            formatted_lines = []
            for line in code_lines:
                line_parts = line.split(': ', 1)
                if len(line_parts) == 2:
                    line_num = int(line_parts[0].strip())
                    line_content = line_parts[1]

                    if line_num == start_line:
                        formatted_lines.append(f"→ {line_num:4d}: {line_content}")
                    else:
                        formatted_lines.append(f"  {line_num:4d}: {line_content}")
                else:
                    formatted_lines.append(line)

            return '\n'.join(formatted_lines)

        except Exception as e:
            logger.warning(f"获取问题代码片段失败: {e}")
            return f"获取代码片段失败: {str(e)}"

    def test_connection(self) -> bool:
        """测试SonarQube连接"""
        try:
            self._make_request('system/status')
            logger.info("SonarQube连接测试成功")
            return True
        except Exception as e:
            logger.error(f"SonarQube连接测试失败: {e}")
            return False
