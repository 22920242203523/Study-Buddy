# 家长端API设计草图

**作者**：张一凡  
**日期**：2026.05.12  
**版本**：v0.1（预研版）  
**任务**：家长端API预研

---

## 1. 家长端核心目标

- 让家长实时了解孩子学习情况
- 提供有价值的学习建议和预警
- 保护学生隐私（脱敏处理）
- 为后续家长端功能开发提供清晰接口规范

---

## 2. 主要功能模块与接口设计

### 2.1 学情看板（Dashboard）

**接口**：`GET /api/parent/dashboard/{parent_id}`

**功能**：返回孩子整体学习概览

**返回字段示例**：
```json
{
  "child_name": "张小明",
  "grade": "八年级",
  "total_compositions": 28,
  "average_score": 84.5,
  "recent_trend": "上升", 
  "strength_subjects": ["记叙文", "议论文"],
  "weak_subjects": ["说明文"],
  "last_correction": {
    "date": "2026-05-11",
    "score": 88,
    "suggestions": "..."
  }
}

2.2 周学习计划
接口：GET /api/parent/weekly-plan/{parent_id}
功能：生成或返回本周学习建议
返回字段：

本周作文训练重点
推荐练习题型
预计提升目标
家长可配合事项

2.3 脱敏学习报告（周报/月报）
接口：GET /api/parent/report/{parent_id}?type=weekly
特点：不显示具体作文内容，仅显示趋势和建议，保护学生隐私。
返回示例：

{
  "report_type": "weekly",
  "period": "2026.05.05 - 2026.05.11",
  "average_score": 83.2,
  "improvement_points": ["结构清晰度", "情感表达"],
  "suggested_actions": ["多读优秀范文", "加强审题训练"],
  "warning_level": "normal"
}

{
  "report_type": "weekly",
  "period": "2026.05.05 - 2026.05.11",
  "average_score": 83.2,
  "improvement_points": ["结构清晰度", "情感表达"],
  "suggested_actions": ["多读优秀范文", "加强审题训练"],
  "warning_level": "normal"
}

2.4 行为预警接口
接口：GET /api/parent/warning/{parent_id}
功能：检测异常学习行为并预警
预警类型：

连续多篇作文分数下滑
多次出现相同问题（如跑题、字数不足）
长时间未提交作文
抄袭风险提示（如果后续接入检测）

3. 推荐接口列表（v1.0）
接口名称,方法,路径,说明
学情看板,GET,/api/parent/dashboard/{parent_id},整体概览
周学习计划,GET,/api/parent/weekly-plan/{parent_id},周计划建议
学习报告,GET,/api/parent/report/{parent_id},周报/月报（脱敏）
行为预警,GET,/api/parent/warning/{parent_id},异常行为提醒
历史批改记录,GET,/api/parent/history/{parent_id},孩子所有批改记录

4. 设计原则

隐私保护：所有涉及作文原文的接口均做脱敏处理
数据安全：家长只能查看自己孩子的相关数据
易用性：返回数据结构清晰，方便前端展示
可扩展性：预留后续消息推送、家长反馈等接口


5. 下一步计划

与杜鑫胜确认数据字段
完成家长端API代码实现
与薛慧欣对接前端展示
进行脱敏逻辑详细设计