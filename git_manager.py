import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from git import Repo, GitCommandError
import gitlab
from models import SonarIssue
from config import Config

logger = logging.getLogger(__name__)

class GitManager:
    """Git仓库管理器"""
    
    def __init__(self, repository_path: str):
        self.repository_path = repository_path
        
        try:
            self.repo = Repo(repository_path)
            logger.info(f"Git仓库初始化成功: {repository_path}")
        except Exception as e:
            logger.error(f"Git仓库初始化失败: {e}")
            raise
    
    def create_branch(self, branch_name: str, base_branch: str = "main") -> bool:
        """创建新分支"""
        try:
            # 确保在主分支上
            self.repo.git.checkout(base_branch)
            self.repo.git.pull()
            
            # 创建并切换到新分支
            self.repo.git.checkout('-b', branch_name)
            
            logger.info(f"创建分支成功: {branch_name}")
            return True
            
        except GitCommandError as e:
            logger.error(f"创建分支失败: {e}")
            return False
    
    def commit_changes(self, files: List[str], commit_message: str) -> bool:
        """提交更改"""
        try:
            # 添加文件到暂存区
            for file_path in files:
                self.repo.git.add(file_path)
            
            # 检查是否有更改
            if not self.repo.index.diff("HEAD"):
                logger.info("没有更改需要提交")
                return False
            
            # 提交更改
            self.repo.git.commit('-m', commit_message)
            
            logger.info(f"提交成功: {commit_message}")
            return True
            
        except GitCommandError as e:
            logger.error(f"提交失败: {e}")
            return False
    
    def push_branch(self, branch_name: str) -> bool:
        """推送分支到远程"""
        try:
            # 设置远程跟踪分支并推送
            self.repo.git.push('--set-upstream', 'origin', branch_name)
            
            logger.info(f"推送分支成功: {branch_name}")
            return True
            
        except GitCommandError as e:
            logger.error(f"推送分支失败: {e}")
            return False
    
    def apply_fixes(self, fixes: List[Dict[str, Any]]) -> List[str]:
        """应用修复到文件"""
        modified_files = []
        
        for fix in fixes:
            file_path = fix['file_path']
            fixed_content = fix['fixed_content']
            
            try:
                # 写入修复后的内容
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                
                modified_files.append(file_path)
                logger.info(f"应用修复: {file_path}")
                
            except Exception as e:
                logger.error(f"应用修复失败 {file_path}: {e}")
        
        return modified_files

class GitLabManager:
    """GitLab Merge Request管理器"""
    
    def __init__(self, url: str, token: str, project_id: str):
        try:
            self.gl = gitlab.Gitlab(url, private_token=token)
            self.project = self.gl.projects.get(project_id)
            logger.info(f"GitLab客户端初始化成功: {project_id}")
        except Exception as e:
            logger.error(f"GitLab客户端初始化失败: {e}")
            raise
    
    def create_merge_request(self, source_branch: str, target_branch: str = "main", 
                           title: str = None, description: str = None) -> Optional[str]:
        """创建Merge Request"""
        try:
            mr = self.project.mergerequests.create({
                'source_branch': source_branch,
                'target_branch': target_branch,
                'title': title or f"自动修复SonarQube Critical问题 - {source_branch}",
                'description': description or "自动生成的代码修复"
            })
            
            logger.info(f"Merge Request创建成功: {mr.web_url}")
            return mr.web_url
            
        except Exception as e:
            logger.error(f"创建Merge Request失败: {e}")
            return None

