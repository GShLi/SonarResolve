"""
Git 管理器
增强版本，支持自动发现GitLab仓库并执行git pull
"""

import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse, urlunparse

from sonar_tools.core.config import Config

logger = Config.setup_logging(__name__)

try:
    import gitlab

    GITLAB_AVAILABLE = True
except ImportError:
    GITLAB_AVAILABLE = False
    logger.warning("GitLab库未安装，某些功能将不可用")

try:
    import git
    from git import Repo

    GITPYTHON_AVAILABLE = True
except ImportError:
    GITPYTHON_AVAILABLE = False
    logger.warning("GitPython库未安装，某些功能将不可用")


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
            logger.info(
                f"执行GitPython clone --branch {default_branch} [URL] {local_path}"
            )

            repo = Repo.clone_from(
                url=clone_url,
                to_path=str(local_path),
                branch=default_branch,
                depth=1,  # 浅克隆，只获取最新提交，提高性能
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
                            repo.create_head(
                                default_branch, repo.refs[f"origin/{default_branch}"]
                            )
                            repo.heads[default_branch].set_tracking_branch(
                                repo.refs[f"origin/{default_branch}"]
                            )
                            repo.heads[default_branch].checkout()
                        else:
                            logger.error(f"远程分支 origin/{default_branch} 不存在")
                            return False, None

                except Exception as e:
                    logger.warning(
                        f"切换分支失败，继续在当前分支: {current_branch}, 错误: {e}"
                    )

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
                commits_behind = list(
                    repo.iter_commits(f"{active_branch}..{tracking_branch}")
                )
                commits_ahead = list(
                    repo.iter_commits(f"{tracking_branch}..{active_branch}")
                )

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
                        logger.info(
                            f"Git pull成功，合并了 {len(commits_behind)} 个提交"
                        )
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

    def create_branch(self, repo_path: Path, branch_name: str) -> bool:
        """创建并切换到新分支"""
        if not GITPYTHON_AVAILABLE:
            logger.error("GitPython库不可用，无法创建分支")
            return False

        try:
            repo = Repo(repo_path)

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

    def commit_changes(self, repo_path: Path, files: list, message: str) -> bool:
        """提交更改"""
        if not GITPYTHON_AVAILABLE:
            logger.error("GitPython库不可用，无法提交更改")
            return False

        try:
            repo = Repo(repo_path)

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

    def push_branch(self, repo_path: Path, branch_name: str) -> bool:
        """推送分支到远程"""
        if not GITPYTHON_AVAILABLE:
            logger.error("GitPython库不可用，无法推送分支")
            return False

        try:
            repo = Repo(repo_path)

            if not repo.remotes:
                logger.error("没有配置远程仓库")
                return False

            origin = repo.remotes.origin

            # 推送分支到远程，并设置跟踪
            push_info = origin.push(
                f"refs/heads/{branch_name}:refs/heads/{branch_name}"
            )

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

    def checkout_branch(self, repo_path: Path, branch_name: str) -> bool:
        """
        切换到指定分支

        Args:
            repo_path: 仓库路径
            branch_name: 分支名称

        Returns:
            切换是否成功
        """
        try:
            if not GITPYTHON_AVAILABLE:
                logger.error("GitPython库未安装，无法切换分支")
                return False

            repo = Repo(repo_path)

            # 检查是否已在目标分支上
            if repo.active_branch.name == branch_name:
                logger.debug(f"已在目标分支上: {branch_name}")
                return True

            # 检查分支是否存在于本地
            if branch_name in repo.heads:
                # 本地分支存在，直接切换
                repo.heads[branch_name].checkout()
                logger.info(f"切换到本地分支: {branch_name}")
            else:
                # 检查远程分支是否存在
                remote_branch = f"origin/{branch_name}"
                if remote_branch in repo.refs:
                    # 从远程分支创建本地分支
                    repo.git.checkout("-b", branch_name, remote_branch)
                    logger.info(f"从远程分支创建并切换到: {branch_name}")
                else:
                    logger.error(f"分支不存在: {branch_name}")
                    return False

            return True

        except git.exc.GitCommandError as e:
            logger.error(f"切换分支失败: {e}")
            return False
        except Exception as e:
            logger.error(f"切换分支异常: {e}")
            return False

    def pull_latest(self, repo_path: Path) -> bool:
        """
        拉取当前分支的最新代码

        Args:
            repo_path: 仓库路径

        Returns:
            拉取是否成功
        """
        try:
            if not GITPYTHON_AVAILABLE:
                logger.error("GitPython库未安装，无法拉取代码")
                return False

            repo = Repo(repo_path)
            origin = repo.remotes.origin

            # 拉取最新代码
            pull_info = origin.pull()

            for info in pull_info:
                if info.flags & info.ERROR:
                    logger.error(f"拉取代码失败: {info.note}")
                    return False
                elif info.flags & info.UP_TO_DATE:
                    logger.info("代码已是最新")
                elif info.flags & (info.NEW_TAG | info.NEW_HEAD | info.FAST_FORWARD):
                    logger.info("成功拉取最新代码")

            return True

        except git.exc.GitCommandError as e:
            logger.error(f"拉取代码失败: {e}")
            return False
        except Exception as e:
            logger.error(f"拉取代码异常: {e}")
            return False

    def delete_branch(self, repo_path: Path, branch_name: str) -> bool:
        """
        删除本地分支

        Args:
            repo_path: 仓库路径
            branch_name: 分支名称

        Returns:
            删除是否成功
        """
        try:
            if not GITPYTHON_AVAILABLE:
                logger.warning("GitPython库未安装，无法删除分支")
                return False

            repo = Repo(repo_path)

            # 检查分支是否存在
            if branch_name not in repo.heads:
                logger.warning(f"分支不存在，无需删除: {branch_name}")
                return True

            # 确保不在要删除的分支上
            if repo.active_branch.name == branch_name:
                # 切换到默认分支
                default_branch = "main" if "main" in repo.heads else "master"
                if default_branch in repo.heads:
                    repo.heads[default_branch].checkout()
                    logger.info(f"切换到 {default_branch} 分支以删除 {branch_name}")
                else:
                    logger.error("无法找到默认分支进行切换")
                    return False

            # 删除分支
            repo.delete_head(branch_name, force=True)
            logger.info(f"成功删除分支: {branch_name}")
            return True

        except git.exc.GitCommandError as e:
            logger.error(f"删除分支失败: {e}")
            return False
        except Exception as e:
            logger.error(f"删除分支异常: {e}")
            return False


class GitLabClient:
    """GitLab Merge Request管理器"""

    def __init__(self):
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

    def get_merge_request_status(self, mr_url: str) -> Optional[Dict[str, Any]]:
        """
        获取Merge Request状态

        Args:
            mr_url: MR的URL

        Returns:
            MR状态信息，包含状态、title等
        """
        try:
            # 从URL中提取项目ID和MR IID
            # 格式通常是: https://gitlab.example.com/group/project/-/merge_requests/123
            parts = mr_url.split("/")
            if "merge_requests" not in parts:
                logger.error(f"无效的MR URL格式: {mr_url}")
                return None

            mr_iid = parts[-1]
            # 找到项目路径
            gitlab_base = f"{self.gitlab_url}/"
            if not mr_url.startswith(gitlab_base):
                logger.error(f"MR URL不属于当前GitLab实例: {mr_url}")
                return None

            # 提取项目路径
            relative_path = mr_url[len(gitlab_base) :]
            project_path = relative_path.split("/-/merge_requests/")[0]

            # 获取项目和MR
            project = self.gitlab_client.projects.get(project_path, lazy=True)
            mr = project.mergerequests.get(mr_iid)

            return {
                "mr_iid": mr.iid,
                "title": mr.title,
                "state": mr.state,  # opened, closed, merged
                "merge_status": getattr(mr, "merge_status", None),
                "source_branch": mr.source_branch,
                "target_branch": mr.target_branch,
                "web_url": mr.web_url,
                "created_at": mr.created_at,
                "updated_at": mr.updated_at,
                "merged_at": getattr(mr, "merged_at", None),
                "author": mr.author.get("name", "") if mr.author else "",
                "description": mr.description or "",
            }

        except Exception as e:
            logger.error(f"获取MR状态失败 {mr_url}: {e}")
            return None

    def batch_get_merge_request_status(
        self, mr_urls: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        批量获取MR状态

        Args:
            mr_urls: MR URL列表

        Returns:
            字典，key为MR URL，value为状态信息
        """
        results = {}

        for mr_url in mr_urls:
            try:
                status = self.get_merge_request_status(mr_url)
                if status:
                    results[mr_url] = status
                else:
                    logger.warning(f"无法获取MR状态: {mr_url}")

            except Exception as e:
                logger.error(f"获取MR状态异常 {mr_url}: {e}")

        logger.info(f"批量获取MR状态完成，成功获取 {len(results)}/{len(mr_urls)} 个")
        return results
