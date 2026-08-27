from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime, date
from typing import List, Optional
from database import BaseModel


class User(BaseModel, table=True):
    """用户（学生）模型"""
    __tablename__ = "users"

    name: str = Field(index=True)
    school: str = Field(index=True)
    grade: int = Field(index=True)
    class_number: int = Field(index=True)
    birth_date: Optional[date] = Field(default=None, index=True)  # 出生日期
    # 学号（可选）：登记一次后凭学号快速登录，历史用户没有学号也不受影响
    student_id: Optional[str] = Field(default=None, index=True, unique=True, max_length=64)
    # 测验序号：本次是该学生的第几次测验，登录时填写，便于前后测数据比对
    test_round: Optional[int] = Field(default=None, index=True)
    # 最近一次登录（开始测验）的时间，登录时自动记录
    last_login_at: Optional[datetime] = Field(default=None, index=True)