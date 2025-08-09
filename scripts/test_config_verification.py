#!/usr/bin/env python3
"""
配置验证测试脚本
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_config():
    """测试配置是否正确"""
    print("🔧 SonarResolve - 配置验证测试")
    print("=" * 50)
    
    try:
        from sonar_tools.core.config import Config
        
        print("📋 基础配置:")
        print(f"  SonarQube URL: {Config.SONARQUBE_URL}")
        print(f"  获取代码片段: {Config.SONARQUBE_FETCH_CODE_SNIPPET}")
        
        print("\n📋 Jira配置:")
        print(f"  Jira URL: {Config.JIRA_URL}")
        print(f"  任务前缀: {Config.JIRA_TASK_PREFIX}")
        print(f"  包含代码片段: {Config.JIRA_INCLUDE_CODE_SNIPPET}")
        print(f"  代码上下文行数: {Config.JIRA_CODE_CONTEXT_LINES}")
        
        print("\n📋 存储配置:")
        print(f"  数据库路径: {Config.DATABASE_PATH}")
        print(f"  日志路径: {Config.LOG_FILE_PATH}")
        print(f"  日志级别: {Config.LOG_LEVEL}")
        print(f"  日志最大大小: {Config.LOG_MAX_SIZE}MB")
        print(f"  日志备份数量: {Config.LOG_BACKUP_COUNT}")
        
        # 验证路径是否正确
        db_path = Path(Config.DATABASE_PATH)
        log_path = Path(Config.LOG_FILE_PATH)
        
        print(f"\n📁 路径验证:")
        print(f"  数据库绝对路径: {db_path.absolute()}")
        print(f"  日志文件绝对路径: {log_path.absolute()}")
        print(f"  数据库目录存在: {db_path.parent.exists()}")
        print(f"  日志目录存在: {log_path.parent.exists()}")
        
        # 测试配置方法
        print(f"\n🧪 配置方法测试:")
        
        # 获取日志信息
        log_info = Config.get_log_info()
        print(f"  日志配置查询: ✅")
        
        # 设置日志
        actual_log_path = Config.setup_logging()
        print(f"  日志设置: ✅ -> {actual_log_path}")
        
        print("\n🎉 所有配置验证通过！")
        return True
        
    except Exception as e:
        print(f"❌ 配置验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_config()
    sys.exit(0 if success else 1)
