from openai import OpenAI
from app.core.config import settings
from app.llm.prompts import SYSTEM_PROMPT  

client = OpenAI(
    api_key=settings.BAILIAN_API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

async def call_qwen(作文内容: str, model: str = None):
    """调用 Qwen 模型进行作文批改（使用 v0.5 Prompt）"""
    model = model or settings.MODEL_NAME
    
    user_prompt = f"请严格按照JSON格式批改以下作文：\n{作文内容}"

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.6,
        max_tokens=1500,
    )
    return response.choices[0].message.content
