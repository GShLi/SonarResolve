"""
项目发现和匹配管理器
自动发现并匹配SonarQube和Jira项目
"""

import os
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from ..clients.sonarqube_client import SonarQubeClient
from ..clients.jira_client import JiraClient

logger = logging.getLogger(__name__)

@dataclass
class ProjectMapping:
    """项目映射信息"""
    sonar_key: str
    sonar_name: str
    jira_key: str
    jira_name: str
    similarity_score: float
    mapping_reason: str

class ProjectDiscovery:
    """项目发现和匹配管理器"""
    
    def __init__(self, sonar_client: SonarQubeClient, jira_client: JiraClient):
        self.sonar_client = sonar_client
        self.jira_client = jira_client
    
    def discover_projects(self, git_remote_url: str = None) -> List[ProjectMapping]:
        """发现并匹配项目"""
        logger.info("开始自动发现和匹配项目...")
        
        # 获取SonarQube项目列表
        sonar_projects = self._get_sonar_projects()
        logger.info(f"发现 {len(sonar_projects)} 个SonarQube项目")
        
        # 获取Jira项目列表
        jira_projects = self._get_jira_projects()
        logger.info(f"发现 {len(jira_projects)} 个Jira项目")
        
        # 从Git URL推断项目名称
        git_project_name = self._extract_project_name_from_git(git_remote_url) if git_remote_url else None
        
        # 匹配项目
        mappings = self._match_projects(sonar_projects, jira_projects, git_project_name)
        
        # 按相似度排序
        mappings.sort(key=lambda x: x.similarity_score, reverse=True)
        
        logger.info(f"找到 {len(mappings)} 个项目匹配")
        
        return mappings
    
    def get_best_project_mapping(self, git_remote_url: str = None) -> Optional[ProjectMapping]:
        """获取最佳项目匹配"""
        mappings = self.discover_projects(git_remote_url)
        
        if not mappings:
            logger.warning("未找到任何项目匹配")
            return None
        
        best_mapping = mappings[0]
        logger.info(f"选择最佳匹配: {best_mapping.sonar_name} <-> {best_mapping.jira_name} (相似度: {best_mapping.similarity_score:.2f})")
        
        return best_mapping
    
    def _get_sonar_projects(self) -> List[Dict[str, Any]]:
        """获取SonarQube项目列表"""
        try:
            response = self.sonar_client._make_request('components/search', {
                'qualifiers': 'TRK',
                'ps': 100
            })
            
            projects = []
            for component in response.get('components', []):
                projects.append({
                    'key': component.get('key'),
                    'name': component.get('name'),
                    'qualifier': component.get('qualifier')
                })
            
            return projects
            
        except Exception as e:
            logger.error(f"获取SonarQube项目列表失败: {e}")
            return []
    
    def _get_jira_projects(self) -> List[Dict[str, Any]]:
        """获取Jira项目列表"""
        try:
            projects = self.jira_client.jira.projects()
            
            project_list = []
            for project in projects:
                project_list.append({
                    'key': project.key,
                    'name': project.name,
                    'description': getattr(project, 'description', ''),
                    'lead': project.lead.displayName if project.lead else None
                })
            
            return project_list
            
        except Exception as e:
            logger.error(f"获取Jira项目列表失败: {e}")
            return []
    
    def _extract_project_name_from_git(self, git_url: str) -> Optional[str]:
        """从Git URL提取项目名称"""
        if not git_url:
            return None
        
        try:
            # 匹配常见的Git URL格式
            patterns = [
                r'https?://[^/]+/[^/]+/([^/]+?)(?:\.git)?/?$',  # https://gitlab.com/user/project.git
                r'git@[^:]+:([^/]+)/([^/]+?)(?:\.git)?/?$',     # git@gitlab.com:user/project.git
                r'/([^/]+?)(?:\.git)?/?$'                       # 简单路径
            ]
            
            for pattern in patterns:
                match = re.search(pattern, git_url)
                if match:
                    project_name = match.group(-1)  # 取最后一个组
                    # 清理项目名称
                    project_name = project_name.replace('.git', '').replace('-', ' ').replace('_', ' ')
                    logger.info(f"从Git URL提取项目名称: {project_name}")
                    return project_name
            
            logger.warning(f"无法从Git URL提取项目名称: {git_url}")
            return None
            
        except Exception as e:
            logger.error(f"解析Git URL失败: {e}")
            return None
    
    def _match_projects(self, sonar_projects: List[Dict[str, Any]], 
                       jira_projects: List[Dict[str, Any]], 
                       git_project_name: str = None) -> List[ProjectMapping]:
        """匹配SonarQube和Jira项目"""
        mappings = []
        
        for sonar_project in sonar_projects:
            sonar_key = sonar_project['key']
            sonar_name = sonar_project['name']
            
            for jira_project in jira_projects:
                jira_key = jira_project['key']
                jira_name = jira_project['name']
                
                # 计算相似度
                similarity_score, reason = self._calculate_similarity(
                    sonar_key, sonar_name, jira_key, jira_name, git_project_name
                )
                
                # 只保留有一定相似度的匹配
                if similarity_score > 0.3:
                    mapping = ProjectMapping(
                        sonar_key=sonar_key,
                        sonar_name=sonar_name,
                        jira_key=jira_key,
                        jira_name=jira_name,
                        similarity_score=similarity_score,
                        mapping_reason=reason
                    )
                    mappings.append(mapping)
        
        return mappings
    
    def _calculate_similarity(self, sonar_key: str, sonar_name: str, 
                            jira_key: str, jira_name: str, 
                            git_project_name: str = None) -> Tuple[float, str]:
        """计算项目相似度"""
        scores = []
        reasons = []
        
        # 1. 项目键相似度
        key_similarity = self._string_similarity(sonar_key.lower(), jira_key.lower())
        if key_similarity > 0.7:
            scores.append(key_similarity * 0.4)
            reasons.append(f"项目键相似 ({key_similarity:.2f})")
        
        # 2. 项目名称相似度
        name_similarity = self._string_similarity(sonar_name.lower(), jira_name.lower())
        if name_similarity > 0.5:
            scores.append(name_similarity * 0.3)
            reasons.append(f"项目名称相似 ({name_similarity:.2f})")
        
        # 3. 与Git项目名称的相似度
        if git_project_name:
            git_name_lower = git_project_name.lower()
            sonar_git_similarity = self._string_similarity(sonar_name.lower(), git_name_lower)
            jira_git_similarity = self._string_similarity(jira_name.lower(), git_name_lower)
            
            if sonar_git_similarity > 0.6 and jira_git_similarity > 0.6:
                git_similarity = (sonar_git_similarity + jira_git_similarity) / 2
                scores.append(git_similarity * 0.3)
                reasons.append(f"与Git项目名称匹配 ({git_similarity:.2f})")
        
        # 4. 关键词匹配
        keyword_score = self._keyword_matching(sonar_name, jira_name)
        if keyword_score > 0:
            scores.append(keyword_score * 0.2)
            reasons.append(f"关键词匹配 ({keyword_score:.2f})")
        
        # 5. 特殊规则匹配
        special_score = self._special_rule_matching(sonar_key, sonar_name, jira_key, jira_name)
        if special_score > 0:
            scores.append(special_score * 0.1)
            reasons.append(f"特殊规则匹配 ({special_score:.2f})")
        
        total_score = sum(scores) if scores else 0
        reason = "; ".join(reasons) if reasons else "无明显关联"
        
        return min(total_score, 1.0), reason
    
    def _string_similarity(self, s1: str, s2: str) -> float:
        """计算字符串相似度（简单的Jaccard相似度）"""
        if not s1 or not s2:
            return 0.0
        
        # 分割成词
        words1 = set(re.findall(r'\w+', s1.lower()))
        words2 = set(re.findall(r'\w+', s2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        # Jaccard相似度
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _keyword_matching(self, sonar_name: str, jira_name: str) -> float:
        """关键词匹配"""
        # 常见的项目关键词
        keywords = ['api', 'service', 'web', 'app', 'core', 'common', 'util', 'client', 'server']
        
        sonar_words = set(re.findall(r'\w+', sonar_name.lower()))
        jira_words = set(re.findall(r'\w+', jira_name.lower()))
        
        common_keywords = sonar_words.intersection(jira_words).intersection(keywords)
        
        return len(common_keywords) * 0.2
    
    def _special_rule_matching(self, sonar_key: str, sonar_name: str, 
                              jira_key: str, jira_name: str) -> float:
        """特殊规则匹配"""
        score = 0.0
        
        # 规则1: 如果项目键包含相同的组织或团队前缀
        sonar_prefix = sonar_key.split(':')[0] if ':' in sonar_key else sonar_key.split('-')[0]
        if len(sonar_prefix) > 2 and sonar_prefix.lower() in jira_key.lower():
            score += 0.3
        
        # 规则2: 如果项目名称包含年份或版本号
        year_pattern = r'20\d{2}'
        version_pattern = r'v?\d+\.\d+'
        
        sonar_has_version = bool(re.search(year_pattern, sonar_name) or re.search(version_pattern, sonar_name))
        jira_has_version = bool(re.search(year_pattern, jira_name) or re.search(version_pattern, jira_name))
        
        if sonar_has_version and jira_has_version:
            score += 0.2
        
        return min(score, 1.0)
    
    def list_available_projects(self) -> Dict[str, List[Dict[str, Any]]]:
        """列出所有可用的项目"""
        return {
            'sonar_projects': self._get_sonar_projects(),
            'jira_projects': self._get_jira_projects()
        }
