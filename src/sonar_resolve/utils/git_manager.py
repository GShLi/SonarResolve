"""
Git 管理器
增强版本，支持自动发现GitLab仓库并执行git pull
"""

import os
import logging
import subprocess
import shutil
import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlparse, urlunparse

try:
    import gitlab
    GITLAB_AVAILABLE = True
except ImportError:
    GITLAB_AVAILABLE = False
    logging.warning("GitLab库未安装，某些功能将不可用")

from ..core.config import Config

logger = logging.getLogger(__name__)

class GitRepositoryManager:
    """Git仓库管理器 - 自动发现和管理仓库"""
    
    def __init__(self):
        """初始化Git仓库管理器"""
        self.gitlab_url = Config.GITLAB_URL
        self.gitlab_token = Config.GITLAB_TOKEN
        self.local_workspace = Config.LOCAL_WORKSPACE
        
        # 确保本地工作目录存在
        Path(self.local_workspace).mkdir(parents=True, exist_ok=True)
        
        # 初始化GitLab客户端
        if GITLAB_AVAILABLE and self.gitlab_token:
            try:
                self.gitlab_client = gitlab.Gitlab(self.gitlab_url, private_token=self.gitlab_token)
                # 测试连接
                self.gitlab_client.auth()
                logger.info("GitLab客户端初始化成功")
            except Exception as e:
                logger.error(f"GitLab客户端初始化失败: {e}")
                self.gitlab_client = None
        else:
            logger.warning("GitLab token未配置或库未安装，将无法访问私有仓库")
            self.gitlab_client = None
    
    def find_repository_by_project_name(self, project_name: str) -> Optional[Dict[str, Any]]:
        """根据项目名在GitLab中查找仓库"""
        if not self.gitlab_client:
            logger.error("GitLab客户端未初始化")
            return None
        
        try:
            logger.info(f"在GitLab中搜索项目: {project_name}")
            
            # 搜索项目
            projects = self.gitlab_client.projects.list(search=project_name, all=True)
            
            if not projects:
                logger.warning(f"未找到匹配的GitLab项目: {project_name}")
                return None
            
            # 寻找最佳匹配
            best_match = None
            for project in projects:
                # 优先选择名称完全匹配的项目
                if project.name.lower() == project_name.lower():
                    best_match = project
                    break
                # 或者路径名匹配
                if project.path.lower() == project_name.lower():
                    best_match = project
                    break
                # 或者包含项目名的
                if project_name.lower() in project.name.lower():
                    if not best_match:
                        best_match = project
            
            if not best_match:
                best_match = projects[0]  # 使用第一个匹配项
            
            repo_info = {
                'id': best_match.id,
                'name': best_match.name,
                'path': best_match.path,
                'namespace': best_match.namespace['full_path'],
                'clone_url': best_match.http_url_to_repo,
                'ssh_url': best_match.ssh_url_to_repo,
                'default_branch': best_match.default_branch,
                'full_path': best_match.path_with_namespace
            }
            
            logger.info(f"找到匹配的GitLab项目: {repo_info['full_path']}")
            return repo_info
            
        except Exception as e:
            logger.error(f"搜索GitLab项目失败: {e}")
            return None
    
    def get_local_repo_path(self, project_name: str) -> Path:
        """获取项目的本地仓库路径"""
        # 清理项目名，用作目录名
        clean_name = project_name.replace(' ', '-').replace('_', '-').lower()
        # 移除特殊字符
        import re
        clean_name = re.sub(r'[^\w\-]', '', clean_name)
        return Path(self.local_workspace) / clean_name
    
    def clone_or_update_repository(self, project_name: str) -> Tuple[bool, Optional[Path]]:
        """克隆或更新仓库到本地"""
        try:
            # 查找GitLab仓库
            repo_info = self.find_repository_by_project_name(project_name)
            if not repo_info:
                logger.error(f"无法找到项目的GitLab仓库: {project_name}")
                return False, None
            
            local_repo_path = self.get_local_repo_path(project_name)
            clone_url = repo_info['clone_url']
            
            # 如果token存在，在URL中添加认证
            if self.gitlab_token:
                clone_url = self._add_auth_to_url(clone_url, self.gitlab_token)
            
            # 检查本地仓库是否存在
            if local_repo_path.exists() and (local_repo_path / '.git').exists():
                logger.info(f"本地仓库已存在，执行git pull: {local_repo_path}")
                return self._git_pull(local_repo_path, repo_info['default_branch'])
            else:
                logger.info(f"克隆仓库到本地: {repo_info['full_path']} -> {local_repo_path}")
                return self._git_clone(clone_url, local_repo_path, repo_info['default_branch'])
                
        except Exception as e:
            logger.error(f"克隆或更新仓库失败: {e}")
            return False, None
    
    def _add_auth_to_url(self, url: str, token: str) -> str:
        """为URL添加认证信息"""
        try:
            parsed = urlparse(url)
            auth_url = urlunparse((
                parsed.scheme,
                f"oauth2:{token}@{parsed.netloc}",
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))
            return auth_url
        except Exception as e:
            logger.error(f"添加认证信息失败: {e}")
            return url
    
    def _git_clone(self, clone_url: str, local_path: Path, default_branch: str) -> Tuple[bool, Optional[Path]]:
        """执行git clone"""
        try:
            # 确保父目录存在
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 如果目录已存在但不是git仓库，删除它
            if local_path.exists():
                if not (local_path / '.git').exists():
                    shutil.rmtree(local_path)
                else:
                    logger.info(f"目录已存在且是git仓库: {local_path}")
                    return True, local_path
            
            # 执行git clone
            cmd = ['git', 'clone', '--branch', default_branch, clone_url, str(local_path)]
            logger.info(f"执行: git clone --branch {default_branch} [URL] {local_path}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info(f"仓库克隆成功: {local_path}")
                return True, local_path
            else:
                logger.error(f"Git clone失败: {result.stderr}")
                return False, None
                
        except subprocess.TimeoutExpired:
            logger.error("Git clone超时")
            return False, None
        except Exception as e:
            logger.error(f"Git clone异常: {e}")
            return False, None
    
    def _git_pull(self, repo_path: Path, default_branch: str) -> Tuple[bool, Optional[Path]]:
        """执行git pull"""
        try:
            # 切换到仓库目录
            original_cwd = os.getcwd()
            os.chdir(repo_path)
            
            try:
                # 首先检查当前分支
                result = subprocess.run(['git', 'branch', '--show-current'], 
                                      capture_output=True, text=True, timeout=30)
                current_branch = result.stdout.strip()
                logger.info(f"当前分支: {current_branch}")
                
                # 如果不在默认分支，先切换
                if current_branch != default_branch:
                    logger.info(f"切换到默认分支: {default_branch}")
                    result = subprocess.run(['git', 'checkout', default_branch], 
                                          capture_output=True, text=True, timeout=30)
                    if result.returncode != 0:
                        logger.warning(f"切换分支失败，继续在当前分支: {current_branch}")
                
                # 执行git pull
                logger.info(f"执行git pull: {repo_path}")
                result = subprocess.run(['git', 'pull'], capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    output = result.stdout.strip()
                    if "Already up to date" in output:
                        logger.info("代码已是最新")
                    else:
                        logger.info(f"Git pull成功: {output}")
                    return True, repo_path
                else:
                    logger.error(f"Git pull失败: {result.stderr}")
                    return False, None
                    
            finally:
                # 恢复原始工作目录
                os.chdir(original_cwd)
                
        except subprocess.TimeoutExpired:
            logger.error("Git pull超时")
            return False, None
        except Exception as e:
            logger.error(f"Git pull异常: {e}")
            return False, None
    
    def prepare_repository_for_project(self, project_name: str) -> Tuple[bool, Optional[Path], Optional[Dict[str, Any]]]:
        """为项目准备仓库（查找、克隆/更新）"""
        logger.info(f"为项目准备Git仓库: {project_name}")
        
        # 查找仓库信息
        repo_info = self.find_repository_by_project_name(project_name)
        if not repo_info:
            return False, None, None
        
        # 克隆或更新仓库
        success, local_path = self.clone_or_update_repository(project_name)
        
        if success and local_path:
            logger.info(f"仓库准备完成: {local_path}")
            return True, local_path, repo_info
        else:
            logger.error(f"仓库准备失败: {project_name}")
            return False, None, repo_info


class GitManager:
    """Git操作管理器 - 兼容性保持"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.repo_manager = GitRepositoryManager()
    
    def create_branch(self, branch_name: str) -> bool:
        """创建并切换到新分支"""
        try:
            original_cwd = os.getcwd()
            os.chdir(self.repo_path)
            
            try:
                # 创建并切换分支
                result = subprocess.run(['git', 'checkout', '-b', branch_name], 
                                      capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    logger.info(f"分支创建成功: {branch_name}")
                    return True
                else:
                    logger.error(f"创建分支失败: {result.stderr}")
                    return False
            finally:
                os.chdir(original_cwd)
                
        except Exception as e:
            logger.error(f"创建分支失败: {e}")
            return False
    
    def commit_changes(self, files: list, message: str) -> bool:
        """提交更改"""
        try:
            original_cwd = os.getcwd()
            os.chdir(self.repo_path)
            
            try:
                # 添加文件
                for file in files:
                    result = subprocess.run(['git', 'add', file], 
                                          capture_output=True, text=True, timeout=30)
                    if result.returncode != 0:
                        logger.error(f"添加文件失败 {file}: {result.stderr}")
                        return False
                
                # 提交
                result = subprocess.run(['git', 'commit', '-m', message], 
                                      capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    logger.info(f"提交成功: {message}")
                    return True
                else:
                    logger.error(f"提交失败: {result.stderr}")
                    return False
            finally:
                os.chdir(original_cwd)
                
        except Exception as e:
            logger.error(f"提交更改失败: {e}")
            return False
    
    def push_branch(self, branch_name: str) -> bool:
        """推送分支到远程"""
        try:
            original_cwd = os.getcwd()
            os.chdir(self.repo_path)
            
            try:
                result = subprocess.run(['git', 'push', '-u', 'origin', branch_name], 
                                      capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    logger.info(f"分支推送成功: {branch_name}")
                    return True
                else:
                    logger.error(f"推送分支失败: {result.stderr}")
                    return False
            finally:
                os.chdir(original_cwd)
                
        except Exception as e:
            logger.error(f"推送分支失败: {e}")
            return False


class AutoFixProcessor:
    """自动修复处理器"""
    
    def __init__(self):
        self.repo_manager = GitRepositoryManager()
    
    def process_project_fixes(self, project_name: str, fixes: list) -> bool:
        """处理项目的自动修复"""
        # 准备仓库
        success, local_path, repo_info = self.repo_manager.prepare_repository_for_project(project_name)
        
        if not success:
            logger.error(f"无法准备项目仓库: {project_name}")
            return False
        
        # 使用本地路径进行后续的修复操作
        git_manager = GitManager(str(local_path))
        
        # 创建修复分支
        branch_name = f"fix/sonar-issues-{int(time.time())}"
        if not git_manager.create_branch(branch_name):
            logger.error("创建修复分支失败")
            return False
        
        # 应用修复
        modified_files = []
        for fix in fixes:
            file_path = local_path / fix['file_path']
            if self._apply_fix(file_path, fix):
                modified_files.append(fix['file_path'])
        
        if not modified_files:
            logger.warning("没有文件被修改")
            return False
        
        # 提交更改
        commit_message = f"自动修复SonarQube Critical问题\n\n修复的文件:\n" + "\n".join(f"- {f}" for f in modified_files)
        
        if not git_manager.commit_changes(modified_files, commit_message):
            logger.error("提交更改失败")
            return False
        
        # 推送分支
        if not git_manager.push_branch(branch_name):
            logger.error("推送分支失败")
            return False
        
        logger.info(f"自动修复完成，分支: {branch_name}")
        return True
    
    def _apply_fix(self, file_path: Path, fix: dict) -> bool:
        """应用单个修复"""
        try:
            if not file_path.exists():
                logger.error(f"文件不存在: {file_path}")
                return False
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 应用修复
            if fix.get('old_code') and fix.get('new_code'):
                content = content.replace(fix['old_code'], fix['new_code'])
            
            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"应用修复成功: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"应用修复失败 {file_path}: {e}")
            return False


class GitLabManager:
    """GitLab Merge Request管理器"""
    
    def __init__(self, project_id: str = None):
        self.project_id = project_id
        self.gitlab_url = Config.GITLAB_URL
        self.gitlab_token = Config.GITLAB_TOKEN
        
        if GITLAB_AVAILABLE and self.gitlab_token:
            try:
                self.gitlab_client = gitlab.Gitlab(self.gitlab_url, private_token=self.gitlab_token)
                self.gitlab_client.auth()
            except Exception as e:
                logger.error(f"GitLab客户端初始化失败: {e}")
                raise ValueError(f"GitLab初始化失败: {e}")
        else:
            raise ValueError("GitLab token未配置或库未安装")
    
    def create_merge_request(self, project_id: str, source_branch: str, target_branch: str = 'main', 
                           title: str = None, description: str = None) -> Optional[Dict[str, Any]]:
        """创建Merge Request"""
        try:
            project = self.gitlab_client.projects.get(project_id)
            
            mr_data = {
                'source_branch': source_branch,
                'target_branch': target_branch,
                'title': title or f"自动修复: {source_branch}",
                'description': description or "SonarQube Critical问题自动修复"
            }
            
            mr = project.mergerequests.create(mr_data)
            
            logger.info(f"Merge Request创建成功: {mr.web_url}")
            return {
                'id': mr.iid,
                'url': mr.web_url,
                'title': mr.title
            }
            
        except Exception as e:
            logger.error(f"创建Merge Request失败: {e}")
            return None
