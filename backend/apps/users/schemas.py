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
    student_id: Optional[str] = None
    test_round: Optional[int] = None
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class UserRegister(UserBase):
    """首次登记请求模型：在基本信息之外附带学号"""
    student_id: str


class UserLogin(SQLModel):
    """登录请求模型：学号 + 姓名双重校验，并登记本次是第几次测验"""
    student_id: str
    name: str
    test_round: Optional[int] = None


class SchoolsResponse(SQLModel):
    """学校列表响应模型"""
    schools: List[str]