#!/usr/bin/env python3
"""
SonarQube Critical Issues to Jira Tasks
自动从SonarQube获取Critical问题并创建Jira任务
"""

import logging
import sys
from datetime import datetime
from typing import List, Dict, Any

from .config import Config
from ..clients.sonarqube_client import SonarQubeClient
from ..clients.jira_client import JiraClient
from .project_discovery import ProjectDiscovery
from .models import SonarIssue, JiraTask

# 配置日志
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'sonar_to_jira_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

logger = logging.getLogger(__name__)

class SonarToJiraProcessor:
    """SonarQube到Jira的处理器"""
    
    def __init__(self):
        # 验证配置
        try:
            Config.validate_config()
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
        
        # 初始化项目发现器
        self.project_discovery = ProjectDiscovery(self.sonar_client, self.jira_client)
    
    def test_connections(self) -> bool:
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
    
    def process_critical_issues(self) -> Dict[str, Any]:
        """处理Critical问题的主流程"""
        logger.info("开始处理SonarQube Critical问题...")
        
        results = {
            'start_time': datetime.now(),
            'sonar_issues_count': 0,
            'jira_tasks_created': 0,
            'errors': [],
            'created_tasks': [],
            'project_mapping': None
        }
        
        try:
            # 1. 自动发现和匹配项目
            logger.info("自动发现和匹配项目...")
            git_remote_url = getattr(Config, 'GIT_REMOTE_URL', None)
            project_mapping = self.project_discovery.get_best_project_mapping(git_remote_url)
            
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
            logger.info(f"匹配原因: {project_mapping.mapping_reason}")
            
            # 2. 获取SonarQube Critical问题
            logger.info(f"从项目 {project_mapping.sonar_key} 获取Critical问题...")
            sonar_issues = self.sonar_client.get_critical_issues(project_mapping.sonar_key)
            results['sonar_issues_count'] = len(sonar_issues)
            
            if not sonar_issues:
                logger.info("没有发现Critical问题")
                return results
            
            # 3. 在Jira中创建任务
            logger.info(f"为 {len(sonar_issues)} 个Critical问题创建Jira任务...")
            created_tasks = self.jira_client.create_issues_from_sonar(
                sonar_issues, 
                project_mapping.jira_key
            )
            
            results['jira_tasks_created'] = len(created_tasks)
            results['created_tasks'] = created_tasks
            
            # 4. 生成报告
            self._generate_report(sonar_issues, created_tasks, results)
            
        except Exception as e:
            error_msg = f"处理过程中发生错误: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
        
        finally:
            results['end_time'] = datetime.now()
            results['duration'] = results['end_time'] - results['start_time']
        
        return results
    
    def _generate_report(self, sonar_issues: List[SonarIssue], 
                        created_tasks: List[str], results: Dict[str, Any]):
        """生成处理报告"""
        logger.info("生成处理报告...")
        
        report_content = f"""
SonarQube到Jira任务创建报告
========================================

处理时间: {results['start_time'].strftime('%Y-%m-%d %H:%M:%S')}

项目匹配信息:
- SonarQube项目: {results.get('project_mapping', {}).get('sonar_project', 'N/A')}
- Jira项目: {results.get('project_mapping', {}).get('jira_project', 'N/A')}
- 匹配相似度: {results.get('project_mapping', {}).get('similarity_score', 0):.2f}
- 匹配原因: {results.get('project_mapping', {}).get('mapping_reason', 'N/A')}

处理结果:
- 发现Critical问题: {results['sonar_issues_count']} 个
- 创建Jira任务: {results['jira_tasks_created']} 个
- 跳过重复任务: {results['sonar_issues_count'] - results['jira_tasks_created']} 个

创建的Jira任务:
{chr(10).join([f"- {task}" for task in created_tasks])}

SonarQube问题详情:
"""
        
        for i, issue in enumerate(sonar_issues, 1):
            report_content += f"""
{i}. {issue.key}
   文件: {issue.get_location_info()}
   规则: {issue.rule}
   消息: {issue.message}
   类型: {issue.type}
"""
        
        # 保存报告
        report_filename = f'sonar_to_jira_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"报告已保存到: {report_filename}")
        print(f"\n报告预览:\n{report_content}")

def main():
    """主函数"""
    logger.info("SonarQube到Jira任务自动创建程序启动")
    
    try:
        processor = SonarToJiraProcessor()
        
        # 测试连接
        if not processor.test_connections():
            logger.error("连接测试失败，程序退出")
            sys.exit(1)
        
        # 处理Critical问题
        results = processor.process_critical_issues()
        
        # 输出结果摘要
        logger.info("处理完成！")
        logger.info(f"发现Critical问题: {results['sonar_issues_count']} 个")
        logger.info(f"创建Jira任务: {results['jira_tasks_created']} 个")
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
