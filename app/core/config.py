from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    BAILIAN_API_KEY: str
    OPENAI_API_KEY: str = None   # 兼容使用

    MODEL_NAME: str = "qwen-turbo"

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore'          # 重要：忽略多余字段

# 创建全局配置实例
settings = Settings()