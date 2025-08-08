from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Text
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from database import BaseModel
from apps.users.models import User


class TestStatus(str, Enum):
    """测试状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class LiteracyTest(BaseModel, table=True):
    """识字量测验会话模型"""

    __tablename__ = "literacy_tests"

    user_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    status: TestStatus = Field(default=TestStatus.PENDING)
    
    # 测试结果统计
    total_characters: int = Field(default=0)  # 总字数
    correct_characters: int = Field(default=0)  # 正确字数
    total_score: Optional[float] = None  # 总得分
    
    # 各组得分详情
    group_scores: Optional[str] = Field(default=None, sa_column=Text)  # JSON格式存储各组得分
    
    # 评测状态
    evaluation_status: str = Field(default="pending")
    evaluation_completed_at: Optional[datetime] = None
    
    # 关系
    user: Optional[User] = Relationship()
    audio_records: List["LiteracyAudioRecord"] = Relationship(back_populates="test")

    @property
    def accuracy_rate(self) -> float:
        """计算准确率"""
        if self.total_characters == 0:
            return 0.0
        return (self.correct_characters / self.total_characters) * 100


class LiteracyAudioRecord(BaseModel, table=True):
    """识字量音频记录模型"""

    __tablename__ = "literacy_audio_records"

    test_id: Optional[int] = Field(default=None, foreign_key="literacy_tests.id", index=True)
    character: str = Field(max_length=10)  # 朗读的字符
    group_id: int = Field()  # 字符组ID
    coefficient: float = Field()  # 该组系数
    
    # 录音文件信息
    audio_file_path: Optional[str] = Field(default=None, max_length=500)
    audio_duration: Optional[float] = None  # 录音时长（秒）
    file_size: Optional[int] = None  # 文件大小（字节）
    
    # 评测结果
    is_correct: Optional[bool] = None  # 是否朗读正确
    confidence_score: Optional[float] = None  # 置信度分数
    evaluation_result_path: Optional[str] = Field(default=None, max_length=500)  # 评测结果文件路径
    
    # 评测状态
    evaluation_status: str = Field(default="pending")  # pending, processing, completed, failed
    evaluation_started_at: Optional[datetime] = None
    evaluation_completed_at: Optional[datetime] = None
    error_message: Optional[str] = Field(default=None, sa_column=Text)
    
    # 关系
    test: Optional[LiteracyTest] = Relationship(back_populates="audio_records")

    @property
    def score_contribution(self) -> float:
        """计算该记录对总分的贡献"""
        if self.is_correct:
            return self.coefficient
        return 0.0