from typing import Optional
from sqlmodel import Field, SQLModel, create_engine, Session
from datetime import datetime
import uuid

from config import settings

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)


# 基础模型类
class BaseModel(SQLModel):
    """所有模型的基类"""
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now, index=True)
    updated_at: datetime = Field(default_factory=datetime.now, index=True)
    
    class Config:
        arbitrary_types_allowed = True


# 会话上下文管理器
def get_session():
    with Session(engine) as session:
        yield session


# 创建所有数据库表
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


if __name__ == "__main__":
    # 手动运行此文件时创建数据库和表
    create_db_and_tables()
    print("数据库表已创建")