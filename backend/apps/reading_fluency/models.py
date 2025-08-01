from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from database import BaseModel
from apps.users.models import User


class TestStatus(str, Enum):
    """测试状态枚举"""
    PENDING = "pending"      # 待开始
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失败


class ReadingFluencyTest(BaseModel, table=True):
    """朗读流畅性测试会话模型"""

    __tablename__ = "reading_fluency_tests"  # type: ignore

    user_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    status: TestStatus = Field(default=TestStatus.PENDING)
    
    # 第一轮测试结果
    round1_duration: Optional[int] = None  # 第一轮用时（秒）
    round1_character_count: Optional[int] = None  # 第一轮正确朗读字数
    round1_completed: bool = Field(default=False)
    
    # 第二轮测试结果
    round2_duration: Optional[int] = None  # 第二轮用时（秒）
    round2_character_count: Optional[int] = None  # 第二轮正确朗读字数
    round2_completed: bool = Field(default=False)
    
    # 最终成绩
    average_score: Optional[float] = None  # 平均成绩（字/分钟）
    total_audio_files: int = Field(default=0)  # 音频文件总数
    
    # 评测状态
    evaluation_status: str = Field(default="pending")  # pending, processing, completed, failed
    evaluation_completed_at: Optional[datetime] = None
    
    # 关系
    user: Optional[User] = Relationship()
    audio_records: List["ReadingAudioRecord"] = Relationship(back_populates="test")

    @property
    def is_completed(self) -> bool:
        """是否完成测试"""
        return self.round1_completed and self.round2_completed

    @property
    def total_duration(self) -> int:
        """总用时"""
        duration = 0
        if self.round1_duration:
            duration += self.round1_duration
        if self.round2_duration:
            duration += self.round2_duration
        return duration

    @property
    def total_character_count(self) -> int:
        """总朗读字数"""
        count = 0
        if self.round1_character_count:
            count += self.round1_character_count
        if self.round2_character_count:
            count += self.round2_character_count
        return count


class ReadingAudioRecord(BaseModel, table=True):
    """朗读音频记录模型"""

    __tablename__ = "reading_audio_records"  # type: ignore

    test_id: Optional[int] = Field(default=None, foreign_key="reading_fluency_tests.id", index=True)
    round_number: int = Field(index=True)  # 轮次：1或2
    row_index: int = Field(index=True)  # 行索引：0-17
    audio_file_path: str  # 音频文件路径
    upload_time: datetime = Field(default_factory=datetime.now)
    
    # 语音评测结果
    evaluation_status: str = Field(default="pending")  # pending, processing, completed, failed
    evaluation_result: Optional[str] = Field(default=None)  # JSON字符串存储详细结果
    total_score: Optional[float] = None
    phone_score: Optional[float] = None
    tone_score: Optional[float] = None
    fluency_score: Optional[float] = None
    integrity_score: Optional[float] = None
    correct_character_count: Optional[int] = None  # 该行正确朗读的字数
    
    # 关系
    test: Optional[ReadingFluencyTest] = Relationship(back_populates="audio_records")


# 数据传输对象（DTO）
class ReadingFluencyTestCreate(SQLModel):
    """创建朗读流畅性测试的请求模型"""
    user_id: int


class RoundResult(SQLModel):
    """单轮测试结果"""
    duration: int  # 用时（秒）
    characterCount: int  # 朗读字数
    audioFileCount: int  # 音频文件数量


class ReadingFluencySubmission(SQLModel):
    """朗读流畅性测试提交数据"""
    testType: str
    results: Dict[str, Any]  # 包含round1和round2的结果


class ReadingFluencyTestResponse(SQLModel):
    """朗读流畅性测试响应模型"""
    id: int
    user_id: int
    start_time: datetime
    end_time: Optional[datetime]
    status: TestStatus
    round1_duration: Optional[int]
    round1_character_count: Optional[int]
    round1_completed: bool
    round2_duration: Optional[int]
    round2_character_count: Optional[int]
    round2_completed: bool
    average_score: Optional[float]
    total_audio_files: int
    evaluation_status: str
    is_completed: bool
    total_duration: int
    total_character_count: int


class AudioRecordResponse(SQLModel):
    """音频记录响应模型"""
    id: int
    test_id: int
    round_number: int
    row_index: int
    audio_file_path: str
    upload_time: datetime
    evaluation_status: str
    total_score: Optional[float]
    phone_score: Optional[float]
    tone_score: Optional[float]
    fluency_score: Optional[float]
    integrity_score: Optional[float]
    correct_character_count: Optional[int]


class TestResultSummary(SQLModel):
    """测试结果摘要"""
    test_id: int
    user_name: str
    total_duration: int
    round1_score: int
    round2_score: int
    average_score: float
    completion_time: datetime
    audio_files_count: int
    evaluation_completion_rate: float