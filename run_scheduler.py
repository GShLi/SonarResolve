#!/usr/bin/env python3
"""
SonarQube到Jira任务调度器启动脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sonar_tools.scheduler import main

if __name__ == "__main__":
    main()
