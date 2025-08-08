import os
from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    """应用配置类"""

    # 基础设置
    APP_NAME: str = "认知能力评估平台"
    API_PREFIX: str = "/api"
    DEBUG: bool = False
    PORT: int = 3000

    # 数据库设置
    DB_USER: str = "meng"
    DB_PASSWORD: str = "meng123456"
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "appdb"
    DATABASE_URL: Optional[str] = None

    # 安全设置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # CORS设置
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # 文件路径设置
    DATA_DIR: str = "data"
    UPLOAD_DIR: str = "uploads"
    
    # 科大讯飞语音评测API设置
    XFYUN_HOST_URL: str = "ws://ise-api.xfyun.cn/v2/open-ise"
    XFYUN_APP_ID: str = "e96b71cc"
    XFYUN_API_KEY: str = "c596bae72326e35a645eca27bf9d235a"
    XFYUN_API_SECRET: str = "YTM0YzkxYTk1MWQzOTdkZDg3Zjg0MTQx"

    def __init__(self, **data):
        super().__init__(**data)
        # 构建数据库URL
        if not self.DATABASE_URL:
            self.DATABASE_URL = f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 创建设置实例
settings = Settings()

# 上传目录配置
from pathlib import Path
UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# 确保数据目录存在
os.makedirs(settings.DATA_DIR, exist_ok=True)
