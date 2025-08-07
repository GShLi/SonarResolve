#!/usr/bin/env python3
"""
SonarQube Critical Issues to Jira Tasks
自动从SonarQube获取Critical问题并创建Jira任务
"""

import logging
import sys
from datetime import datetime
from typing import List, Dict, Any

from core.config import Config
from clients.sonarqube_client import SonarQubeClient
from clients.jira_client import JiraClient
from core.models import SonarIssue, JiraTask
from utils.project_db import ProjectStatusDB

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
        
        # 初始化项目状态数据库（本地缓存）
        self.project_db = ProjectStatusDB()
        
        self.jira_client = JiraClient(
            Config.JIRA_URL,
            Config.JIRA_API_TOKEN,
            project_db=self.project_db  # 传入数据库实例以支持缓存查询
        )        # 清理过期的缓存记录
        try:
            cleaned_count = self.project_db.cleanup_old_records()
            if cleaned_count > 0:
                logger.info(f"清理了 {cleaned_count} 个过期的缓存记录")
        except Exception as e:
            logger.debug(f"清理缓存记录失败: {e}")

    def test_connections(self) -> bool:
        """测试所有连接"""
        logger.info("开始连接测试...")

        # 测试SonarQube连接
        logger.info("测试SonarQube连接...")
        sonar_ok = self.sonar_client.test_connection()
        if sonar_ok:
            logger.info("✅ SonarQube连接测试通过")
        else:
            logger.error("❌ SonarQube连接测试失败")

        # 测试Jira连接
        logger.info("测试Jira连接...")
        jira_ok = self.jira_client.test_connection()
        if jira_ok:
            logger.info("✅ Jira连接测试通过")
        else:
            logger.error("❌ Jira连接测试失败")

        # 总体结果
        if sonar_ok and jira_ok:
            logger.info("🎉 所有连接测试通过")
            return True
        else:
            failed_clients = []
            if not sonar_ok:
                failed_clients.append("SonarQube")
            if not jira_ok:
                failed_clients.append("Jira")

            logger.error(f"❌ 连接测试失败，失败的客户端: {', '.join(failed_clients)}")
            return False

    def show_cache_status(self):
        """显示本地缓存状态"""
        try:
            logger.info("本地项目数据库状态:")

            # 获取项目统计
            project_stats = self.project_db.get_project_statistics()
            task_stats = self.project_db.get_task_statistics()

            logger.info(f"  已创建项目数: {project_stats.get('total_projects', 0)}")
            logger.info(f"  已创建任务数: {task_stats.get('total_tasks', 0)}")

            # 获取最近创建的项目
            recent_projects = self.project_db.get_all_created_projects()
            if recent_projects:
                logger.info("  最近创建的项目:")
                for project in recent_projects[:5]:  # 只显示前5个项目
                    logger.info(
                        f"    - {project['sonar_project_key']} -> {project['jira_project_key']} ({project['created_time']})")

                if len(recent_projects) > 5:
                    logger.info(f"    ... 还有 {len(recent_projects) - 5} 个项目")
            else:
                logger.info("  暂无已创建项目记录")

        except Exception as e:
            logger.error(f"显示数据库状态失败: {e}")

    def _get_all_critical_issues_by_project(self) -> Dict[str, List[SonarIssue]]:
        """获取所有Critical问题并按项目分组"""
        try:
            logger.info("查询所有Critical问题...")

            # 获取所有Critical问题（不指定项目）
            all_issues = self.sonar_client.get_critical_issues()

            # 按项目分组
            issues_by_project = {}
            for issue in all_issues:
                project_key = issue.project  # 使用project属性
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

    def _ensure_jira_project_exists(self, sonar_project_key: str, sonar_project_name: str = None) -> str:
        """确保Jira项目存在，如果不存在则创建"""
        try:
            # 首先尝试查找现有的Jira项目
            jira_project_key = self._find_matching_jira_project(sonar_project_key)

            if jira_project_key:
                logger.info(f"找到匹配的Jira项目: {jira_project_key}")
                return jira_project_key

            # 如果没有找到匹配的项目，创建新项目
            logger.info(f"未找到匹配的Jira项目，为SonarQube项目 {sonar_project_key} 创建新JIRA项目...")

            # 生成Jira项目key（确保符合Jira规范）
            jira_project_key = self._generate_jira_project_key(sonar_project_key)
            jira_project_name = sonar_project_name or sonar_project_key

            # 创建Jira项目
            success = self.jira_client.create_project(
                key=jira_project_key,
                name=f"{jira_project_name}",
                description=f"自动创建的项目，用于管理SonarQube项目 {sonar_project_key} 的Critical问题"
            )

            if success:
                logger.info(f"成功创建Jira项目: {jira_project_key}")

                # 记录新创建的项目到数据库
                self.project_db.record_created_project(sonar_project_key, jira_project_key)
                logger.debug(f"已记录新创建项目到数据库: {sonar_project_key} -> {jira_project_key}")

                return jira_project_key
            else:
                logger.error(f"创建Jira项目失败: {jira_project_key}")
                return None

        except Exception as e:
            logger.error(f"确保Jira项目存在时发生错误: {e}")
            return None

    def _find_matching_jira_project(self, sonar_project_key: str) -> str:
        """查找匹配的Jira项目（优先从SQLite缓存查询）"""
        try:
            # 1. 首先从SQLite缓存中查询项目映射
            logger.debug(f"从缓存中查询项目 {sonar_project_key} 的映射关系...")
            cached_jira_key = self.project_db.is_project_created(sonar_project_key)

            if cached_jira_key:
                logger.info(f"从缓存中找到项目映射: {sonar_project_key} -> {cached_jira_key}")
                return cached_jira_key

            # 2. 如果缓存中没有，从Jira API查询
            logger.debug(f"从Jira API查询项目 {sonar_project_key} 的匹配项目...")
            jira_projects = self.jira_client.get_all_projects()

            found_jira_key = None

            # 精确匹配
            for project in jira_projects:
                if project['key'].upper() == sonar_project_key.upper():
                    found_jira_key = project['key']
                    logger.info(f"精确匹配找到Jira项目: {found_jira_key}")
                    break

            # 如果没有精确匹配，尝试模糊匹配
            if not found_jira_key:
                for project in jira_projects:
                    if sonar_project_key.upper() in project['key'].upper() or \
                            project['key'].upper() in sonar_project_key.upper():
                        found_jira_key = project['key']
                        logger.info(f"模糊匹配找到Jira项目: {found_jira_key}")
                        break

            return found_jira_key

        except Exception as e:
            logger.debug(f"查找匹配Jira项目失败: {e}")
            return None

    def _generate_jira_project_key(self, sonar_project_key: str) -> str:
        """生成符合Jira规范的项目key"""
        # Jira项目key规范：大写字母，长度2-10个字符
        import re

        # 提取字母和数字，转换为大写
        clean_key = re.sub(r'[^A-Za-z0-9]', '', sonar_project_key).upper()

        # 如果太长，截取前10个字符
        if len(clean_key) > 10:
            clean_key = clean_key[:10]

        # 如果太短，补充S前缀（表示SonarQube）
        if len(clean_key) < 2:
            clean_key = f"S{clean_key}"

        # 确保第一个字符是字母
        if clean_key and not clean_key[0].isalpha():
            clean_key = f"S{clean_key}"

        return clean_key or "SONAR"

    def process_critical_issues(self) -> Dict[str, Any]:
        """批量处理所有项目的Critical问题"""
        logger.info("开始批量处理SonarQube Critical问题...")

        results = {
            'start_time': datetime.now(),
            'total_projects': 0,
            'total_sonar_issues': 0,
            'total_jira_tasks_created': 0,
            'successful_projects': 0,
            'failed_projects': 0,
            'project_results': {},
            'errors': [],
            'created_projects': []
        }

        try:
            # 1. 获取所有Critical问题并按项目分组
            issues_by_project = self._get_all_critical_issues_by_project()

            if not issues_by_project:
                logger.info("没有发现任何Critical问题")
                results['total_projects'] = 0
                results['total_sonar_issues'] = 0
                return results

            results['total_projects'] = len(issues_by_project)
            results['total_sonar_issues'] = sum(len(issues) for issues in issues_by_project.values())

            logger.info(f"将处理 {results['total_projects']} 个项目，共 {results['total_sonar_issues']} 个Critical问题")

            # 2. 对每个项目处理Critical问题
            for sonar_project_key, sonar_issues in issues_by_project.items():
                logger.info(f"\n{'=' * 60}")
                logger.info(f"处理项目: {sonar_project_key} ({len(sonar_issues)} 个问题)")
                logger.info(f"{'=' * 60}")

                project_result = {
                    'sonar_project_key': sonar_project_key,
                    'sonar_issues_count': len(sonar_issues),
                    'jira_project_key': None,
                    'jira_project_created': False,
                    'jira_tasks_created': 0,
                    'created_tasks': [],
                    'errors': [],
                    'success': False
                }

                try:
                    # 3. 确保对应的Jira项目存在
                    jira_project_key = self._ensure_jira_project_exists(sonar_project_key)

                    if not jira_project_key:
                        error_msg = f"无法为SonarQube项目 {sonar_project_key} 创建或找到对应的Jira项目"
                        logger.error(error_msg)
                        project_result['errors'].append(error_msg)
                        results['failed_projects'] += 1
                        results['project_results'][sonar_project_key] = project_result
                        continue

                    project_result['jira_project_key'] = jira_project_key

                    # 检查是否是新创建的项目
                    all_jira_projects = self.jira_client.get_all_projects()
                    existing_keys = [p['key'] for p in all_jira_projects]
                    if jira_project_key not in existing_keys:
                        project_result['jira_project_created'] = True
                        results['created_projects'].append(jira_project_key)

                    # 4. 在Jira中创建任务
                    logger.info(f"在Jira项目 {jira_project_key} 中为 {len(sonar_issues)} 个Critical问题创建任务...")
                    created_tasks = self.jira_client.create_issues_from_sonar(
                        sonar_issues,
                        jira_project_key
                    )

                    project_result['jira_tasks_created'] = len(created_tasks)
                    project_result['created_tasks'] = created_tasks
                    project_result['success'] = True

                    results['successful_projects'] += 1
                    results['total_jira_tasks_created'] += len(created_tasks)

                    logger.info(f"项目 {sonar_project_key} 处理成功:")
                    logger.info(f"  Jira项目: {jira_project_key}")
                    logger.info(f"  创建任务: {len(created_tasks)} 个")

                except Exception as e:
                    error_msg = f"处理项目 {sonar_project_key} 时发生错误: {e}"
                    logger.error(error_msg)
                    project_result['errors'].append(error_msg)
                    results['failed_projects'] += 1

                results['project_results'][sonar_project_key] = project_result

            # 5. 生成批量处理报告
            self._generate_batch_report(results)

        except Exception as e:
            error_msg = f"批量处理过程中发生错误: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)

        finally:
            results['end_time'] = datetime.now()
            results['duration'] = results['end_time'] - results['start_time']

            # 显示数据库统计信息
            try:
                project_stats = self.project_db.get_project_statistics()
                task_stats = self.project_db.get_task_statistics()
                logger.info("批量处理完成后的数据库统计:")
                logger.info(f"  - 已创建项目数: {project_stats.get('total_projects', 0)}")
                logger.info(f"  - 已创建任务数: {task_stats.get('total_tasks', 0)}")
                results['db_stats'] = {
                    'projects': project_stats.get('total_projects', 0),
                    'tasks': task_stats.get('total_tasks', 0)
                }
            except Exception as e:
                logger.debug(f"获取数据库统计信息失败: {e}")

        return results

    def _generate_batch_report(self, results: Dict[str, Any]):
        """生成批量处理报告"""
        logger.info("生成批量处理报告...")

        report_content = f"""
SonarQube Critical问题批量处理报告
========================================

处理时间: {results['start_time'].strftime('%Y-%m-%d %H:%M:%S')}
处理耗时: {results['duration']}

总体统计:
- 处理项目总数: {results['total_projects']} 个
- 成功处理项目: {results['successful_projects']} 个  
- 失败项目: {results['failed_projects']} 个
- 成功率: {(results['successful_projects'] / results['total_projects'] * 100) if results['total_projects'] > 0 else 0:.1f}%

问题处理统计:
- 发现Critical问题总数: {results['total_sonar_issues']} 个
- 创建Jira任务总数: {results['total_jira_tasks_created']} 个
- 任务创建率: {(results['total_jira_tasks_created'] / results['total_sonar_issues'] * 100) if results['total_sonar_issues'] > 0 else 0:.1f}%

创建的Jira项目:
{chr(10).join([f"- {project}" for project in results['created_projects']]) if results['created_projects'] else "无新创建项目"}

项目处理详情:
"""

        # 成功处理的项目
        successful_projects = [k for k, v in results['project_results'].items() if v['success']]
        if successful_projects:
            report_content += "\n✅ 成功处理的项目:\n"
            for project_key in successful_projects:
                result = results['project_results'][project_key]
                report_content += f"""
📋 SonarQube项目: {project_key}
   - Jira项目: {result['jira_project_key']}
   - 项目是否新建: {'是' if result['jira_project_created'] else '否'}
   - 发现问题: {result['sonar_issues_count']} 个
   - 创建任务: {result['jira_tasks_created']} 个
   - 创建的任务: {', '.join(result['created_tasks']) if result['created_tasks'] else '无'}
"""

        # 失败的项目
        failed_projects = [k for k, v in results['project_results'].items() if not v['success']]
        if failed_projects:
            report_content += "\n❌ 处理失败的项目:\n"
            for project_key in failed_projects:
                result = results['project_results'][project_key]
                report_content += f"""
📋 SonarQube项目: {project_key}
   - 发现问题: {result['sonar_issues_count']} 个
   - 失败原因:
"""
                for error in result['errors']:
                    report_content += f"     • {error}\n"

        # 整体错误信息
        if results['errors']:
            report_content += f"\n🚨 整体处理错误:\n"
            for error in results['errors']:
                report_content += f"- {error}\n"

        report_content += f"""
========================================
批量处理状态: {'成功' if results['successful_projects'] > 0 else '失败'}
成功项目数: {results['successful_projects']}/{results['total_projects']}
总任务创建数: {results['total_jira_tasks_created']} 个
========================================
"""

        # 保存报告
        report_filename = f'sonar_to_jira_batch_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report_content)

        logger.info(f"批量处理报告已保存到: {report_filename}")

        # 显示摘要
        print(f"\n{'=' * 70}")
        print("📋 SonarQube到Jira批量处理完成")
        print(f"{'=' * 70}")
        print(f"处理项目: {results['successful_projects']}/{results['total_projects']} 个成功")
        print(f"发现问题: {results['total_sonar_issues']} 个")
        print(f"创建任务: {results['total_jira_tasks_created']} 个")
        print(f"处理耗时: {results['duration']}")

        if results['created_projects']:
            print(f"\n🆕 新创建的Jira项目:")
            for project in results['created_projects']:
                print(f"  📁 {project}")

        if successful_projects:
            print(f"\n✅ 成功处理的项目:")
            for project_key in successful_projects:
                result = results['project_results'][project_key]
                print(
                    f"  📋 {project_key} → {result['jira_project_key']}: {result['jira_tasks_created']}/{result['sonar_issues_count']} 个任务")

        if failed_projects:
            print(f"\n❌ 处理失败的项目:")
            for project_key in failed_projects:
                print(f"  📋 {project_key}")

        print(f"\n📄 详细报告: {report_filename}")

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

        # 显示缓存状态
        processor.show_cache_status()

        # 处理Critical问题
        results = processor.process_critical_issues()

        # 输出结果摘要
        if 'total_projects' in results:
            # 批量处理结果
            logger.info("批量处理完成！")
            logger.info(f"处理项目: {results['successful_projects']}/{results['total_projects']} 个成功")
            logger.info(f"发现Critical问题: {results['total_sonar_issues']} 个")
            logger.info(f"创建Jira任务: {results['total_jira_tasks_created']} 个")
            logger.info(f"处理耗时: {results['duration']}")

            if results['created_projects']:
                logger.info(f"新创建Jira项目: {', '.join(results['created_projects'])}")
        else:
            # 单项目处理结果（为了向后兼容保留）
            logger.info("处理完成！")
            logger.info(f"发现Critical问题: {results.get('sonar_issues_count', 0)} 个")
            logger.info(f"创建Jira任务: {results.get('jira_tasks_created', 0)} 个")
            logger.info(f"处理耗时: {results.get('duration', 'N/A')}")

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
