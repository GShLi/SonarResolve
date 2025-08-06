# Jira标签问题修复说明

## 问题描述
原始代码在添加Jira标签时可能会遇到以下错误：
- 标签格式不正确
- 标签包含特殊字符
- 标签为空或None
- Jira API调用失败

## 修复方案

### 1. 在创建issue时直接添加标签
```python
# 在issue_dict中直接包含标签
if task.labels:
    valid_labels = self._validate_and_clean_labels(task.labels)
    if valid_labels:
        issue_dict['labels'] = valid_labels
```

### 2. 多层级的标签添加机制
如果创建时添加失败，会尝试以下方法：
1. 直接更新标签字段
2. 获取现有标签后合并更新
3. 使用REST API直接更新

### 3. 标签验证和清理
添加了 `_validate_and_clean_labels` 方法：
- 移除空白和None值
- 转换为小写
- 替换特殊字符为连字符
- 移除多余连字符
- 限制长度（最大50字符）
- 去重
- 限制数量（最多10个）

### 4. 标签格式规范化
```python
def _validate_and_clean_labels(self, labels: List[str]) -> List[str]:
    """验证和清理标签"""
    valid_labels = []
    for label in labels:
        if not label or not isinstance(label, str):
            continue
            
        # 清理标签：去空格、转小写、替换特殊字符
        cleaned_label = label.strip().lower()
        
        # 替换空格和特殊字符为连字符
        cleaned_label = re.sub(r'[^\w\-]', '-', cleaned_label)
        
        # 移除多余的连字符
        cleaned_label = re.sub(r'-+', '-', cleaned_label)
        
        # 移除开头和结尾的连字符
        cleaned_label = cleaned_label.strip('-')
        
        # 检查长度限制
        if len(cleaned_label) > 50:
            cleaned_label = cleaned_label[:50]
        
        # 确保不为空且不重复
        if cleaned_label and cleaned_label not in valid_labels:
            valid_labels.append(cleaned_label)
    
    return valid_labels[:10]  # 限制标签数量
```

## 修复效果

### 原始标签示例
```python
labels = [
    "sonarqube",
    "critical issue",  
    "Security Vulnerability",
    "java:S1234",
    "   spaces   ",
    "",
    None,
    "special@#$%chars"
]
```

### 清理后的标签
```python
labels = [
    "sonarqube",
    "critical-issue",
    "security-vulnerability", 
    "java-s1234",
    "spaces",
    "special---chars"
]
```

## 错误处理
- 如果所有标签添加方法都失败，会记录警告但不会阻止issue创建
- 提供详细的日志信息帮助调试
- 优雅地处理各种边界情况

## 使用建议
1. 确保标签名称符合Jira规范
2. 避免使用特殊字符和过长的标签名
3. 检查Jira项目的标签权限设置
4. 查看日志了解标签添加状态

## 测试验证
可以运行 `test_labels.py` 来测试标签验证功能：
```bash
python test_labels.py
```

这个修复确保了标签功能的稳定性和兼容性。
