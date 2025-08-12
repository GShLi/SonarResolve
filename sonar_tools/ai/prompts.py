"""
AI提示词模板
包含所有用于代码分析和修复的提示词模板
"""

import json
from typing import Any, Dict


class PromptTemplates:
    """AI提示词模板管理类"""
    
    @staticmethod
    def get_analysis_system_prompt() -> str:
        """获取问题分析的系统提示词"""
        return """你是一个专业的代码质量分析专家。你的任务是分析SonarQube检测到的代码质量问题。

请仔细分析提供的问题信息，包括：
1. 问题的具体类型和严重性
2. 问题的根本原因
3. 潜在的风险等级
4. 修复的复杂度评估

你必须以JSON格式回复，包含以下字段：
{
  "analysis": {
    "issue_type": "问题类型分类",
    "root_cause": "问题根本原因的详细分析", 
    "risk_level": "低/中/高",
    "complexity": "修复复杂度(简单/中等/复杂)",
    "impact_scope": "影响范围评估"
  }
}

请确保分析准确、专业，便于后续的自动修复处理。"""

    @staticmethod
    def get_fix_system_prompt() -> str:
        """获取代码修复的系统提示词"""
        return """你是一个经验丰富的软件工程师，专门负责修复SonarQube检测到的代码质量问题。

修复原则：
1. ✅ 完全解决SonarQube检测到的问题
2. ✅ 保持原有功能逻辑不变
3. ✅ 遵循编程语言最佳实践
4. ✅ 保持代码可读性和可维护性
5. ✅ 不引入新的问题或副作用

你必须以JSON格式回复，包含以下字段：
{
  "analysis": {
    "issue_type": "问题类型",
    "root_cause": "问题根本原因",
    "risk_level": "风险等级(低/中/高)"
  },
  "solution": {
    "strategy": "修复策略说明",
    "changes": "具体改动说明",
    "impact": "影响范围评估"
  },
  "fixed_code": "修复后的完整代码",
  "validation": {
    "sonar_compliant": true/false,
    "functionality_preserved": true/false,
    "additional_improvements": "额外优化说明"
  },
  "commit_message": "简短的提交信息"
}

请确保修复后的代码能够通过SonarQube规则检查，并保持原有功能完整性。"""

    @staticmethod
    def get_validation_system_prompt() -> str:
        """获取修复验证的系统提示词"""
        return """你是一个代码审查专家，负责验证SonarQube问题修复的质量。

验证标准：
1. SonarQube合规性：是否完全解决了原问题
2. 功能完整性：是否保持了原有业务逻辑
3. 代码质量：可读性、复杂度、最佳实践
4. 安全性：是否引入了安全风险

你必须以JSON格式回复，包含以下字段：
{
  "overall_score": "总分(1-20)",
  "compliance_check": true/false,
  "quality_grade": "A/B/C/D/F",
  "detailed_scores": {
    "sonar_compliance": "评分1-5",
    "functionality": "评分1-5", 
    "code_quality": "评分1-5",
    "security": "评分1-5"
  },
  "recommendations": [
    "改进建议1",
    "改进建议2"
  ],
  "approval_status": "APPROVED/NEEDS_REVISION/REJECTED",
  "reviewer_notes": "审查员备注"
}

请提供详细、客观的验证分析。"""

    @staticmethod
    def get_commit_system_prompt() -> str:
        """获取提交信息生成的系统提示词"""
        return """你是一个项目管理专家，负责为代码修复生成规范的Git提交信息和Merge Request描述。

要求：
1. 遵循Conventional Commits规范
2. 提交信息简洁明了但包含关键信息
3. MR描述详细，便于代码审查
4. 包含适当的标签和测试建议

你必须以JSON格式回复，包含以下字段：
{
  "commit": {
    "type": "fix/feat/refactor/perf/security",
    "scope": "模块名称",
    "subject": "简短描述(50字符内)",
    "body": "详细描述修复内容",
    "footer": "关联issue或breaking changes"
  },
  "merge_request": {
    "title": "MR标题",
    "description": "详细的MR描述",
    "labels": ["标签1", "标签2"],
    "assignee_notes": "分配给审查员的说明",
    "testing_notes": "测试建议"
  },
  "branch_name": "分支名称建议"
}

请确保信息准确、专业，便于团队协作。"""

    @staticmethod
    def build_analysis_prompt(issue_data: Dict[str, Any]) -> str:
        """构建问题分析提示词"""
        return f"""请分析以下SonarQube Critical问题：

## 问题信息
- **规则名称**: {issue_data.get('rule', 'Unknown')}
- **严重级别**: {issue_data.get('severity', 'Unknown')}
- **问题描述**: {issue_data.get('message', 'No description')}
- **文件路径**: {issue_data.get('component', 'Unknown')}
- **问题行数**: {issue_data.get('line', 'Unknown')}
- **代码语言**: {issue_data.get('language', 'Unknown')}

## 规则详细信息
{json.dumps(issue_data.get('rule_info', {}), indent=2, ensure_ascii=False)}

## 问题代码上下文
```
{issue_data.get('code_snippet', '无代码片段')}
```

请根据以上信息进行详细的问题分析，并以JSON格式返回结果。"""

    @staticmethod
    def build_fix_prompt(issue_data: Dict[str, Any], analysis_result: Dict[str, Any] = None) -> str:
        """构建代码修复提示词"""
        language = issue_data.get('language', 'unknown')
        
        prompt = f"""请修复以下SonarQube问题：

## 修复任务
**SonarQube规则**: {issue_data.get('rule', 'Unknown')}
**问题描述**: {issue_data.get('message', 'No description')}
**文件**: {issue_data.get('component', 'Unknown')}
**问题行**: {issue_data.get('line', 'Unknown')}
**代码语言**: {language}

## 原始代码
```{language}
{issue_data.get('code_snippet', '无代码片段')}
```

## 规则信息
{json.dumps(issue_data.get('rule_info', {}), indent=2, ensure_ascii=False)}
"""

        if analysis_result:
            prompt += f"""
## 问题分析结果
{json.dumps(analysis_result, indent=2, ensure_ascii=False)}
"""

        prompt += f"""
请根据{language}语言的最佳实践，提供完整的修复方案，并以JSON格式返回结果。"""
        
        return prompt

    @staticmethod
    def build_validation_prompt(original_code: str, fixed_code: str, issue_data: Dict[str, Any]) -> str:
        """构建修复验证提示词"""
        language = issue_data.get('language', 'unknown')
        
        return f"""请验证以下代码修复的质量：

## 验证任务
**原始问题**: {issue_data.get('message', 'Unknown')}
**修复规则**: {issue_data.get('rule', 'Unknown')}
**代码语言**: {language}

## 代码对比
### 修复前:
```{language}
{original_code}
```

### 修复后:
```{language}
{fixed_code}
```

## 规则要求
{json.dumps(issue_data.get('rule_info', {}), indent=2, ensure_ascii=False)}

请逐项检查修复质量，并以JSON格式返回验证结果。"""

    @staticmethod
    def build_commit_prompt(issue_data: Dict[str, Any], fix_result: Dict[str, Any]) -> str:
        """构建提交信息生成提示词"""
        return f"""请为以下代码修复生成Git提交信息和MR描述：

## 修复信息
- **SonarQube规则**: {issue_data.get('rule', 'Unknown')}
- **问题文件**: {issue_data.get('component', 'Unknown')}
- **问题类型**: {fix_result.get('analysis', {}).get('issue_type', 'Unknown')}
- **修复策略**: {fix_result.get('solution', {}).get('strategy', 'Unknown')}

## 修复详情
{json.dumps(fix_result, indent=2, ensure_ascii=False)}

请生成规范的提交信息和详细的MR描述，以JSON格式返回结果。"""
