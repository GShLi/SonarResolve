#!/usr/bin/env python3
"""
SonarQube Critical Issues Auto-Fix
自动修复SonarQube Critical问题并创建Merge Request
"""

import logging
import sys
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

from src.sonar_resolve.core.config import Config
from src.sonar_resolve.clients.sonarqube_client import SonarQubeClient
from src.sonar_resolve.clients.jira_client import JiraClient
from src.sonar_resolve.clients.ai_client import CodeFixer
from src.sonar_resolve.clients.git_client import GitClient, GitManager, AutoFixProcessor
from src.sonar_resolve.core.models import SonarIssue

# 检查GitLab库是否可用
try:
    import gitlab
    GITLAB_AVAILABLE = True
except ImportError:
    GITLAB_AVAILABLE = False

# 配置日志
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'sonar_autofix_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

logger = logging.getLogger(__name__)

class SonarAutoFixProcessor:
    """SonarQube自动修复处理器"""
    
    def __init__(self):
        # 验证所有配置
        try:
            Config.validate_config()
            Config.validate_ai_config()
            Config.validate_git_config()
        except ValueError as e:
            logger.error(f"配置验证失败: {e}")
            sys.exit(1)
        
        # 初始化客户端
        self.sonar_client = SonarQubeClient(
            Config.SONARQUBE_URL,
            Config.SONARQUBE_TOKEN
        )
        
        self.jira_client = JiraClient(
            Config.JIRA_URL,
            Config.JIRA_EMAIL,
            Config.JIRA_API_TOKEN
        )
        
        self.code_fixer = CodeFixer()
        self.git_repo_manager = GitClient()
        
        # 初始化项目发现器
        self.project_discovery = ProjectDiscovery(self.sonar_client, self.jira_client)
    
    def test_all_connections(self) -> bool:
        """测试所有连接"""
        logger.info("开始连接测试...")
        
        sonar_ok = self.sonar_client.test_connection()
        jira_ok = self.jira_client.test_connection()
        
        if sonar_ok and jira_ok:
            logger.info("所有连接测试通过")
            return True
        else:
            logger.error("连接测试失败")
            return False
    
    def _get_git_remote_url(self) -> Optional[str]:
        """获取当前Git仓库的远程URL"""
        try:
            # 尝试从Config.GIT_REPOSITORY_PATH获取Git远程URL
            if hasattr(Config, 'GIT_REPOSITORY_PATH') and Config.GIT_REPOSITORY_PATH:
                import subprocess
                result = subprocess.run(
                    ['git', 'remote', 'get-url', 'origin'],
                    cwd=Config.GIT_REPOSITORY_PATH,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    return result.stdout.strip()
            
            # 如果上述方法失败，尝试从当前目录获取
            import subprocess
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
                
        except Exception as e:
            logger.debug(f"获取Git远程URL失败: {e}")
        
        return None
    
    def _auto_discover_project(self) -> Optional[str]:
        """自动发现SonarQube项目"""
        try:
            # 尝试从当前Git仓库获取远程URL
            git_remote_url = self._get_git_remote_url()
            if git_remote_url:
                logger.info(f"检测到Git远程URL: {git_remote_url}")
                project_mapping = self.project_discovery.get_best_project_mapping(git_remote_url)
                if project_mapping:
                    logger.info(f"自动发现项目: {project_mapping.sonar_name}")
                    return project_mapping.sonar_key
            
            # 如果无法从Git URL发现，尝试获取第一个可用项目
            response = self.sonar_client._make_request('components/search', {
                'qualifiers': 'TRK',
                'ps': 1
            })
            
            components = response.get('components', [])
            if components:
                project_key = components[0]['key']
                logger.info(f"使用第一个可用项目: {project_key}")
                return project_key
                
        except Exception as e:
            logger.error(f"自动发现项目失败: {e}")
        
        return None
    
    def _get_repository_info(self, project_key: str) -> Optional[Dict[str, Any]]:
        """从SonarQube项目信息获取GitLab仓库信息"""
        try:
            # 获取SonarQube项目详情
            project_info = self.sonar_client._make_request(f'projects/search', {
                'projects': project_key
            })
            
            if not project_info.get('components'):
                logger.error(f"SonarQube项目不存在: {project_key}")
                return None
            
            sonar_project = project_info['components'][0]
            project_name = sonar_project.get('name', project_key)
            
            # 使用初始化的git_repo_manager查找仓库
            # 首先尝试用项目key查找
            repo_info = self.git_repo_manager.find_repository_by_project_name(project_key)
            if not repo_info:
                # 再尝试用项目名查找
                repo_info = self.git_repo_manager.find_repository_by_project_name(project_name)
            
            if not repo_info:
                logger.error(f"在GitLab中未找到对应仓库: {project_name}")
                return None
            
            logger.info(f"找到GitLab仓库: {repo_info['full_path']}")
            return repo_info
            
        except Exception as e:
            logger.error(f"获取仓库信息失败: {e}")
            return None
    
    def _clone_or_pull_repository(self, repository_info: Dict[str, Any]) -> Optional[str]:
        """克隆或更新GitLab仓库"""
        try:
            # 使用GitClient的现有方法
            success, local_path = self.git_repo_manager.clone_or_update_repository(
                repository_info['full_path']
            )
            
            if success and local_path:
                logger.info(f"仓库准备完成: {local_path}")
                return str(local_path)
            else:
                logger.error("仓库克隆/更新失败")
                return None
                
        except Exception as e:
            logger.error(f"克隆仓库失败: {e}")
            return None
    
    def _commit_and_push_fixes(self, fixes: List[Dict[str, Any]], 
                              sonar_issues: List[SonarIssue],
                              local_repo_path: str, 
                              repository_info: Dict[str, Any]) -> Dict[str, Any]:
        """提交修复到新分支并推送"""
        try:
            from datetime import datetime
            
            # 生成分支名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            branch_name = f"sonar-fix-{timestamp}"
            
            # 使用GitManager来处理Git操作
            git_manager = GitManager(local_repo_path)
            
            # 创建新分支
            if not git_manager.create_branch(branch_name):
                return {
                    'success': False,
                    'message': f"创建分支失败: {branch_name}",
                    'branch_name': None
                }
            
            logger.info(f"创建分支: {branch_name}")
            
            # 应用修复
            modified_files = []
            for fix in fixes:
                file_path = fix['file_path']
                fixed_content = fix['fixed_content']
                
                # 写入修复后的内容
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                
                # 计算相对路径用于git add
                rel_path = os.path.relpath(file_path, local_repo_path)
                modified_files.append(rel_path)
                logger.info(f"修复文件: {rel_path}")
            
            # 生成提交信息
            commit_message = self._generate_commit_message(sonar_issues, fixes)
            
            # 提交更改
            if not git_manager.commit_changes(modified_files, commit_message):
                return {
                    'success': False,
                    'message': "提交更改失败",
                    'branch_name': branch_name
                }
            
            logger.info("代码提交成功")
            
            # 推送到远程
            if not git_manager.push_branch(branch_name):
                return {
                    'success': False,
                    'message': f"推送分支失败: {branch_name}",
                    'branch_name': branch_name
                }
            
            logger.info(f"推送到远程分支: {branch_name}")
            
            return {
                'success': True,
                'branch_name': branch_name,
                'modified_files': modified_files,
                'commit_message': commit_message
            }
                
        except Exception as e:
            return {
                'success': False,
                'message': f"提交修复失败: {e}",
                'branch_name': None
            }
    
    def _create_merge_request(self, git_result: Dict[str, Any], 
                            repository_info: Dict[str, Any],
                            sonar_issues: List[SonarIssue],
                            fixes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """创建Merge Request"""
        try:
            if not GITLAB_AVAILABLE:
                return {
                    'success': False,
                    'message': "GitLab库不可用，无法创建Merge Request"
                }
            
            # 使用git_manager.py中的GitLabManager
            from ..clients.git_manager import GitLabManager
            gitlab_manager = GitLabManager()
            
            # 生成MR标题和描述
            mr_title = f"🔧 SonarQube Critical问题自动修复 ({len(fixes)}个问题)"
            mr_description = self._generate_mr_description(sonar_issues, fixes)
            
            # 创建Merge Request
            mr_result = gitlab_manager.create_merge_request(
                project_id=str(repository_info['id']),
                source_branch=git_result['branch_name'],
                target_branch=repository_info.get('default_branch', 'main'),
                title=mr_title,
                description=mr_description,
                labels=['sonar-fix', 'automated', 'critical']
            )
            
            if mr_result:
                logger.info(f"Merge Request创建成功: {mr_result['url']}")
                return {
                    'success': True,
                    'merge_request_url': mr_result['url'],
                    'merge_request_id': mr_result['id']
                }
            else:
                return {
                    'success': False,
                    'message': "创建Merge Request失败"
                }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"创建Merge Request失败: {e}"
            }
    
    def _generate_commit_message(self, sonar_issues: List[SonarIssue], 
                               fixes: List[Dict[str, Any]]) -> str:
        """生成提交信息"""
        if len(fixes) == 1:
            issue = fixes[0]['issue']
            return f"fix: 修复SonarQube {issue.severity}问题 - {issue.rule}\n\n{issue.message}"
        else:
            return f"fix: 修复{len(fixes)}个SonarQube Critical问题\n\n自动修复的问题包括:\n" + \
                   "\n".join([f"- {fix['issue'].rule}: {fix['issue'].message}" for fix in fixes[:5]]) + \
                   (f"\n... 以及其他{len(fixes)-5}个问题" if len(fixes) > 5 else "")
    
    def _generate_mr_description(self, sonar_issues: List[SonarIssue], 
                               fixes: List[Dict[str, Any]]) -> str:
        """生成Merge Request描述"""
        description = f"""## 🔧 SonarQube Critical问题自动修复

本次自动修复了 **{len(fixes)}** 个SonarQube Critical级别问题。

### 📊 修复统计
- 总问题数: {len(sonar_issues)}
- 成功修复: {len(fixes)}
- 修复类型: Critical级别问题

### 📋 修复详情
"""
        
        for i, fix in enumerate(fixes[:10], 1):  # 最多显示10个
            issue = fix['issue']
            file_path = os.path.relpath(fix['file_path']) if 'file_path' in fix else 'N/A'
            description += f"""
**{i}. {issue.rule}**
- 文件: `{file_path}`
- 行号: {issue.line or 'N/A'}
- 问题: {issue.message}
- 类型: {issue.type}
"""
        
        if len(fixes) > 10:
            description += f"\n... 以及其他 {len(fixes) - 10} 个问题的修复\n"
        
        description += """
### ✅ 自动化流程
- [x] 从SonarQube获取Critical问题
- [x] 使用AI大模型自动修复
- [x] 自动提交到新分支
- [x] 创建Merge Request

> 本次修复由SonarResolve自动化工具完成 🤖
"""
        
        return description
    
    def _get_all_critical_issues_by_project(self) -> Dict[str, List[SonarIssue]]:
        """获取所有Critical问题并按项目分组"""
        try:
            logger.info("查询所有Critical问题...")
            
            # 获取所有Critical问题（不指定项目）
            all_issues = self.sonar_client.get_critical_issues()
            
            # 按项目分组
            issues_by_project = {}
            for issue in all_issues:
                project_key = issue.project  # 使用project属性而不是project_key
                if project_key not in issues_by_project:
                    issues_by_project[project_key] = []
                issues_by_project[project_key].append(issue)
            
            logger.info(f"找到 {len(all_issues)} 个Critical问题，涉及 {len(issues_by_project)} 个项目")
            for project_key, issues in issues_by_project.items():
                logger.info(f"  项目 {project_key}: {len(issues)} 个问题")
            
            return issues_by_project
            
        except Exception as e:
            logger.error(f"获取Critical问题失败: {e}")
            return {}
    
    def _find_jira_project_for_sonar(self, sonar_project_key: str) -> Optional[str]:
        """为SonarQube项目查找对应的Jira项目"""
        try:
            project_mapping = self.project_discovery.get_best_project_mapping()
            if project_mapping and project_mapping.sonar_key == sonar_project_key:
                return project_mapping.jira_key
        except Exception as e:
            logger.debug(f"查找Jira项目失败: {e}")
        return None
    
    def process_batch_auto_fix(self, create_jira_tasks: bool = False) -> Dict[str, Any]:
        """
        批量自动修复流程：
        1. 从SonarQube获取所有Critical问题
        2. 按项目分组
        3. 对每个项目执行自动修复流程
        """
        logger.info("开始批量SonarQube Critical问题自动修复流程...")
        
        batch_results = {
            'start_time': datetime.now(),
            'total_projects': 0,
            'total_issues': 0,
            'successful_projects': 0,
            'failed_projects': 0,
            'total_fixes_applied': 0,
            'total_jira_tasks_created': 0,
            'project_results': {},
            'errors': [],
            'success': False
        }
        
        try:
            # 1. 获取所有Critical问题并按项目分组
            issues_by_project = self._get_all_critical_issues_by_project()
            
            if not issues_by_project:
                logger.info("没有发现任何Critical问题")
                batch_results['success'] = True
                return batch_results
            
            batch_results['total_projects'] = len(issues_by_project)
            batch_results['total_issues'] = sum(len(issues) for issues in issues_by_project.values())
            
            logger.info(f"将处理 {batch_results['total_projects']} 个项目，共 {batch_results['total_issues']} 个Critical问题")
            
            # 2. 对每个项目执行自动修复
            for project_key, sonar_issues in issues_by_project.items():
                logger.info(f"\n{'='*60}")
                logger.info(f"开始处理项目: {project_key} ({len(sonar_issues)} 个问题)")
                logger.info(f"{'='*60}")
                
                try:
                    # 执行单个项目的自动修复
                    project_result = self._process_single_project_auto_fix(
                        project_key, sonar_issues, create_jira_tasks
                    )
                    
                    # 记录项目结果
                    batch_results['project_results'][project_key] = project_result
                    
                    if project_result['success']:
                        batch_results['successful_projects'] += 1
                        batch_results['total_fixes_applied'] += project_result['fixes_applied']
                        batch_results['total_jira_tasks_created'] += project_result['jira_tasks_created']
                        
                        logger.info(f"项目 {project_key} 处理成功:")
                        logger.info(f"  修复问题: {project_result['fixes_applied']} 个")
                        if project_result['merge_request_url']:
                            logger.info(f"  Merge Request: {project_result['merge_request_url']}")
                    else:
                        batch_results['failed_projects'] += 1
                        batch_results['errors'].extend([f"项目 {project_key}: {error}" for error in project_result['errors']])
                        logger.error(f"项目 {project_key} 处理失败")
                        for error in project_result['errors']:
                            logger.error(f"  - {error}")
                
                except Exception as e:
                    error_msg = f"处理项目 {project_key} 时发生异常: {e}"
                    logger.error(error_msg)
                    batch_results['errors'].append(error_msg)
                    batch_results['failed_projects'] += 1
            
            # 判断整体成功状态
            batch_results['success'] = batch_results['successful_projects'] > 0
            
            # 生成批量处理报告
            self._generate_batch_auto_fix_report(batch_results)
            
        except Exception as e:
            error_msg = f"批量自动修复流程中发生错误: {e}"
            logger.error(error_msg)
            batch_results['errors'].append(error_msg)
        
        finally:
            batch_results['end_time'] = datetime.now()
            batch_results['duration'] = batch_results['end_time'] - batch_results['start_time']
        
        return batch_results
    
    def _process_single_project_auto_fix(self, project_key: str, sonar_issues: List[SonarIssue], 
                                       create_jira_tasks: bool = False) -> Dict[str, Any]:
        """处理单个项目的自动修复"""
        results = {
            'start_time': datetime.now(),
            'project_key': project_key,
            'sonar_issues_count': len(sonar_issues),
            'fixes_applied': 0,
            'jira_tasks_created': 0,
            'merge_request_url': None,
            'branch_name': None,
            'repository_url': None,
            'local_repo_path': None,
            'errors': [],
            'success': False
        }
        
        try:
            # 2. 从SonarQube获取项目信息并从GitLab获取仓库地址
            logger.info("获取项目信息和GitLab仓库地址...")
            repository_info = self._get_repository_info(project_key)
            if not repository_info:
                error_msg = f"无法获取项目 {project_key} 的GitLab仓库信息"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                return results
            
            results['repository_url'] = repository_info['clone_url']
            logger.info(f"找到GitLab仓库: {repository_info['full_path']}")
            
            # 3. 使用GitLab Access Token拉取代码
            logger.info("从GitLab拉取代码...")
            local_repo_path = self._clone_or_pull_repository(repository_info)
            if not local_repo_path:
                error_msg = "无法拉取GitLab仓库代码"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                return results
            
            results['local_repo_path'] = str(local_repo_path)
            logger.info(f"代码拉取成功: {local_repo_path}")
            
            # 4. 根据SonarQube问题信息调用大模型修复
            logger.info("使用AI大模型修复问题...")
            fixes = self.code_fixer.fix_multiple_issues(sonar_issues, str(local_repo_path))
            
            if not fixes:
                logger.warning("没有生成任何修复")
                results['success'] = True  # 没有修复不算失败
                return results
            
            logger.info(f"成功生成 {len(fixes)} 个修复")
            results['fixes_applied'] = len(fixes)
            
            # 5. Commit并Push代码到新分支
            logger.info("提交修复到新分支...")
            git_result = self._commit_and_push_fixes(fixes, sonar_issues, local_repo_path, repository_info)
            
            if not git_result['success']:
                logger.error(f"Git操作失败: {git_result['message']}")
                results['errors'].append(git_result['message'])
                return results
            
            results['branch_name'] = git_result['branch_name']
            logger.info(f"修复推送成功，分支: {git_result['branch_name']}")
            
            # 6. 创建Merge Request合并到main分支
            logger.info("创建Merge Request...")
            mr_result = self._create_merge_request(git_result, repository_info, sonar_issues, fixes)
            
            if mr_result['success']:
                results['success'] = True
                results['merge_request_url'] = mr_result['merge_request_url']
                logger.info(f"Merge Request创建成功: {mr_result['merge_request_url']}")
            else:
                logger.error(f"创建Merge Request失败: {mr_result['message']}")
                results['errors'].append(mr_result['message'])
            
            # 可选：在Jira中创建任务
            if create_jira_tasks:
                logger.info("创建Jira任务...")
                jira_project_key = self._find_jira_project_for_sonar(project_key)
                if jira_project_key:
                    created_tasks = self.jira_client.create_issues_from_sonar(
                        sonar_issues, 
                        jira_project_key
                    )
                    results['jira_tasks_created'] = len(created_tasks)
                    
        except Exception as e:
            error_msg = f"处理项目 {project_key} 时发生错误: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
        
        finally:
            results['end_time'] = datetime.now()
            results['duration'] = results['end_time'] - results['start_time']
        
        return results
    
    def process_auto_fix(self, project_key: str = None, create_jira_tasks: bool = False) -> Dict[str, Any]:
        """
        自动修复流程（支持单项目和批量处理）：
        - 如果指定project_key，则只处理该项目
        - 如果不指定project_key，则获取所有Critical问题并批量处理
        """
        if project_key:
            # 单项目处理模式
            logger.info(f"开始处理指定项目: {project_key}")
            
            # 获取指定项目的Critical问题
            sonar_issues = self.sonar_client.get_critical_issues(project_key)
            if not sonar_issues:
                logger.info(f"项目 {project_key} 没有发现Critical问题")
                return {
                    'start_time': datetime.now(),
                    'end_time': datetime.now(),
                    'duration': datetime.now() - datetime.now(),
                    'project_key': project_key,
                    'sonar_issues_count': 0,
                    'fixes_applied': 0,
                    'jira_tasks_created': 0,
                    'merge_request_url': None,
                    'branch_name': None,
                    'repository_url': None,
                    'local_repo_path': None,
                    'errors': [],
                    'success': True
                }
            
            logger.info(f"项目 {project_key} 发现 {len(sonar_issues)} 个Critical问题")
            return self._process_single_project_auto_fix(project_key, sonar_issues, create_jira_tasks)
        else:
            # 批量处理模式
            logger.info("未指定项目，启动批量处理模式")
            return self.process_batch_auto_fix(create_jira_tasks)
    
    def _generate_batch_auto_fix_report(self, batch_results: Dict[str, Any]):
        """生成批量自动修复报告"""
        logger.info("生成批量自动修复报告...")
        
        report_content = f"""
SonarQube Critical问题批量自动修复报告
==========================================

处理时间: {batch_results['start_time'].strftime('%Y-%m-%d %H:%M:%S')}
处理耗时: {batch_results['duration']}

总体统计:
- 处理项目总数: {batch_results['total_projects']} 个
- 成功处理项目: {batch_results['successful_projects']} 个
- 失败项目: {batch_results['failed_projects']} 个
- 成功率: {(batch_results['successful_projects'] / batch_results['total_projects'] * 100) if batch_results['total_projects'] > 0 else 0:.1f}%

问题修复统计:
- 发现Critical问题总数: {batch_results['total_issues']} 个
- 成功修复问题总数: {batch_results['total_fixes_applied']} 个
- 修复率: {(batch_results['total_fixes_applied'] / batch_results['total_issues'] * 100) if batch_results['total_issues'] > 0 else 0:.1f}%
- 创建Jira任务总数: {batch_results['total_jira_tasks_created']} 个

项目处理详情:
"""
        
        # 成功处理的项目
        successful_projects = [k for k, v in batch_results['project_results'].items() if v['success']]
        if successful_projects:
            report_content += "\n✅ 成功处理的项目:\n"
            for project_key in successful_projects:
                result = batch_results['project_results'][project_key]
                report_content += f"""
📋 项目: {project_key}
   - 发现问题: {result['sonar_issues_count']} 个
   - 成功修复: {result['fixes_applied']} 个
   - 处理耗时: {result['duration']}
   - GitLab仓库: {result.get('repository_url', 'N/A')}
   - Git分支: {result.get('branch_name', 'N/A')}
   - Merge Request: {result.get('merge_request_url', 'N/A')}
   - Jira任务: {result['jira_tasks_created']} 个
"""
        
        # 失败的项目
        failed_projects = [k for k, v in batch_results['project_results'].items() if not v['success']]
        if failed_projects:
            report_content += "\n❌ 处理失败的项目:\n"
            for project_key in failed_projects:
                result = batch_results['project_results'][project_key]
                report_content += f"""
📋 项目: {project_key}
   - 发现问题: {result['sonar_issues_count']} 个
   - 失败原因:
"""
                for error in result['errors']:
                    report_content += f"     • {error}\n"
        
        # 整体错误信息
        if batch_results['errors']:
            report_content += f"\n🚨 整体处理错误:\n"
            for error in batch_results['errors']:
                report_content += f"- {error}\n"
        
        report_content += f"""
==========================================
批量处理状态: {'成功' if batch_results['success'] else '失败'}
成功项目数: {batch_results['successful_projects']}/{batch_results['total_projects']}
总修复数: {batch_results['total_fixes_applied']} 个问题
==========================================
"""
        
        # 保存报告
        report_filename = f'sonar_batch_autofix_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"批量处理报告已保存到: {report_filename}")
        
        # 显示摘要
        print(f"\n{'='*70}")
        print("🔧 SonarQube批量自动修复完成")
        print(f"{'='*70}")
        print(f"处理项目: {batch_results['successful_projects']}/{batch_results['total_projects']} 个成功")
        print(f"发现问题: {batch_results['total_issues']} 个")
        print(f"成功修复: {batch_results['total_fixes_applied']} 个")
        print(f"处理耗时: {batch_results['duration']}")
        
        if successful_projects:
            print(f"\n✅ 成功处理的项目:")
            for project_key in successful_projects:
                result = batch_results['project_results'][project_key]
                print(f"  📋 {project_key}: {result['fixes_applied']}/{result['sonar_issues_count']} 个问题已修复")
                if result['merge_request_url']:
                    print(f"     🔗 MR: {result['merge_request_url']}")
        
        if failed_projects:
            print(f"\n❌ 处理失败的项目:")
            for project_key in failed_projects:
                print(f"  📋 {project_key}")
        
        print(f"\n📄 详细报告: {report_filename}")

    def _generate_auto_fix_report(self, sonar_issues: List[SonarIssue], 
                                 fixes: List[Dict[str, Any]], 
                                 git_result: Dict[str, Any],
                                 results: Dict[str, Any]):
        """生成自动修复报告"""
        logger.info("生成自动修复报告...")
        
        report_content = f"""
SonarQube Critical问题自动修复报告
==========================================

处理时间: {results['start_time'].strftime('%Y-%m-%d %H:%M:%S')}
处理耗时: {results['duration']}

项目信息:
- SonarQube项目: {results.get('project_key', 'N/A')}
- GitLab仓库: {results.get('repository_url', 'N/A')}
- 本地路径: {results.get('local_repo_path', 'N/A')}

处理结果:
- 发现Critical问题: {results['sonar_issues_count']} 个
- 成功修复问题: {results['fixes_applied']} 个
- 创建Jira任务: {results['jira_tasks_created']} 个
- 处理状态: {'成功' if results['success'] else '失败'}

Git操作结果:
- 创建分支: {results.get('branch_name', 'N/A')}
- Merge Request: {results.get('merge_request_url', 'N/A')}

修复详情:
"""
        
        if fixes:
            for i, fix in enumerate(fixes, 1):
                issue = fix['issue']
                # 计算相对路径
                local_repo_path = results.get('local_repo_path', '')
                if local_repo_path and 'file_path' in fix:
                    relative_path = os.path.relpath(fix['file_path'], local_repo_path)
                else:
                    relative_path = fix.get('file_path', 'N/A')
                
                report_content += f"""
{i}. 问题: {issue.key}
   文件: {relative_path}:{issue.line or 'N/A'}
   规则: {issue.rule}
   类型: {issue.type}
   描述: {issue.message}
   
   修复差异:
{fix['diff']}
   
   ---
"""
        
        if results['errors']:
            report_content += f"\n错误信息:\n"
            for error in results['errors']:
                report_content += f"- {error}\n"
        
        # 保存报告
        report_filename = f'sonar_autofix_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"报告已保存到: {report_filename}")
        
        # 显示摘要
        print(f"\n{'='*50}")
        print("🔧 SonarQube自动修复完成")
        print(f"{'='*50}")
        print(f"发现问题: {results['sonar_issues_count']} 个")
        print(f"成功修复: {results['fixes_applied']} 个")
        if git_result.get('branch_name'):
            print(f"Git分支: {git_result['branch_name']}")
        if git_result.get('merge_request_url'):
            print(f"Merge Request: {git_result['merge_request_url']}")
        print(f"详细报告: {report_filename}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='SonarQube Critical问题自动修复工具')
    parser.add_argument('--project-key', '-p', type=str,
                       help='指定SonarQube项目Key（可选，不指定则批量处理所有项目）')
    parser.add_argument('--batch', '-b', action='store_true',
                       help='强制批量处理模式（即使指定了project-key）')
    parser.add_argument('--with-jira', action='store_true', 
                       help='同时创建Jira任务')
    parser.add_argument('--test-only', action='store_true',
                       help='仅测试连接，不执行修复')
    
    args = parser.parse_args()
    
    logger.info("SonarQube自动修复程序启动")
    
    try:
        processor = SonarAutoFixProcessor()
        
        # 测试连接
        if not processor.test_all_connections():
            logger.error("连接测试失败，程序退出")
            sys.exit(1)
        
        if args.test_only:
            logger.info("连接测试完成，程序退出")
            return
        
        # 执行自动修复
        if args.batch:
            # 强制批量处理模式
            logger.info("强制批量处理模式")
            results = processor.process_batch_auto_fix(create_jira_tasks=args.with_jira)
            
            # 输出批量处理结果摘要
            if results['success']:
                logger.info("批量自动修复流程完成！")
            else:
                logger.error("批量自动修复流程失败")
            
            logger.info(f"处理项目: {results['successful_projects']}/{results['total_projects']} 个成功")
            logger.info(f"发现Critical问题: {results['total_issues']} 个")
            logger.info(f"成功修复问题: {results['total_fixes_applied']} 个")
            logger.info(f"处理耗时: {results['duration']}")
            
            if results['errors']:
                logger.error(f"处理过程中发生 {len(results['errors'])} 个错误")
                for error in results['errors']:
                    logger.error(f"  - {error}")
                sys.exit(1)
        else:
            # 单项目或自动批量处理模式
            results = processor.process_auto_fix(
                project_key=args.project_key,
                create_jira_tasks=args.with_jira
            )
            
            # 检查是否是批量处理结果
            if 'total_projects' in results:
                # 批量处理结果
                if results['success']:
                    logger.info("批量自动修复流程完成！")
                else:
                    logger.error("批量自动修复流程失败")
                
                logger.info(f"处理项目: {results['successful_projects']}/{results['total_projects']} 个成功")
                logger.info(f"发现Critical问题: {results['total_issues']} 个")
                logger.info(f"成功修复问题: {results['total_fixes_applied']} 个")
                logger.info(f"处理耗时: {results['duration']}")
            else:
                # 单项目处理结果
                if results['success']:
                    logger.info("自动修复流程完成！")
                    if results.get('merge_request_url'):
                        logger.info(f"Merge Request: {results['merge_request_url']}")
                else:
                    logger.error("自动修复流程失败")
                    
                logger.info(f"项目: {results.get('project_key', 'N/A')}")
                logger.info(f"发现Critical问题: {results.get('sonar_issues_count', 0)} 个")
                logger.info(f"成功修复问题: {results.get('fixes_applied', 0)} 个")
                logger.info(f"处理耗时: {results.get('duration', 'N/A')}")
            
            if results.get('errors'):
                logger.error(f"处理过程中发生 {len(results['errors'])} 个错误")
                for error in results['errors']:
                    logger.error(f"  - {error}")
                sys.exit(1)
        
    except KeyboardInterrupt:
        logger.info("用户中断程序")
        sys.exit(0)
    except Exception as e:
        logger.error(f"程序异常退出: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
