#!/usr/bin/env python3
"""
SonarQube Critical Issues Auto-Fix
自动修复SonarQube Critical问题并创建Merge Request
"""

import logging
import sys
from datetime import datetime
from typing import List, Dict, Any

from .config import Config
from ..clients.sonarqube_client import SonarQubeClient
from ..clients.jira_client import JiraClient
from ..clients.ai_client import CodeFixer
from ..utils.git_manager import AutoFixProcessor
from .project_discovery import ProjectDiscovery
from .models import SonarIssue

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
        self.auto_fix_processor = AutoFixProcessor()
        
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
    
    def process_auto_fix(self, create_jira_tasks: bool = True) -> Dict[str, Any]:
        """自动修复流程"""
        logger.info("开始SonarQube Critical问题自动修复流程...")
        
        results = {
            'start_time': datetime.now(),
            'sonar_issues_count': 0,
            'fixes_applied': 0,
            'jira_tasks_created': 0,
            'merge_request_url': None,
            'branch_name': None,
            'errors': [],
            'success': False,
            'project_mapping': None
        }
        
        try:
            # 1. 自动发现和匹配项目
            logger.info("自动发现和匹配项目...")
            project_mapping = self.project_discovery.get_best_project_mapping(Config.GIT_REMOTE_URL)
            
            if not project_mapping:
                error_msg = "未找到匹配的SonarQube和Jira项目，请检查项目配置"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                return results
            
            results['project_mapping'] = {
                'sonar_project': f"{project_mapping.sonar_name} ({project_mapping.sonar_key})",
                'jira_project': f"{project_mapping.jira_name} ({project_mapping.jira_key})",
                'similarity_score': project_mapping.similarity_score,
                'mapping_reason': project_mapping.mapping_reason
            }
            
            logger.info(f"发现项目匹配: {project_mapping.sonar_name} <-> {project_mapping.jira_name}")
            
            # 2. 获取SonarQube Critical问题
            logger.info(f"从项目 {project_mapping.sonar_key} 获取Critical问题...")
            sonar_issues = self.sonar_client.get_critical_issues(project_mapping.sonar_key)
            results['sonar_issues_count'] = len(sonar_issues)
            
            if not sonar_issues:
                logger.info("没有发现Critical问题")
                results['success'] = True
                return results
            
            logger.info(f"发现 {len(sonar_issues)} 个Critical问题")
            
            # 3. 使用AI修复代码问题
            logger.info("开始AI自动修复...")
            fixes = self.code_fixer.fix_multiple_issues(
                sonar_issues, 
                Config.GIT_REPOSITORY_PATH
            )
            
            if not fixes:
                logger.warning("没有生成任何修复")
                return results
            
            logger.info(f"成功生成 {len(fixes)} 个修复")
            results['fixes_applied'] = len(fixes)
            
            # 4. 应用修复并创建Merge Request
            logger.info("应用修复并推送到Git...")
            git_result = self.auto_fix_processor.process_fixes(fixes, sonar_issues)
            
            if git_result['success']:
                results['success'] = True
                results['branch_name'] = git_result['branch_name']
                results['merge_request_url'] = git_result['merge_request_url']
                logger.info(f"修复推送成功，分支: {git_result['branch_name']}")
                
                if git_result['merge_request_url']:
                    logger.info(f"Merge Request创建成功: {git_result['merge_request_url']}")
            else:
                logger.error(f"Git操作失败: {git_result['message']}")
                results['errors'].append(git_result['message'])
            
            # 5. 可选：在Jira中创建任务
            if create_jira_tasks:
                logger.info("在Jira中创建任务...")
                created_tasks = self.jira_client.create_issues_from_sonar(
                    sonar_issues, 
                    project_mapping.jira_key
                )
                results['jira_tasks_created'] = len(created_tasks)
            
            # 6. 生成详细报告
            self._generate_auto_fix_report(sonar_issues, fixes, git_result, results)
            
        except Exception as e:
            error_msg = f"自动修复流程中发生错误: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
        
        finally:
            results['end_time'] = datetime.now()
            results['duration'] = results['end_time'] - results['start_time']
        
        return results
    
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

项目匹配信息:
- SonarQube项目: {results.get('project_mapping', {}).get('sonar_project', 'N/A')}
- Jira项目: {results.get('project_mapping', {}).get('jira_project', 'N/A')}
- 匹配相似度: {results.get('project_mapping', {}).get('similarity_score', 0):.2f}
- 匹配原因: {results.get('project_mapping', {}).get('mapping_reason', 'N/A')}

Git仓库: {Config.GIT_REPOSITORY_PATH}

处理结果:
- 发现Critical问题: {results['sonar_issues_count']} 个
- 成功修复问题: {results['fixes_applied']} 个
- 创建Jira任务: {results['jira_tasks_created']} 个
- 处理状态: {'成功' if results['success'] else '失败'}

Git操作结果:
- 创建分支: {git_result.get('branch_name', 'N/A')}
- 修改文件数: {len(git_result.get('modified_files', []))}
- Merge Request: {git_result.get('merge_request_url', 'N/A')}

修复详情:
"""
        
        if fixes:
            for i, fix in enumerate(fixes, 1):
                issue = fix['issue']
                relative_path = fix['file_path'].replace(Config.GIT_REPOSITORY_PATH, '').lstrip('\\/')
                
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
    parser.add_argument('--no-jira', action='store_true', 
                       help='跳过创建Jira任务')
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
        create_jira = not args.no_jira
        results = processor.process_auto_fix(create_jira_tasks=create_jira)
        
        # 输出结果摘要
        if results['success']:
            logger.info("自动修复流程完成！")
            if results['merge_request_url']:
                logger.info(f"Merge Request: {results['merge_request_url']}")
        else:
            logger.error("自动修复流程失败")
            
        logger.info(f"发现Critical问题: {results['sonar_issues_count']} 个")
        logger.info(f"成功修复问题: {results['fixes_applied']} 个")
        logger.info(f"处理耗时: {results['duration']}")
        
        if results['errors']:
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
