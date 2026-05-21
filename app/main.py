"""
中小学生学习助手 - 后端服务 v1.0 (学生端完整版)
作者：张一凡
日期：2026.05.12
第四周交付：student_api_complete_张一凡
"""

import json
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
from openai import OpenAI
import os
from dotenv import load_dotenv
from datetime import datetime

# 加载环境变量
load_dotenv()

app = FastAPI(
    title="中小学生学习助手 - AI 批改服务",
    description="学生端API v1.0",
    version="1.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 配置 ====================
client = OpenAI(
    api_key=os.getenv("BAILIAN_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# 内存缓存 + 简单历史记录存储（实际项目建议换成数据库）
composition_cache = {}        # 批改缓存
correction_history = []       # 批改历史记录（内存版，后续可换数据库）

# ==================== Prompt ====================
SYSTEM_PROMPT = """你是"中小学生学习助手"，一位专业的初中语文老师。

【最高铁律】
你**只能**返回一个纯净的JSON对象，绝对不要输出任何其他文字。

输出格式必须严格如下：
{
  "total_score": 整数 (0-100),
  "dimension_scores": {
    "内容与主题": "分数/25",
    "结构与逻辑": "分数/25",
    "语言表达": "分数/25",
    "创新与情感": "分数/25"
  },
  "strengths": ["优点1", "优点2"],
  "weaknesses": ["不足1"],
  "suggestions": "改进建议",
  "inspiring_questions": ["问题1", "问题2", "问题3"],
  "encouragement": "鼓励语"
}

现在开始批改，只返回JSON。"""

# ==================== 数据模型 ====================
class CompositionRequest(BaseModel):
    content: str
    grade: str = "中年级"
    student_id: Optional[str] = "default_student"   # 新增：支持学生ID

class CompositionResponse(BaseModel):
    total_score: int
    dimension_scores: Dict[str, str]
    strengths: List[str]
    weaknesses: List[str]
    suggestions: str
    inspiring_questions: List[str]
    encouragement: str

class HistoryRecord(BaseModel):
    id: int
    student_id: str
    content_preview: str
    total_score: int
    created_at: str

# ==================== 核心批改函数 ====================
async def call_qwen_for_correction(content: str):
    user_prompt = f"请严格按照JSON格式批改以下作文：\n{content}"
    
    response = client.chat.completions.create(
        model="qwen-turbo",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.6,
        max_tokens=1500,
    )
    return response.choices[0].message.content

# ==================== 主接口 ====================
@app.post("/api/composition/correct", response_model=CompositionResponse)
async def correct_composition(request: CompositionRequest):
    start_time = time.time()
    cache_key = f"{request.student_id}:{request.grade}:{request.content[:300]}"

    if cache_key in composition_cache:
        print(f"【缓存命中】学生 {request.student_id}")
        return composition_cache[cache_key]

    try:
        content = request.content.replace("\r\n", "\n").replace("\r", "\n")
        result_text = await call_qwen_for_correction(content)

        # 清理JSON
        cleaned = result_text.strip()
        if "```" in cleaned:
            cleaned = cleaned.split("```")[1].strip()
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()

        result = json.loads(cleaned)

        response_data = CompositionResponse(
            total_score=result.get("total_score", 80),
            dimension_scores=result.get("dimension_scores", {}),
            strengths=result.get("strengths", []),
            weaknesses=result.get("weaknesses", []),
            suggestions=result.get("suggestions", "暂无具体建议"),
            inspiring_questions=result.get("inspiring_questions", []),
            encouragement=result.get("encouragement", "继续努力，你会越来越好！")
        )

        # 保存到历史记录
        correction_history.append({
            "id": len(correction_history) + 1,
            "student_id": request.student_id,
            "content_preview": request.content[:100] + "...",
            "total_score": response_data.total_score,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        composition_cache[cache_key] = response_data
        print(f"【批改完成】学生 {request.student_id} 总分: {response_data.total_score} 耗时: {time.time()-start_time:.2f}秒")
        
        return response_data

    except Exception as e:
        print(f"批改失败: {e}")
        return CompositionResponse(
            total_score=75,
            dimension_scores={},
            strengths=["作文已接收"],
            weaknesses=[],
            suggestions="系统处理异常，请稍后重试",
            inspiring_questions=[],
            encouragement="坚持就是胜利！你已经迈出了重要一步！"
        )

# ==================== 新增：历史记录查询接口 ====================
@app.get("/api/history/{student_id}", response_model=List[HistoryRecord])
async def get_history(student_id: str, limit: int = 10):
    """获取学生批改历史"""
    user_history = [record for record in correction_history if record["student_id"] == student_id]
    return sorted(user_history, key=lambda x: x["created_at"], reverse=True)[:limit]

# ==================== 健康检查 ====================
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": "1.0",
        "message": "学生端API服务正常运行",
        "history_count": len(correction_history),
        "timestamp": time.time()
    }

# ==================== 启动 ====================
if __name__ == "__main__":
    import uvicorn
    print("启动中小学生学习助手 - 学生端API v1.0...")
    uvicorn.run(app, host="0.0.0.0", port=8000)