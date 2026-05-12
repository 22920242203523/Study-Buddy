"""
中小学生学习助手 - 性能优化版 v1.0
作者：张一凡
日期：2026.05.12
交付物：performance_optimized_张一凡_20260512.py

优化点：
- 内存缓存（相同作文秒级返回）
- 请求耗时监控与日志
- 缓存命中率统计
- 异步优化准备
- 更稳定的错误处理
"""

import json
import time
import asyncio
from fastapi import FastAPI, Request
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
    title="中小学生学习助手 - 性能优化版",
    description="响应速度深度优化 v1.0",
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

# 性能监控
request_count = 0
cache_hit_count = 0
total_response_time = 0.0

# 内存缓存（支持 student_id）
composition_cache: Dict[str, dict] = {}

# ==================== Prompt ====================
SYSTEM_PROMPT = """你是"中小学生学习助手"，一位温柔且专业的初中语文老师。

【最高铁律】
你**只能**返回一个纯净的JSON对象，绝对不要输出任何其他文字、解释、问候或markdown。

输出格式必须严格如下：
{
  "total_score": 整数 (0-100),
  "dimension_scores": {
    "内容与主题": "分数/25",
    "结构与逻辑": "分数/25",
    "语言表达": "分数/25",
    "创新与情感": "分数/25"
  },
  "strengths": ["优点描述1", "优点描述2"],
  "weaknesses": ["不足描述1"],
  "suggestions": "3-5句具体、可操作的专业改进建议",
  "inspiring_questions": ["启发性问题1", "启发性问题2", "启发性问题3"],
  "encouragement": "温暖鼓励的话语"
}

现在开始批改作文，只返回JSON。"""

# ==================== 数据模型 ====================
class CompositionRequest(BaseModel):
    content: str
    grade: str = "中年级"
    student_id: Optional[str] = "default_student"

class CompositionResponse(BaseModel):
    total_score: int
    dimension_scores: Dict[str, str]
    strengths: List[str]
    weaknesses: List[str]
    suggestions: str
    inspiring_questions: List[str]
    encouragement: str

# ==================== 核心批改函数 ====================
async def call_qwen_for_correction(content: str):
    user_prompt = f"请严格按照JSON格式批改以下作文：\n{content}"

    response = client.chat.completions.create(
        model="qwen-turbo",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.55,      # 降低随机性，提高稳定性
        max_tokens=1400,
    )
    return response.choices[0].message.content

# ==================== 主接口（性能优化版） ====================
@app.post("/api/composition/correct", response_model=CompositionResponse)
async def correct_composition(request: CompositionRequest):
    global request_count, cache_hit_count, total_response_time
    start_time = time.time()
    request_count += 1

    # 生成缓存 Key（更精准）
    cache_key = f"{request.student_id}:{request.grade}:{hash(request.content[:500])}"

    # 1. 缓存命中
    if cache_key in composition_cache:
        cache_hit_count += 1
        hit_time = time.time() - start_time
        print(f"【缓存命中】学生 {request.student_id} | 耗时: {hit_time:.3f}秒")
        return composition_cache[cache_key]

    # 2. 调用模型
    try:
        content = request.content.replace("\r\n", "\n").replace("\r", "\n")
        result_text = await call_qwen_for_correction(content)

        # 清理 JSON
        cleaned = result_text.strip()
        if cleaned.startswith("```"):
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

        # 存入缓存
        composition_cache[cache_key] = response_data

        # 性能统计
        cost_time = time.time() - start_time
        total_response_time += cost_time
        avg_time = total_response_time / request_count

        print(f"【批改完成】学生 {request.student_id} | 总分: {response_data.total_score} | 耗时: {cost_time:.2f}秒 | 平均: {avg_time:.2f}秒 | 缓存命中率: {cache_hit_count/request_count*100:.1f}%")

        return response_data

    except Exception as e:
        print(f"【错误】批改失败: {e}")
        default_response = CompositionResponse(
            total_score=75,
            dimension_scores={},
            strengths=["作文已接收"],
            weaknesses=[],
            suggestions="系统处理异常，请稍后重试",
            inspiring_questions=[],
            encouragement="坚持就是胜利！你已经迈出了重要一步！"
        )
        return default_response

# ==================== 历史记录接口 ====================
@app.get("/api/history/{student_id}")
async def get_history(student_id: str, limit: int = 10):
    """获取学生批改历史"""
    # 这里可以后续接入数据库，目前使用内存
    # 模拟返回
    return []

# ==================== 健康检查 + 性能监控 ====================
@app.get("/health")
async def health():
    avg_time = total_response_time / request_count if request_count > 0 else 0
    return {
        "status": "ok",
        "version": "1.0",
        "message": "性能优化版服务正常运行",
        "total_requests": request_count,
        "cache_hit_rate": f"{cache_hit_count/request_count*100:.1f}%" if request_count > 0 else "0%",
        "avg_response_time": f"{avg_time:.2f}秒",
        "timestamp": time.time()
    }

# ==================== 启动 ====================
if __name__ == "__main__":
    import uvicorn
    print("🚀 启动中小学生学习助手 - 性能优化版 v1.0...")
    print("访问地址: http://0.0.0.0:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)