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
5. 问题范围分析（特别关注是否是函数内部问题）
6. 如果是函数内部问题，需要分析函数的代码边界

你必须以JSON格式回复，包含以下字段：
{
  "analysis": {
    "issue_type": "问题类型分类",
    "root_cause": "问题根本原因的详细分析", 
    "risk_level": "低/中/高",
    "complexity": "修复复杂度(简单/中等/复杂)",
    "impact_scope": "影响范围评估"
  },
  "scope": {
    "scope_type": "问题范围类型(function_internal/class_method/global/file_level)",
    "is_function_internal": true/false,
    "function_name": "如果是函数内部问题，提供函数名",
    "estimated_function_start_line": "预估函数开始行号(基于代码片段分析)",
    "estimated_function_end_line": "预估函数结束行号(基于代码片段分析)",
    "context_analysis": "基于提供的代码片段对函数边界的分析说明"
  }
}

重要说明：
- 如果问题在函数内部，请仔细分析代码片段，推断函数的可能边界
- 基于代码缩进、语法结构等特征来估算函数范围
- 范围分析将用于后续的精确代码修复和合并操作
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
        code_snippet = issue_data.get("code_snippet", "无代码片段")
        issue_line = issue_data.get("line", "Unknown")

        return f"""请分析以下SonarQube Critical问题：

## 问题信息
- **规则名称**: {issue_data.get('rule', 'Unknown')}
- **严重级别**: {issue_data.get('severity', 'Unknown')}
- **问题描述**: {issue_data.get('message', 'No description')}
- **文件路径**: {issue_data.get('component', 'Unknown')}
- **问题行数**: {issue_line}
- **代码语言**: {issue_data.get('language', 'Unknown')}

## 规则详细信息
{json.dumps(issue_data.get('rule_info', {}), indent=2, ensure_ascii=False)}

## 问题代码上下文
```
{code_snippet}
```

## 范围分析指导
请特别关注以下几点：
1. 分析问题是否发生在函数/方法内部
2. 如果是函数内部问题，请基于代码片段推断函数的边界：
   - 查找函数定义关键字（如 def, function, func 等）
   - 分析代码缩进结构来确定函数范围
   - 查找函数结束标志（如 return 语句、函数末尾等）
   - 估算函数在原文件中的大致行号范围
3. 考虑问题的影响范围（仅影响当前函数还是可能影响其他部分）

请根据以上信息进行详细的问题分析，特别是范围分析，并以JSON格式返回结果。"""

    @staticmethod
    def build_fix_prompt(
        issue_data: Dict[str, Any], analysis_result: Dict[str, Any] = None
    ) -> str:
        """构建代码修复提示词"""
        language = issue_data.get("language", "unknown")

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

        # 添加函数范围信息
        function_scope = issue_data.get("function_scope")
        if function_scope and function_scope.get("success"):
            prompt += f"""
## 函数范围信息
**函数名称**: {function_scope.get('function_name', 'Unknown')}
**函数签名**: {function_scope.get('function_signature', 'Unknown')}
**函数范围**: 第{function_scope.get('start_line', 'Unknown')}-{function_scope.get('end_line', 'Unknown')}行
**范围类型**: {function_scope.get('scope_type', 'Unknown')}

**范围分析说明**: {function_scope.get('analysis_notes', '无说明')}

重要提示：
1. 该问题位于函数内部，修复时请确保不破坏函数的整体结构
2. 如果需要修改函数签名或函数整体逻辑，请在修复方案中详细说明
3. 优先进行局部修复，避免影响函数的其他部分
"""

        prompt += f"""
请根据{language}语言的最佳实践，提供完整的修复方案，并以JSON格式返回结果。

如果问题在函数内部，请特别注意：
- 保持函数的原始功能和接口不变
- 尽量进行最小化修改
- 确保修复不会影响函数的其他逻辑"""

        return prompt

    @staticmethod
    def get_code_application_system_prompt() -> str:
        """获取代码应用的系统提示词"""
        return """你是一个专业的代码编辑专家，负责将AI修复的代码准确地应用到原始文件中。

你的任务是：
1. 分析原始文件内容和修复代码
2. 智能识别需要修复的代码位置
3. 精确应用修复，保持文件的完整性
4. 确保修复后的代码语法正确

应用策略（按优先级）：
1. **精确行号匹配**：如果有准确的行号信息，直接替换指定行
2. **模式匹配**：通过代码特征匹配，找到需要修复的代码段
3. **函数级替换**：替换整个函数或方法块
4. **智能合并**：将修复代码智能合并到原文件中

你必须以JSON格式回复，包含以下字段：
{
  "success": true/false,
  "strategy_used": "使用的应用策略",
  "modified_content": "修改后的完整文件内容",
  "changes_summary": "修改摘要说明",
  "confidence": "应用信心等级(1-10)",
  "warnings": ["潜在问题警告"],
  "validation_notes": "验证说明"
}

要求：
- 保持原文件的结构和格式
- 不破坏现有功能
- 精确应用修复，避免误修改
- 如果无法确定应用位置，返回 success: false"""

    @staticmethod
    def build_code_application_prompt(
        original_content: str, fixed_code: str, issue_data: Dict[str, Any]
    ) -> str:
        """构建代码应用提示词"""
        language = issue_data.get("language", "unknown")
        file_path = issue_data.get("component", "Unknown")
        line_number = issue_data.get("line", "Unknown")
        problem_description = issue_data.get("message", "No description")

        prompt = f"""请将AI修复的代码应用到原始文件中：

## 任务信息
- **文件路径**: {file_path}
- **问题行号**: {line_number}
- **代码语言**: {language}
- **问题描述**: {problem_description}

## 原始文件内容
```{language}
{original_content}
```

## AI修复后的代码
```{language}
{fixed_code}
```

## 原始问题代码片段（来自SonarQube）
```{language}
{issue_data.get('code_snippet', '无代码片段')}
```
"""

        # 添加函数范围信息
        function_scope = issue_data.get("function_scope")
        if function_scope and function_scope.get("success"):
            prompt += f"""
## 函数范围上下文
- **函数名称**: {function_scope.get('function_name', 'Unknown')}
- **函数范围**: 第{function_scope.get('start_line', 'Unknown')}-{function_scope.get('end_line', 'Unknown')}行
- **函数类型**: {function_scope.get('scope_type', 'Unknown')}
- **函数签名**: {function_scope.get('function_signature', 'Unknown')}

**重要提示**:
该问题位于函数内部，请特别注意：
1. 修复范围应限制在指定的函数边界内
2. 不要修改函数外的代码
3. 保持函数的原始接口和整体结构
4. 优先进行最小化的局部修复
"""

        prompt += """
请分析原始文件和修复代码，找到最佳的应用方式，并返回修改后的完整文件内容。

注意事项：
1. 修复代码可能包含行号标记（如 "→ 123: "），需要清理
2. 要保持原文件的导入语句、注释、格式等
3. 只修改必要的部分，不要改动无关代码
4. 确保修复后的代码语法正确且逻辑完整
5. 如果问题在函数内部，请确保修改范围不超出函数边界"""

        return prompt

    @staticmethod
    def build_validation_prompt(
        original_code: str, fixed_code: str, issue_data: Dict[str, Any]
    ) -> str:
        """构建修复验证提示词"""
        language = issue_data.get("language", "unknown")

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
    def build_commit_prompt(
        issue_data: Dict[str, Any], fix_result: Dict[str, Any]
    ) -> str:
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
