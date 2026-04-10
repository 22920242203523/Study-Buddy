from pydantic import BaseModel
from typing import List, Dict, Optional

class StandardResponse(BaseModel):
    """统一响应格式"""
    code: int = 200
    message: str = "success"
    data: Optional[Dict] = None


class CompositionResponse(BaseModel):
    """作文批改响应模型"""
    total_score: int
    dimension_scores: Dict[str, str]
    strengths: List[str]
    weaknesses: List[str]
    suggestions: str
    inspiring_questions: List[str]
    encouragement: str


# 可选：统一成功响应函数
def success_response(data: Dict):
    return StandardResponse(code=200, message="success", data=data)


def error_response(message: str, code: int = 400):
    return StandardResponse(code=code, message=message)