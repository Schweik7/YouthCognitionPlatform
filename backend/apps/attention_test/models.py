from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime
from typing import List, Optional, Dict, Any
from database import BaseModel
from apps.users.models import User


class AttentionTestSession(BaseModel, table=True):
    """注意力筛查测试会话模型，记录单次测试的整体情况"""

    __tablename__ = "at_test_sessions"

    user_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    is_completed: bool = Field(default=False)
    total_time_seconds: Optional[int] = None  # 测试总耗时（秒）
    target_symbol: str = Field(default="Ψ")  # 目标符号
    correct_count: int = Field(default=0)  # 正确点击数量
    incorrect_count: int = Field(default=0)  # 错误点击数量
    missed_count: int = Field(default=0)  # 遗漏数量
    total_score: float = Field(default=0.0)  # 最终得分

    # 关系
    user: Optional[User] = Relationship()
    records: List["AttentionRecord"] = Relationship(back_populates="test_session")

    @property
    def accuracy(self) -> float:
        """计算准确率"""
        total = self.correct_count + self.incorrect_count
        if total == 0:
            return 0.0
        return (self.correct_count / total) * 100.0


class AttentionRecord(BaseModel, table=True):
    """注意力筛查测试记录模型，只记录用户点击的位置"""

    __tablename__ = "at_records"

    user_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    test_session_id: Optional[int] = Field(
        default=None, foreign_key="at_test_sessions.id", index=True
    )
    row_index: int = Field(index=True)  # 行索引
    col_index: int = Field(index=True)  # 列索引
    symbol: str = Field(default="")  # 实际符号
    is_target: bool = Field(default=False)  # 是否是目标符号
    is_correct: bool = Field(default=False)  # 点击是否正确（是否点击了目标符号）
    response_time: Optional[int] = None  # 响应时间（毫秒，从行显示到点击的时间）

    # 关系
    user: Optional[User] = Relationship()
    test_session: Optional[AttentionTestSession] = Relationship(back_populates="records")


# 数据传输对象（DTO）
class AttentionRecordCreate(SQLModel):
    """创建注意力测试记录的请求模型"""

    user_id: int
    test_session_id: int
    row_index: int
    col_index: int
    symbol: str
    is_target: bool
    response_time: Optional[int] = None


class AttentionClickedRecordsCreate(SQLModel):
    """批量创建用户点击记录的请求模型"""

    user_id: int
    test_session_id: int
    clicked_positions: List[Dict[str, Any]]  # 包含点击位置的列表


class AttentionSessionCreate(SQLModel):
    """创建注意力测试会话的请求模型"""

    user_id: int
    target_symbol: str = "Ψ"


class AttentionSessionUpdate(SQLModel):
    """更新注意力测试会话的请求模型"""

    is_completed: Optional[bool] = None
    end_time: Optional[datetime] = None
    correct_count: Optional[int] = None
    incorrect_count: Optional[int] = None
    missed_count: Optional[int] = None
    total_score: Optional[float] = None


class AttentionSessionResponse(SQLModel):
    """注意力测试会话响应模型"""

    id: int
    user_id: int
    start_time: datetime
    end_time: Optional[datetime]
    is_completed: bool
    total_time_seconds: Optional[int]
    target_symbol: str
    correct_count: int
    incorrect_count: int
    missed_count: int
    total_score: float
    accuracy: float


class AttentionResultResponse(SQLModel):
    """注意力测试结果响应模型"""

    user: User
    session: AttentionTestSession
    records: List[AttentionRecord]
    stats: Dict[str, Any]


class SymbolRowResponse(SQLModel):
    """符号行响应模型"""

    row_index: int
    symbols: List[Dict[str, Any]]
