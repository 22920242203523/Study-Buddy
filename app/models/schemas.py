from pydantic import BaseModel
from typing import List, Dict, Union

class CompositionRequest(BaseModel):
    content: str
    grade: str = "中年级"   # 低年级 / 中年级 / 高年级

class CompositionResponse(BaseModel):
    total_score: int
    dimension_scores: Dict[str, str]
    strengths: List[str]
    weaknesses: List[str]
    suggestions: Union[str, List[str]]   # 支持字符串或列表
    inspiring_questions: List[str]
    encouragement: str