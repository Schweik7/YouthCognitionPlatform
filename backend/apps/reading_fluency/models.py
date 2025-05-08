from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime
from typing import List, Optional
from database import BaseModel
from apps.users.models import User


class TestSession(BaseModel, table=True):
    """测试会话模型，记录单次测试的整体情况"""

    __tablename__ = "rf_test_sessions"

    user_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    is_completed: bool = Field(default=False)
    total_time_seconds: Optional[int] = None  # 测试总耗时（秒）
    progress: int = Field(default=0)  # 进度（已完成的试题数量）
    total_questions: int = Field(default=0)  # 总题目数量
    correct_count: int = Field(default=0)  # 正确答题数量

    # 关系
    user: Optional[User] = Relationship()
    trials: List["Trial"] = Relationship(back_populates="test_session")

    @property
    def accuracy(self) -> float:
        """计算正确率"""
        if self.progress == 0:
            return 0.0
        return (self.correct_count / self.progress) * 100.0

    @property
    def completion_rate(self) -> float:
        """计算完成率"""
        if self.total_questions == 0:
            return 0.0
        return (self.progress / self.total_questions) * 100.0


class Trial(BaseModel, table=True):
    """试验记录模型，记录单个试题的回答情况"""

    __tablename__ = "rf_trials"

    user_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    test_session_id: Optional[int] = Field(
        default=None, foreign_key="rf_test_sessions.id", index=True
    )
    trial_id: int = Field(index=True)  # 试题编号
    user_answer: bool = Field(default=False)  # 用户回答
    is_correct: Optional[bool] = None  # 是否正确
    response_time: int = Field(default=0)  # 回答时间（毫秒）

    # 关系
    user: Optional[User] = Relationship()
    test_session: Optional[TestSession] = Relationship(back_populates="trials")


# 数据传输对象（DTO）
class TrialData(SQLModel):
    """试验数据传输对象"""

    user_id: int
    test_session_id: Optional[int] = None
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
    timestamp: Optional[datetime] = None  # 可选的时间戳字段


class TestSessionCreate(SQLModel):
    """创建测试会话的请求模型"""

    user_id: int
    total_questions: int = 0


class TestSessionUpdate(SQLModel):
    """更新测试会话的请求模型"""

    is_completed: Optional[bool] = None
    progress: Optional[int] = None
    correct_count: Optional[int] = None
    end_time: Optional[datetime] = None


class TestSessionResponse(SQLModel):
    """测试会话响应模型"""

    id: int
    user_id: int
    start_time: datetime
    end_time: Optional[datetime]
    is_completed: bool
    total_time_seconds: Optional[int]
    progress: int
    total_questions: int
    correct_count: int
    accuracy: float
    completion_rate: float


class ResultResponse(SQLModel):
    """结果响应模型"""

    user: User
    results: dict
    trials: List[Trial]
