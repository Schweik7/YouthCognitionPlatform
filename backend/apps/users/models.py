from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime
from typing import List, Optional
from database import BaseModel


class User(BaseModel, table=True):
    """用户（学生）模型"""
    __tablename__ = "users"
    
    name: str = Field(index=True)
    school: str = Field(index=True)
    grade: int = Field(index=True)
    class_number: int = Field(index=True)