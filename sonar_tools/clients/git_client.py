"""
Git 管理器
增强版本，支持自动发现GitLab仓库并执行git pull
"""

import logging
import os
import re
import shutil
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse, urlunparse

try:
    import gitlab

    GITLAB_AVAILABLE = True
except ImportError:
    GITLAB_AVAILABLE = False
    logging.warning("GitLab库未安装，某些功能将不可用")

try:
    import git
    from git import Repo
    GITPYTHON_AVAILABLE = True
except ImportError:
    GITPYTHON_AVAILABLE = False
    logging.warning("GitPython库未安装，某些功能将不可用")

from ..core.config import Config

logger = logging.getLogger(__name__)


class GitClient:
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
                self.gitlab_client = gitlab.Gitlab(
                    self.gitlab_url, private_token=self.gitlab_token
                )
                # 测试连接
                self.gitlab_client.auth()
                logger.info("GitLab客户端初始化成功")
            except Exception as e:
                logger.error(f"GitLab客户端初始化失败: {e}")
                self.gitlab_client = None
        else:
            logger.warning("GitLab token未配置或库未安装，将无法访问私有仓库")
            self.gitlab_client = None

    def find_repository_by_project_name(
        self, project_name: str
    ) -> Optional[Dict[str, Any]]:
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
                "id": best_match.id,
                "name": best_match.name,
                "path": best_match.path,
                "namespace": best_match.namespace["full_path"],
                "clone_url": best_match.http_url_to_repo,
                "ssh_url": best_match.ssh_url_to_repo,
                "default_branch": best_match.default_branch,
                "full_path": best_match.path_with_namespace,
            }

            logger.info(f"找到匹配的GitLab项目: {repo_info['full_path']}")
            return repo_info

        except Exception as e:
            logger.error(f"搜索GitLab项目失败: {e}")
            return None

    def get_local_repo_path(self, project_name: str) -> Path:
        """获取项目的本地仓库路径"""
        # 清理项目名，用作目录名
        clean_name = project_name.replace(" ", "-").replace("_", "-").lower()
        # 移除特殊字符
        clean_name = re.sub(r"[^\w\-]", "", clean_name)
        return Path(self.local_workspace) / clean_name

    def clone_or_update_repository(
        self, project_name: str
    ) -> Tuple[bool, Optional[Path]]:
        """克隆或更新仓库到本地"""
        try:
            # 查找GitLab仓库
            repo_info = self.find_repository_by_project_name(project_name)
            if not repo_info:
                logger.error(f"无法找到项目的GitLab仓库: {project_name}")
                return False, None

            local_repo_path = self.get_local_repo_path(project_name)
            clone_url = repo_info["clone_url"]

            # 如果token存在，在URL中添加认证
            if self.gitlab_token:
                clone_url = self._add_auth_to_url(clone_url, self.gitlab_token)

            # 检查本地仓库是否存在
            if local_repo_path.exists() and (local_repo_path / ".git").exists():
                logger.info(f"本地仓库已存在，执行git pull: {local_repo_path}")
                return self._git_pull(local_repo_path, repo_info["default_branch"])
            else:
                logger.info(
                    f"克隆仓库到本地: {repo_info['full_path']} -> {local_repo_path}"
                )
                return self._git_clone(
                    clone_url, local_repo_path, repo_info["default_branch"]
                )

        except Exception as e:
            logger.error(f"克隆或更新仓库失败: {e}")
            return False, None

    def _add_auth_to_url(self, url: str, token: str) -> str:
        """为URL添加认证信息"""
        try:
            parsed = urlparse(url)
            auth_url = urlunparse(
                (
                    parsed.scheme,
                    f"oauth2:{token}@{parsed.netloc}",
                    parsed.path,
                    parsed.params,
                    parsed.query,
                    parsed.fragment,
                )
            )
            return auth_url
        except Exception as e:
            logger.error(f"添加认证信息失败: {e}")
            return url

    def _git_clone(
        self, clone_url: str, local_path: Path, default_branch: str
    ) -> Tuple[bool, Optional[Path]]:
        """执行git clone - 使用GitPython库"""
        if not GITPYTHON_AVAILABLE:
            logger.error("GitPython库不可用，无法执行git clone")
            return False, None
            
        try:
            # 确保父目录存在
            local_path.parent.mkdir(parents=True, exist_ok=True)

            # 如果目录已存在但不是git仓库，删除它
            if local_path.exists():
                if not (local_path / ".git").exists():
                    shutil.rmtree(local_path)
                else:
                    logger.info(f"目录已存在且是git仓库: {local_path}")
                    return True, local_path

            # 使用GitPython执行clone
            logger.info(f"执行GitPython clone --branch {default_branch} [URL] {local_path}")
            
            repo = Repo.clone_from(
                url=clone_url,
                to_path=str(local_path),
                branch=default_branch,
                depth=1  # 浅克隆，只获取最新提交，提高性能
            )
            
            logger.info(f"仓库克隆成功: {local_path}")
            return True, local_path

        except git.exc.GitCommandError as e:
            logger.error(f"GitPython clone失败: {e}")
            return False, None
        except Exception as e:
            logger.error(f"Git clone异常: {e}")
            return False, None

    def _git_pull(
        self, repo_path: Path, default_branch: str
    ) -> Tuple[bool, Optional[Path]]:
        """执行git pull - 使用GitPython库"""
        if not GITPYTHON_AVAILABLE:
            logger.error("GitPython库不可用，无法执行git pull")
            return False, None
            
        try:
            # 使用GitPython打开仓库
            repo = Repo(repo_path)
            
            if repo.bare:
                logger.error(f"仓库是bare仓库: {repo_path}")
                return False, None
                
            # 检查当前分支
            current_branch = repo.active_branch.name
            logger.info(f"当前分支: {current_branch}")
            
            # 如果不在默认分支，先切换
            if current_branch != default_branch:
                logger.info(f"切换到默认分支: {default_branch}")
                try:
                    # 检查分支是否存在
                    if default_branch in repo.heads:
                        repo.heads[default_branch].checkout()
                    else:
                        # 创建并跟踪远程分支
                        if f"origin/{default_branch}" in repo.refs:
                            repo.create_head(default_branch, repo.refs[f"origin/{default_branch}"])
                            repo.heads[default_branch].set_tracking_branch(repo.refs[f"origin/{default_branch}"])
                            repo.heads[default_branch].checkout()
                        else:
                            logger.error(f"远程分支 origin/{default_branch} 不存在")
                            return False, None
                            
                except Exception as e:
                    logger.warning(f"切换分支失败，继续在当前分支: {current_branch}, 错误: {e}")
            
            # 执行git pull
            logger.info(f"执行git pull: {repo_path}")
            
            # 获取远程仓库引用
            if not repo.remotes:
                logger.error("没有配置远程仓库")
                return False, None
                
            origin = repo.remotes.origin
            
            # 首先fetch最新的远程内容
            logger.info("执行fetch操作...")
            fetch_info = origin.fetch()
            logger.debug(f"Fetch结果: {[str(info) for info in fetch_info]}")
            
            # 执行pull（实际上是merge）
            active_branch = repo.active_branch
            tracking_branch = active_branch.tracking_branch()
            
            if tracking_branch:
                # 检查是否需要更新
                commits_behind = list(repo.iter_commits(f'{active_branch}..{tracking_branch}'))
                commits_ahead = list(repo.iter_commits(f'{tracking_branch}..{active_branch}'))
                
                if not commits_behind and not commits_ahead:
                    logger.info("代码已是最新")
                    return True, repo_path
                elif commits_ahead and not commits_behind:
                    logger.info("本地分支领先于远程分支")
                    return True, repo_path
                elif commits_behind:
                    # 执行merge
                    try:
                        repo.git.merge(tracking_branch)
                        logger.info(f"Git pull成功，合并了 {len(commits_behind)} 个提交")
                        return True, repo_path
                    except git.exc.GitCommandError as e:
                        logger.error(f"Git merge失败: {e}")
                        return False, None
            else:
                logger.warning("当前分支没有设置跟踪分支")
                return False, None
                
        except git.exc.InvalidGitRepositoryError:
            logger.error(f"无效的Git仓库: {repo_path}")
            return False, None
        except git.exc.GitCommandError as e:
            logger.error(f"Git命令执行失败: {e}")
            return False, None
        except Exception as e:
            logger.error(f"Git pull异常: {e}")
            return False, None

    def prepare_repository_for_project(
        self, project_name: str
    ) -> Tuple[bool, Optional[Path], Optional[Dict[str, Any]]]:
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
    """Git操作管理器 - 使用GitPython库"""

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.repo_manager = GitClient()

    def create_branch(self, branch_name: str) -> bool:
        """创建并切换到新分支"""
        if not GITPYTHON_AVAILABLE:
            logger.error("GitPython库不可用，无法创建分支")
            return False
            
        try:
            repo = Repo(self.repo_path)
            
            # 检查分支是否已存在
            if branch_name in repo.heads:
                logger.info(f"分支已存在，切换到: {branch_name}")
                repo.heads[branch_name].checkout()
                return True
            
            # 创建并切换到新分支
            new_branch = repo.create_head(branch_name)
            new_branch.checkout()
            
            logger.info(f"分支创建成功: {branch_name}")
            return True
            
        except git.exc.GitCommandError as e:
            logger.error(f"GitPython创建分支失败: {e}")
            return False
        except Exception as e:
            logger.error(f"创建分支异常: {e}")
            return False

    def commit_changes(self, files: list, message: str) -> bool:
        """提交更改"""
        if not GITPYTHON_AVAILABLE:
            logger.error("GitPython库不可用，无法提交更改")
            return False
            
        try:
            repo = Repo(self.repo_path)
            
            # 添加文件到暂存区
            for file in files:
                try:
                    repo.index.add([file])
                    logger.debug(f"添加文件到暂存区: {file}")
                except Exception as e:
                    logger.error(f"添加文件失败 {file}: {e}")
                    return False
            
            # 检查是否有更改需要提交
            if not repo.index.diff("HEAD"):
                logger.warning("没有更改需要提交")
                return True
            
            # 提交更改
            commit = repo.index.commit(message)
            logger.info(f"提交成功: {message} (commit: {commit.hexsha[:8]})")
            return True
            
        except git.exc.GitCommandError as e:
            logger.error(f"GitPython提交失败: {e}")
            return False
        except Exception as e:
            logger.error(f"提交更改异常: {e}")
            return False

    def push_branch(self, branch_name: str) -> bool:
        """推送分支到远程"""
        if not GITPYTHON_AVAILABLE:
            logger.error("GitPython库不可用，无法推送分支")
            return False
            
        try:
            repo = Repo(self.repo_path)
            
            if not repo.remotes:
                logger.error("没有配置远程仓库")
                return False
                
            origin = repo.remotes.origin
            
            # 推送分支到远程，并设置跟踪
            push_info = origin.push(f"refs/heads/{branch_name}:refs/heads/{branch_name}")
            
            # 检查推送结果
            for info in push_info:
                if info.flags & info.ERROR:
                    logger.error(f"推送分支失败: {info.summary}")
                    return False
                elif info.flags & info.UP_TO_DATE:
                    logger.info(f"分支已是最新: {branch_name}")
                elif info.flags & (info.NEW_TAG | info.NEW_HEAD | info.FAST_FORWARD):
                    logger.info(f"分支推送成功: {branch_name}")
            
            # 设置本地分支跟踪远程分支
            if branch_name in repo.heads:
                local_branch = repo.heads[branch_name]
                remote_ref = f"origin/{branch_name}"
                if remote_ref in repo.refs:
                    local_branch.set_tracking_branch(repo.refs[remote_ref])
            
            return True
            
        except git.exc.GitCommandError as e:
            logger.error(f"GitPython推送分支失败: {e}")
            return False
        except Exception as e:
            logger.error(f"推送分支异常: {e}")
            return False


