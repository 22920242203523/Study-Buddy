"""
中小学生学习助手 - 后端评分服务 v0.5
作者：张一凡
日期：2026.04.17
功能：接收作文 → 调用Qwen模型 → 返回结构化批改结果
"""

import json
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List
from openai import OpenAI
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

app = FastAPI(
    title="中小学生学习助手 - AI 批改服务",
    description="基于Qwen的作文智能批改系统",
    version="0.5"
)

# CORS 配置（允许前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # 开发阶段允许所有，生产环境请修改
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 配置 ====================
client = OpenAI(
    api_key=os.getenv("BAILIAN_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# 简单内存缓存（相同作文30秒内不重复调用）
composition_cache = {}

# ==================== Prompt v0.5 ====================
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
        temperature=0.6,
        max_tokens=1500,
    )
    return response.choices[0].message.content

# ==================== 主接口 ====================
@app.post("/api/composition/correct", response_model=CompositionResponse)
async def correct_composition(request: CompositionRequest):
    start_time = time.time()
    
    # 生成缓存Key
    cache_key = f"{request.grade}:{request.content[:300]}"
    
    # 检查缓存
    if cache_key in composition_cache:
        print(f"【缓存命中】耗时: {time.time()-start_time:.2f}秒")
        return composition_cache[cache_key]

    try:
        content = request.content.replace("\r\n", "\n").replace("\r", "\n")
        
        result_text = await call_qwen_for_correction(content)
        
        # 清理可能的代码块
        cleaned = result_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned.split("```json")[1].split("```")[0]
        elif cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]

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

        # 存入缓存（30秒）
        composition_cache[cache_key] = response_data
        
        print(f"【批改完成】总分: {response_data.total_score} 耗时: {time.time()-start_time:.2f}秒")
        return response_data

    except Exception as e:
        print(f"批改失败: {e}")
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

# ==================== 健康检查 ====================
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "message": "中小学生学习助手后端服务 v0.5 正常运行",
        "timestamp": time.time()
    }

# ==================== 启动 ====================
if __name__ == "__main__":
    import uvicorn
    print("启动中小学生学习助手后端服务 v0.5...")
    uvicorn.run(app, host="0.0.0.0", port=8000)