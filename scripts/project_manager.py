#!/usr/bin/env python3
"""
项目管理工具 - 列出和选择SonarQube和Jira项目
"""

import logging
import sys
from typing import Optional, Dict, Any
from pathlib import Path

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from sonar_resolve.core.config import Config
from sonar_resolve.clients.sonarqube_client import SonarQubeClient
from sonar_resolve.clients.jira_client import JiraClient
from sonar_resolve.core.project_discovery import ProjectDiscovery, ProjectMapping

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProjectManager:
    """项目管理器"""
    
    def __init__(self):
        try:
            Config.validate_config()
        except ValueError as e:
            logger.error(f"配置验证失败: {e}")
            sys.exit(1)
        
        self.sonar_client = SonarQubeClient(Config.SONARQUBE_URL, Config.SONARQUBE_TOKEN)
        self.jira_client = JiraClient(Config.JIRA_URL, Config.JIRA_EMAIL, Config.JIRA_API_TOKEN)
        self.project_discovery = ProjectDiscovery(self.sonar_client, self.jira_client)
    
    def list_all_projects(self):
        """列出所有项目"""
        print("📋 可用项目列表")
        print("=" * 50)
        
        try:
            projects = self.project_discovery.list_available_projects()
            
            print(f"\n🔍 SonarQube项目 ({len(projects['sonar_projects'])} 个):")
            print("-" * 30)
            for i, project in enumerate(projects['sonar_projects'], 1):
                print(f"{i:2d}. {project['name']}")
                print(f"    Key: {project['key']}")
                print()
            
            print(f"\n📊 Jira项目 ({len(projects['jira_projects'])} 个):")
            print("-" * 30)
            for i, project in enumerate(projects['jira_projects'], 1):
                print(f"{i:2d}. {project['name']}")
                print(f"    Key: {project['key']}")
                if project.get('description'):
                    print(f"    描述: {project['description'][:50]}...")
                if project.get('lead'):
                    print(f"    负责人: {project['lead']}")
                print()
                
        except Exception as e:
            logger.error(f"获取项目列表失败: {e}")
    
    def discover_project_mappings(self, git_url: str = None):
        """发现项目映射"""
        print("🔗 项目自动匹配结果")
        print("=" * 50)
        
        try:
            # 从配置获取Git URL
            if not git_url:
                git_url = getattr(Config, 'GIT_REMOTE_URL', None)
            
            if git_url:
                print(f"Git仓库: {git_url}")
            
            mappings = self.project_discovery.discover_projects(git_url)
            
            if not mappings:
                print("❌ 未找到任何项目匹配")
                return
            
            print(f"\n找到 {len(mappings)} 个可能的匹配:")
            print()
            
            for i, mapping in enumerate(mappings, 1):
                print(f"{i}. 匹配 #{i} (相似度: {mapping.similarity_score:.2f})")
                print(f"   SonarQube: {mapping.sonar_name} ({mapping.sonar_key})")
                print(f"   Jira:      {mapping.jira_name} ({mapping.jira_key})")
                print(f"   原因:      {mapping.mapping_reason}")
                
                if i == 1:
                    print("   ⭐ 推荐使用此匹配")
                print()
                
        except Exception as e:
            logger.error(f"项目匹配失败: {e}")
    
    def analyze_project_issues(self, sonar_project_key: str):
        """分析指定项目的问题"""
        print(f"📊 项目问题分析: {sonar_project_key}")
        print("=" * 50)
        
        try:
            # 获取项目信息
            project_info = self.sonar_client.get_project_info(sonar_project_key)
            print(f"项目名称: {project_info.get('name', 'N/A')}")
            print(f"项目键: {project_info.get('key', 'N/A')}")
            print()
            
            # 获取Critical问题
            issues = self.sonar_client.get_critical_issues(sonar_project_key)
            print(f"Critical问题总数: {len(issues)}")
            
            if issues:
                # 按类型分组
                issue_types = {}
                issue_rules = {}
                
                for issue in issues:
                    # 按类型统计
                    if issue.type not in issue_types:
                        issue_types[issue.type] = 0
                    issue_types[issue.type] += 1
                    
                    # 按规则统计
                    if issue.rule not in issue_rules:
                        issue_rules[issue.rule] = 0
                    issue_rules[issue.rule] += 1
                
                print("\n问题类型分布:")
                for issue_type, count in sorted(issue_types.items()):
                    print(f"  {issue_type}: {count} 个")
                
                print("\n最常见的规则 (Top 5):")
                sorted_rules = sorted(issue_rules.items(), key=lambda x: x[1], reverse=True)
                for rule, count in sorted_rules[:5]:
                    print(f"  {rule}: {count} 个")
                
                print("\n问题详情 (前5个):")
                for i, issue in enumerate(issues[:5], 1):
                    print(f"  {i}. {issue.key}")
                    print(f"     文件: {issue.get_location_info()}")
                    print(f"     规则: {issue.rule}")
                    print(f"     类型: {issue.type}")
                    print(f"     描述: {issue.message}")
                    print()
            
        except Exception as e:
            logger.error(f"分析项目问题失败: {e}")
    
    def interactive_project_selection(self):
        """交互式项目选择"""
        print("🎯 交互式项目选择")
        print("=" * 50)
        
        try:
            # 首先尝试自动匹配
            git_url = getattr(Config, 'GIT_REMOTE_URL', None)
            best_mapping = self.project_discovery.get_best_project_mapping(git_url)
            
            if best_mapping:
                print("✅ 自动发现最佳匹配:")
                print(f"   SonarQube: {best_mapping.sonar_name} ({best_mapping.sonar_key})")
                print(f"   Jira:      {best_mapping.jira_name} ({best_mapping.jira_key})")
                print(f"   相似度:    {best_mapping.similarity_score:.2f}")
                print(f"   原因:      {best_mapping.mapping_reason}")
                
                choice = input("\n是否使用此匹配？(y/n): ").lower().strip()
                if choice == 'y':
                    return best_mapping
            
            # 手动选择
            print("\n手动选择项目:")
            projects = self.project_discovery.list_available_projects()
            
            # 选择SonarQube项目
            print(f"\n选择SonarQube项目:")
            for i, project in enumerate(projects['sonar_projects'], 1):
                print(f"{i:2d}. {project['name']} ({project['key']})")
            
            while True:
                try:
                    sonar_choice = int(input(f"\n请选择SonarQube项目 (1-{len(projects['sonar_projects'])}): "))
                    if 1 <= sonar_choice <= len(projects['sonar_projects']):
                        selected_sonar = projects['sonar_projects'][sonar_choice - 1]
                        break
                    else:
                        print("无效选择，请重新输入")
                except ValueError:
                    print("请输入数字")
            
            # 选择Jira项目
            print(f"\n选择Jira项目:")
            for i, project in enumerate(projects['jira_projects'], 1):
                print(f"{i:2d}. {project['name']} ({project['key']})")
            
            while True:
                try:
                    jira_choice = int(input(f"\n请选择Jira项目 (1-{len(projects['jira_projects'])}): "))
                    if 1 <= jira_choice <= len(projects['jira_projects']):
                        selected_jira = projects['jira_projects'][jira_choice - 1]
                        break
                    else:
                        print("无效选择，请重新输入")
                except ValueError:
                    print("请输入数字")
            
            # 创建手动映射
            manual_mapping = ProjectMapping(
                sonar_key=selected_sonar['key'],
                sonar_name=selected_sonar['name'],
                jira_key=selected_jira['key'],
                jira_name=selected_jira['name'],
                similarity_score=1.0,
                mapping_reason="手动选择"
            )
            
            return manual_mapping
            
        except KeyboardInterrupt:
            print("\n操作已取消")
            return None
        except Exception as e:
            logger.error(f"交互式选择失败: {e}")
            return None

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='SonarQube和Jira项目管理工具')
    parser.add_argument('--list', action='store_true', help='列出所有项目')
    parser.add_argument('--discover', action='store_true', help='发现项目匹配')
    parser.add_argument('--analyze', type=str, help='分析指定SonarQube项目的问题')
    parser.add_argument('--interactive', action='store_true', help='交互式项目选择')
    parser.add_argument('--git-url', type=str, help='指定Git仓库URL')
    
    args = parser.parse_args()
    
    if not any([args.list, args.discover, args.analyze, args.interactive]):
        parser.print_help()
        return
    
    try:
        manager = ProjectManager()
        
        if args.list:
            manager.list_all_projects()
        
        if args.discover:
            manager.discover_project_mappings(args.git_url)
        
        if args.analyze:
            manager.analyze_project_issues(args.analyze)
        
        if args.interactive:
            mapping = manager.interactive_project_selection()
            if mapping:
                print(f"\n✅ 选择完成:")
                print(f"   SonarQube: {mapping.sonar_name} ({mapping.sonar_key})")
                print(f"   Jira:      {mapping.jira_name} ({mapping.jira_key})")
        
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