class AutoFixProcessor:
    """自动修复处理器"""

    def __init__(self):
        self.repo_manager = GitClient()

    def process_project_fixes(self, project_name: str, fixes: list) -> bool:
        """处理项目的自动修复"""
        # 准备仓库
        (
            success,
            local_path,
            repo_info,
        ) = self.repo_manager.prepare_repository_for_project(project_name)

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
            file_path = local_path / fix["file_path"]
            if self._apply_fix(file_path, fix):
                modified_files.append(fix["file_path"])

        if not modified_files:
            logger.warning("没有文件被修改")
            return False

        # 提交更改
        commit_message = "自动修复SonarQube Critical问题\n\n修复的文件:\n" + "\n".join(
            f"- {f}" for f in modified_files
        )

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
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 智能应用修复
            if self._apply_smart_fix(file_path, content, fix):
                logger.info(f"应用修复成功: {file_path}")
                return True
            else:
                logger.error(f"应用修复失败: {file_path}")
                return False

        except Exception as e:
            logger.error(f"应用修复失败 {file_path}: {e}")
            return False

    def _apply_smart_fix(self, file_path: Path, content: str, fix: dict) -> bool:
        """智能应用代码修复（支持AI应用和传统方法）"""
        try:
            # 获取修复信息
            fixed_code = fix.get("fixed_code", "").strip()
            if not fixed_code:
                logger.error("没有有效的修复代码")
                return False

            # 首先尝试AI智能应用（推荐方式）
            if self._try_ai_application(file_path, content, fix):
                return True
            
            logger.info("AI应用失败，回退到传统修复策略")
            
            # 回退到传统的多策略修复方法
            strategies = [
                self._apply_by_line_range,
                self._apply_by_pattern_match,
                self._apply_by_function_block,
                self._apply_full_replacement
            ]

            for strategy in strategies:
                try:
                    new_content = strategy(content, fix)
                    if new_content and new_content != content:
                        # 写回文件
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(new_content)
                        logger.info(f"使用策略 {strategy.__name__} 修复成功")
                        return True
                except Exception as e:
                    logger.debug(f"修复策略 {strategy.__name__} 失败: {e}")
                    continue

            logger.error("所有修复策略都失败了")
            return False

        except Exception as e:
            logger.error(f"智能修复失败: {e}")
            return False

    def _try_ai_application(self, file_path: Path, content: str, fix: dict) -> bool:
        """尝试使用AI智能应用修复"""
        try:
            # 检查是否启用AI应用
            from ..core.config import Config
            if not getattr(Config, 'AI_APPLY_FIXES', True):
                logger.debug("AI应用修复已禁用")
                return False
            
            # 导入AI客户端
            from .langchain_client import LangChainClient
            
            ai_client = LangChainClient()
            fixed_code = fix.get("fixed_code", "")
            
            # 构造问题数据
            issue_data = {
                "component": str(file_path),
                "line": fix.get("line", 0),
                "language": fix.get("language", self._detect_language(file_path)),
                "message": fix.get("message", "SonarQube Critical issue"),
                "code_snippet": fix.get("code_snippet", ""),
                "key": fix.get("key", f"issue_{file_path.name}")
            }
            
            # 使用AI应用修复
            result = ai_client.apply_code_fix(content, fixed_code, issue_data)
            
            if result.get("success") and result.get("modified_content"):
                confidence = result.get("confidence", 0)
                threshold = getattr(Config, 'AI_APPLY_CONFIDENCE_THRESHOLD', 7)
                
                if confidence >= threshold:  # 使用配置的信心阈值
                    # 写回文件
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(result["modified_content"])
                    
                    logger.info(f"AI应用修复成功 - 策略: {result.get('strategy_used')}, 信心: {confidence}/10")
                    if result.get("warnings"):
                        logger.warning(f"AI应用警告: {', '.join(result['warnings'])}")
                    
                    return True
                else:
                    logger.warning(f"AI应用信心不足: {confidence}/10 < {threshold}，使用传统方法")
                    return False
            else:
                logger.debug(f"AI应用失败: {result.get('changes_summary', 'Unknown reason')}")
                return False
                
        except ImportError:
            logger.debug("AI组件未可用，使用传统修复方法")
            return False
        except Exception as e:
            logger.debug(f"AI应用异常: {e}")
            return False

    def _detect_language(self, file_path: Path) -> str:
        """根据文件扩展名检测编程语言"""
        extension = file_path.suffix.lower()
        language_map = {
            '.py': 'python',
            '.java': 'java',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.cs': 'csharp',
            '.cpp': 'cpp',
            '.c': 'c',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.kt': 'kotlin',
            '.scala': 'scala'
        }
        return language_map.get(extension, 'unknown')

    def _apply_by_line_range(self, content: str, fix: dict) -> str:
        """基于行号范围的修复策略"""
        # 从fix信息中获取行号
        line_number = fix.get("line", 0)
        if not line_number:
            return None

        lines = content.split('\n')
        fixed_code = fix.get("fixed_code", "").strip()
        
        # 获取问题代码的上下文行数
        context_lines = 5
        start_line = max(0, line_number - context_lines - 1)
        end_line = min(len(lines), line_number + context_lines)
        
        # 清理fixed_code，移除行号标记
        clean_fixed_lines = []
        for line in fixed_code.split('\n'):
            # 移除行号前缀 (如 "  123: " 或 "→ 123: ")
            clean_line = re.sub(r'^[→\s]*\d+:\s*', '', line)
            clean_fixed_lines.append(clean_line)
        
        # 替换目标行及其上下文
        new_lines = lines[:start_line] + clean_fixed_lines + lines[end_line:]
        return '\n'.join(new_lines)

    def _apply_by_pattern_match(self, content: str, fix: dict) -> str:
        """基于模式匹配的修复策略"""
        # 从原始代码片段中提取关键模式
        code_snippet = fix.get("code_snippet", "")
        if not code_snippet:
            return None
            
        # 提取问题行的关键代码（去除行号和标记）
        pattern_lines = []
        for line in code_snippet.split('\n'):
            if '→' in line:  # 问题行
                clean_line = re.sub(r'^[→\s]*\d+:\s*', '', line).strip()
                if clean_line:
                    pattern_lines.append(clean_line)
        
        if not pattern_lines:
            return None
            
        # 在文件中查找匹配的代码行
        fixed_code = fix.get("fixed_code", "").strip()
        clean_fixed_lines = []
        for line in fixed_code.split('\n'):
            clean_line = re.sub(r'^[→\s]*\d+:\s*', '', line)
            clean_fixed_lines.append(clean_line)
        
        # 替换第一个匹配的模式
        for pattern in pattern_lines:
            if pattern in content:
                # 找到完整的行进行替换
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if pattern.strip() in line.strip():
                        # 替换这一行
                        if clean_fixed_lines:
                            lines[i] = clean_fixed_lines[0]  # 使用修复后的第一行
                            return '\n'.join(lines)
        
        return None

    def _apply_by_function_block(self, content: str, fix: dict) -> str:
        """基于函数块的修复策略"""
        # 获取行号和语言信息
        line_number = fix.get("line", 0)
        language = fix.get("language", "").lower()
        
        if not line_number:
            return None
            
        lines = content.split('\n')
        if line_number > len(lines):
            return None
            
        # 根据语言找到函数或方法边界
        function_start, function_end = self._find_function_boundaries(
            lines, line_number - 1, language
        )
        
        if function_start is None or function_end is None:
            return None
            
        # 获取修复后的代码
        fixed_code = fix.get("fixed_code", "").strip()
        clean_fixed_lines = []
        for line in fixed_code.split('\n'):
            clean_line = re.sub(r'^[→\s]*\d+:\s*', '', line)
            clean_fixed_lines.append(clean_line)
        
        # 替换函数块
        new_lines = (
            lines[:function_start] + 
            clean_fixed_lines + 
            lines[function_end + 1:]
        )
        
        return '\n'.join(new_lines)

    def _apply_full_replacement(self, content: str, fix: dict) -> str:
        """全文件替换策略（最后的备用策略）"""
        fixed_code = fix.get("fixed_code", "").strip()
        if not fixed_code:
            return None
            
        # 清理修复代码
        clean_lines = []
        for line in fixed_code.split('\n'):
            clean_line = re.sub(r'^[→\s]*\d+:\s*', '', line)
            clean_lines.append(clean_line)
        
        # 仅当修复代码看起来是完整文件时才使用
        fixed_content = '\n'.join(clean_lines)
        if len(fixed_content) > len(content) * 0.5:  # 至少是原文件的50%
            return fixed_content
            
        return None

    def _find_function_boundaries(self, lines: list, target_line: int, language: str) -> tuple:
        """查找函数边界"""
        if target_line < 0 or target_line >= len(lines):
            return None, None
            
        # 根据语言定义函数关键字
        function_keywords = {
            'python': ['def ', 'class ', 'async def '],
            'java': ['public ', 'private ', 'protected ', 'static '],
            'javascript': ['function ', 'const ', 'let ', 'var '],
            'typescript': ['function ', 'const ', 'let ', 'var ', 'export '],
            'csharp': ['public ', 'private ', 'protected ', 'internal '],
            'cpp': ['int ', 'void ', 'double ', 'float ', 'bool '],
        }
        
        keywords = function_keywords.get(language, ['def ', 'function '])
        
        # 向上查找函数开始
        function_start = None
        for i in range(target_line, -1, -1):
            line = lines[i].strip()
            if any(keyword in line for keyword in keywords):
                function_start = i
                break
                
        # 向下查找函数结束（简单的括号匹配）
        function_end = None
        if function_start is not None:
            brace_count = 0
            in_function = False
            
            for i in range(function_start, len(lines)):
                line = lines[i]
                if '{' in line:
                    brace_count += line.count('{')
                    in_function = True
                if '}' in line:
                    brace_count -= line.count('}')
                    
                if in_function and brace_count == 0:
                    function_end = i
                    break
                    
            # 对于Python等使用缩进的语言
            if function_end is None and language == 'python':
                base_indent = len(lines[function_start]) - len(lines[function_start].lstrip())
                for i in range(function_start + 1, len(lines)):
                    line = lines[i]
                    if line.strip() and len(line) - len(line.lstrip()) <= base_indent:
                        function_end = i - 1
                        break
                        
        return function_start, function_end