class AutoFixProcessor:
    """自动修复处理器"""
    
    def __init__(self):
        # 验证配置
        Config.validate_git_config()
        
        self.git_manager = GitManager(Config.GIT_REPOSITORY_PATH)
        
        if Config.GITLAB_URL and Config.GITLAB_TOKEN and Config.GITLAB_PROJECT_ID:
            self.gitlab_manager = GitLabManager(
                Config.GITLAB_URL,
                Config.GITLAB_TOKEN,
                Config.GITLAB_PROJECT_ID
            )
        else:
            self.gitlab_manager = None
            logger.warning("GitLab配置不完整，将跳过Merge Request创建")
    
    def process_fixes(self, fixes: List[Dict[str, Any]], issues: List[SonarIssue]) -> Dict[str, Any]:
        """处理自动修复流程"""
        if not fixes:
            logger.info("没有需要修复的问题")
            return {'success': False, 'message': '没有需要修复的问题'}
        
        # 生成分支名称
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        branch_name = f"sonar-fix-{timestamp}"
        
        try:
            # 1. 创建新分支
            if not self.git_manager.create_branch(branch_name):
                return {'success': False, 'message': '创建分支失败'}
            
            # 2. 应用修复
            modified_files = self.git_manager.apply_fixes(fixes)
            
            if not modified_files:
                return {'success': False, 'message': '没有文件被修改'}
            
            # 3. 生成提交信息
            commit_message = self._generate_commit_message(fixes, issues)
            
            # 4. 提交更改
            if not self.git_manager.commit_changes(modified_files, commit_message):
                return {'success': False, 'message': '提交更改失败'}
            
            # 5. 推送分支
            if not self.git_manager.push_branch(branch_name):
                return {'success': False, 'message': '推送分支失败'}
            
            # 6. 创建Merge Request
            mr_url = None
            if self.gitlab_manager:
                mr_title, mr_description = self._generate_mr_content(fixes, issues)
                mr_url = self.gitlab_manager.create_merge_request(
                    source_branch=branch_name,
                    title=mr_title,
                    description=mr_description
                )
            
            return {
                'success': True,
                'branch_name': branch_name,
                'modified_files': modified_files,
                'fixes_count': len(fixes),
                'merge_request_url': mr_url,
                'commit_message': commit_message
            }
            
        except Exception as e:
            logger.error(f"自动修复流程失败: {e}")
            return {'success': False, 'message': f'处理失败: {e}'}
    
    def _generate_commit_message(self, fixes: List[Dict[str, Any]], issues: List[SonarIssue]) -> str:
        """生成提交信息"""
        fixed_files = set(fix['file_path'] for fix in fixes)
        fixed_rules = set(fix['issue'].rule for fix in fixes)
        
        message = f"fix: 自动修复 {len(fixes)} 个SonarQube Critical问题\n\n"
        message += f"修复的文件 ({len(fixed_files)}):\n"
        
        for file_path in sorted(fixed_files):
            relative_path = os.path.relpath(file_path, Config.GIT_REPOSITORY_PATH)
            message += f"- {relative_path}\n"
        
        message += f"\n修复的规则 ({len(fixed_rules)}):\n"
        for rule in sorted(fixed_rules):
            message += f"- {rule}\n"
        
        message += f"\n详细信息:\n"
        for i, fix in enumerate(fixes, 1):
            issue = fix['issue']
            relative_path = os.path.relpath(fix['file_path'], Config.GIT_REPOSITORY_PATH)
            message += f"{i}. {issue.rule} - {relative_path}\n"
            message += f"   {issue.message}\n"
        
        return message
    
    def _generate_mr_content(self, fixes: List[Dict[str, Any]], issues: List[SonarIssue]) -> tuple:
        """生成Merge Request标题和描述"""
        title = f"🔧 自动修复 {len(fixes)} 个SonarQube Critical问题"
        
        description = f"""## 📋 修复摘要

本次自动修复解决了 **{len(fixes)}** 个SonarQube Critical级别的问题。

### 📊 修复统计
- 修复问题数量: {len(fixes)}
- 影响文件数量: {len(set(fix['file_path'] for fix in fixes))}
- 修复规则数量: {len(set(fix['issue'].rule for fix in fixes))}

### 📁 修复的文件
"""
        
        fixed_files = set(fix['file_path'] for fix in fixes)
        for file_path in sorted(fixed_files):
            relative_path = os.path.relpath(file_path, Config.GIT_REPOSITORY_PATH)
            description += f"- `{relative_path}`\n"
        
        description += "\n### 🔧 修复的问题\n"
        
        for i, fix in enumerate(fixes, 1):
            issue = fix['issue']
            relative_path = os.path.relpath(fix['file_path'], Config.GIT_REPOSITORY_PATH)
            
            description += f"""
#### {i}. {issue.rule}
- **文件**: `{relative_path}:{issue.line or 'N/A'}`
- **类型**: {issue.type}
- **描述**: {issue.message}
- **SonarQube链接**: {issue.key}

**修复差异**:
```diff
{fix['diff']}
```
"""
        
        description += f"""
### ⚠️ 注意事项
- 本次修复由AI自动生成，建议进行代码审查
- 请确保修复后的代码通过单元测试
- 如有问题，请及时反馈

### 🔗 相关链接
- SonarQube项目: {Config.SONARQUBE_PROJECT_KEY}
- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return title, description
