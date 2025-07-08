from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime
from typing import List, Optional, Dict, Any
from database import BaseModel
from apps.users.models import User


class CalculationTestSession(BaseModel, table=True):
    """计算流畅性测试会话模型，记录单次测试的整体情况"""

    __tablename__ = "calc_test_sessions"

    user_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    is_completed: bool = Field(default=False)
    total_time_seconds: Optional[int] = None  # 测试总耗时（秒）
    grade_level: int = Field(default=1)  # 年级水平（1-7）
    progress: int = Field(default=0)  # 进度（已完成的题目数量）
    total_questions: int = Field(default=40)  # 总题目数量
    correct_count: int = Field(default=0)  # 正确答题数量
    total_score: int = Field(default=0)  # 总得分
    max_score: int = Field(default=40)  # 最高可能得分

    # 关系
    user: Optional[User] = Relationship()
    problems: List["CalculationProblem"] = Relationship(back_populates="test_session")

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
    
    @property
    def score_percentage(self) -> float:
        """计算得分率"""
        if self.max_score == 0:
            return 0.0
        return (self.total_score / self.max_score) * 100.0


class CalculationProblem(BaseModel, table=True):
    """计算题目记录模型，记录单个计算题的回答情况"""

    __tablename__ = "calc_problems"

    user_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    test_session_id: Optional[int] = Field(
        default=None, foreign_key="calc_test_sessions.id", index=True
    )
    problem_index: int = Field(index=True)  # 题目序号（从1开始）
    problem_text: str = Field()  # 题目文本，如 "1 + 3 = "
    problem_type: Optional[str] = Field(default=None, index=True)  # 题目类型，如 "addition", "multiplication", "fraction" 等
    correct_answer: str = Field()  # 正确答案（支持分数格式：a+b/c）
    user_answer: Optional[str] = None  # 用户答案（支持分数格式：a+b/c）
    is_correct: Optional[bool] = None  # 是否正确
    response_time: int = Field(default=0)  # 回答时间（毫秒）
    score: int = Field(default=0)  # 得分: 1分(正确), 0分(错误或未答)

    # 关系
    user: Optional[User] = Relationship()
    test_session: Optional[CalculationTestSession] = Relationship(back_populates="problems")


# 数据传输对象（DTO）
class ProblemData(SQLModel):
    """计算题目数据传输对象"""

    user_id: int
    test_session_id: int
    problem_index: int
    problem_text: str
    problem_type: Optional[str] = None
    correct_answer: str
    user_answer: str
    response_time: int


class BatchProblemData(SQLModel):
    """批量计算题目数据传输对象"""

    user_id: int
    test_session_id: int
    problems: List[Dict[str, Any]]  # 包含所有题目的答案数据


class TestSessionCreate(SQLModel):
    """创建测试会话的请求模型"""

    user_id: int
    grade_level: int
    total_questions: int = 40


class TestSessionUpdate(SQLModel):
    """更新测试会话的请求模型"""

    is_completed: Optional[bool] = None
    progress: Optional[int] = None
    correct_count: Optional[int] = None
    total_score: Optional[int] = None
    end_time: Optional[datetime] = None


class TestSessionResponse(SQLModel):
    """测试会话响应模型"""

    id: int
    user_id: int
    start_time: datetime
    end_time: Optional[datetime]
    is_completed: bool
    total_time_seconds: Optional[int]
    grade_level: int
    progress: int
    total_questions: int
    correct_count: int
    total_score: int
    max_score: int
    accuracy: float
    completion_rate: float
    score_percentage: float


class ResultResponse(SQLModel):
    """结果响应模型"""

    user: User
    session: CalculationTestSession
    problems: List[CalculationProblem]
    stats: Dict[str, Any]