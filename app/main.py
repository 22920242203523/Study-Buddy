import json
from fastapi import FastAPI, APIRouter
from pydantic import BaseModel
from app.core.config import settings
from app.llm.client import call_qwen
from app.utils.response import CompositionResponse   

app = FastAPI(title="中小学生学习助手 - AI 后端")

# 创建路由
router = APIRouter()

class CompositionRequest(BaseModel):
    content: str
    grade: str = "中年级"

@router.post("/api/composition/correct", response_model=CompositionResponse)
async def correct_composition(request: CompositionRequest):
    print(f"收到作文请求，长度: {len(request.content)} 字符")

    try:
        content = request.content.replace("\r\n", "\n").replace("\r", "\n")
        
        result_text = await call_qwen(content)
        print("=== LLM 原始返回 ===")
        print(result_text)
        print("=== 原始返回结束 ===")

        # 清理
        cleaned = result_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned.split("```json")[1].split("```")[0]
        elif cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]

        result = json.loads(cleaned)

        return CompositionResponse(
            total_score=result.get("total_score", 80),
            dimension_scores=result.get("dimension_scores", {}),
            strengths=result.get("strengths", []),
            weaknesses=result.get("weaknesses", []),
            suggestions=result.get("suggestions", "暂无具体建议"),
            inspiring_questions=result.get("inspiring_questions", []),
            encouragement=result.get("encouragement", "继续努力，你会越来越好！")
        )

    except Exception as e:
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        if 'result_text' in locals():
            print("原始返回内容:", result_text)
        return CompositionResponse(
            total_score=75,
            dimension_scores={},
            strengths=["作文已接收"],
            weaknesses=[],
            suggestions="系统正在优化 Prompt，请稍后重试",
            inspiring_questions=[],
            encouragement="坚持就是胜利！你已经迈出了重要一步！"
        )

# 注册路由
app.include_router(router)

# 健康检查
@app.get("/health")
async def health():
    return {"status": "ok", "message": "中小学生学习助手后端服务正常运行"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)