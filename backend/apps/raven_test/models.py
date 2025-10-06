from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime
from typing import List, Optional, Dict, Any
from database import BaseModel
from apps.users.models import User


class RavenTestSession(BaseModel, table=True):
    """瑞文智力测验会话模型，记录单次测试的整体情况"""

    __tablename__ = "raven_test_sessions"  # type: ignore

    user_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    is_completed: bool = Field(default=False)
    total_time_seconds: Optional[int] = None  # 测试总耗时（秒）

    # 当前进度（用于继续未完成的测试）
    current_question: int = Field(default=0)  # 当前题目索引（0-71）

    # 测试结果
    raw_score: int = Field(default=0)  # 原始分数（正确题目数）
    percentile: Optional[float] = None  # 百分位
    z_score: Optional[float] = None  # Z分数
    iq: Optional[int] = None  # 智商

    # 用户年龄（测试时的年龄，岁）
    user_age: Optional[float] = None

    # 关系
    user: Optional[User] = Relationship()
    answers: List["RavenAnswer"] = Relationship(back_populates="test_session")


class RavenAnswer(BaseModel, table=True):
    """瑞文测验答题记录模型"""

    __tablename__ = "raven_answers"  # type: ignore

    user_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    test_session_id: Optional[int] = Field(
        default=None, foreign_key="raven_test_sessions.id", index=True
    )

    question_id: int = Field(index=True)  # 题目ID（1-72）
    group_name: str = Field(index=True)  # 组名（A, AB, B, C, D, E）
    user_answer: int  # 用户选择的选项（1-6或1-8）
    correct_answer: int  # 正确答案
    is_correct: bool = Field(default=False)  # 是否正确
    response_time: Optional[int] = None  # 答题时间（毫秒）

    # 关系
    user: Optional[User] = Relationship()
    test_session: Optional[RavenTestSession] = Relationship(back_populates="answers")


# 数据传输对象（DTO）
class RavenSessionCreate(SQLModel):
    """创建瑞文测试会话的请求模型"""
    user_id: int


class RavenSessionUpdate(SQLModel):
    """更新瑞文测试会话的请求模型"""
    is_completed: Optional[bool] = None
    end_time: Optional[datetime] = None
    current_question: Optional[int] = None
    raw_score: Optional[int] = None
    percentile: Optional[float] = None
    z_score: Optional[float] = None
    iq: Optional[int] = None


class RavenAnswerCreate(SQLModel):
    """创建答题记录的请求模型"""
    user_id: int
    test_session_id: int
    question_id: int
    user_answer: int
    response_time: Optional[int] = None


class RavenAnswerBatchCreate(SQLModel):
    """批量创建答题记录的请求模型"""
    user_id: int
    test_session_id: int
    answers: List[Dict[str, Any]]  # [{question_id, user_answer, response_time}, ...]


class RavenSessionResponse(SQLModel):
    """瑞文测试会话响应模型"""
    id: int
    user_id: int
    start_time: datetime
    end_time: Optional[datetime]
    is_completed: bool
    total_time_seconds: Optional[int]
    current_question: int
    raw_score: int
    percentile: Optional[float]
    z_score: Optional[float]
    iq: Optional[int]
    user_age: Optional[float]


class RavenResultResponse(SQLModel):
    """瑞文测试结果响应模型"""
    user: User
    session: RavenTestSession
    answers: List[RavenAnswer]
    stats: Dict[str, Any]


class QuestionInfo(SQLModel):
    """题目信息模型"""
    question_id: int
    group_name: str
    question_in_group: int  # 组内题号（1-12）
    num_options: int  # 选项数量（6或8）
    main_image_url: str  # 主图片URL
    option_image_urls: List[str]  # 选项图片URL列表
    user_answer: Optional[int] = None  # 用户已选答案（如果有）
