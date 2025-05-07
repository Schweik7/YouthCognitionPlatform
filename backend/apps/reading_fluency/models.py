from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime
from typing import List, Optional
from database import BaseModel
from apps.users.models import User


class Trial(BaseModel, table=True):
    """试验记录模型"""

    __tablename__ = "rf_trials"

    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    trial_id: int = Field(index=True)
    user_answer: bool = Field(default=False)
    response_time: int = Field(default=0)  # 以毫秒为单位

    # 关系
    user: Optional[User] = Relationship()


class TrialData(SQLModel):
    """试验数据传输对象"""

    user_id: int
    trial_id: int
    user_answer: bool
    response_time: int


class UserTrialData(SQLModel):
    """包含用户信息的试验数据传输对象（向后兼容）"""

    name: str
    school: str
    grade: int
    class_number: int
    trial_id: int
    user_answer: bool
    response_time: int


class ResultResponse(SQLModel):
    """结果响应模型"""

    user: User
    results: dict
    trials: List[Trial]
