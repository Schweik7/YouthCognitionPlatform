from typing import List, Optional
from sqlmodel import SQLModel
from datetime import datetime, date


class UserBase(SQLModel):
    """用户基础数据结构"""
    name: str
    school: str
    grade: int
    class_number: int
    birth_date: Optional[date] = None


class UserCreate(UserBase):
    """创建用户请求模型"""
    pass


class UserResponse(UserBase):
    """用户响应模型"""
    id: int
    created_at: datetime
    updated_at: datetime


class SchoolsResponse(SQLModel):
    """学校列表响应模型"""
    schools: List[str]