class GitLabManager:
    """GitLab Merge Request管理器"""

    def __init__(self, project_id: str = None):
        self.project_id = project_id
        self.gitlab_url = Config.GITLAB_URL
        self.gitlab_token = Config.GITLAB_TOKEN

        if GITLAB_AVAILABLE and self.gitlab_token:
            try:
                self.gitlab_client = gitlab.Gitlab(
                    self.gitlab_url, private_token=self.gitlab_token
                )
                self.gitlab_client.auth()
            except Exception as e:
                logger.error(f"GitLab客户端初始化失败: {e}")
                raise ValueError(f"GitLab初始化失败: {e}")
        else:
            raise ValueError("GitLab token未配置或库未安装")

    def create_merge_request(
        self,
        project_id: str,
        source_branch: str,
        target_branch: str = "main",
        title: str = None,
        description: str = None,
        labels: list = None,
    ) -> Optional[Dict[str, Any]]:
        """创建Merge Request"""
        try:
            project = self.gitlab_client.projects.get(project_id)

            mr_data = {
                "source_branch": source_branch,
                "target_branch": target_branch,
                "title": title or f"自动修复: {source_branch}",
                "description": description or "SonarQube Critical问题自动修复",
                "remove_source_branch": True,
            }

            # 添加标签支持
            if labels:
                mr_data["labels"] = labels

            mr = project.mergerequests.create(mr_data)

            logger.info(f"Merge Request创建成功: {mr.web_url}")
            return {"id": mr.iid, "url": mr.web_url, "title": mr.title}

        except Exception as e:
            logger.error(f"创建Merge Request失败: {e}")
            return None
