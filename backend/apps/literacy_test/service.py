import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlmodel import Session, select
from database import get_session
from config import UPLOAD_DIR
from .models import LiteracyTest, LiteracyAudioRecord, TestStatus
import uuid
from apps.oral_reading_fluency.xfyun_sdk import XfyunSpeechEvaluationSDK
from config import settings


# 加载识字量测验数据
def load_literacy_test_data() -> Dict[str, Any]:
    """加载识字量测验数据"""
    data_path = Path(__file__).parent.parent.parent / "data" / "literacy_test_data.json"
    with open(data_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_character_groups() -> List[Dict[str, Any]]:
    """获取所有字符组"""
    data = load_literacy_test_data()
    # 只返回有字符的组
    return [group for group in data["character_groups"] if group["characters"]]


def create_literacy_test(user_id: int) -> LiteracyTest:
    """创建新的识字量测验"""
    session_gen = get_session()
    session = next(session_gen)
    try:
        test = LiteracyTest(
            user_id=user_id,
            status=TestStatus.IN_PROGRESS
        )
        session.add(test)
        session.commit()
        session.refresh(test)
        return test
    finally:
        try:
            next(session_gen)
        except StopIteration:
            pass


def get_literacy_test(test_id: int) -> Optional[LiteracyTest]:
    """获取识字量测验"""
    session_gen = get_session()
    session = next(session_gen)
    try:
        return session.get(LiteracyTest, test_id)
    finally:
        try:
            next(session_gen)
        except StopIteration:
            pass


def save_audio_record(
    test_id: int,
    character: str,
    group_id: int,
    coefficient: float,
    audio_file_path: str,
    audio_duration: float,
    file_size: int
) -> LiteracyAudioRecord:
    """保存音频记录"""
    session_gen = get_session()
    session = next(session_gen)
    try:
        record = LiteracyAudioRecord(
            test_id=test_id,
            character=character,
            group_id=group_id,
            coefficient=coefficient,
            audio_file_path=audio_file_path,
            audio_duration=audio_duration,
            file_size=file_size
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return record
    finally:
        try:
            next(session_gen)
        except StopIteration:
            pass


def save_evaluation_result_file(xml_result: str, detailed_analysis: dict, audio_record_id: int) -> str:
    """保存评测结果到文件并返回文件路径"""
    results_dir = UPLOAD_DIR / "evaluation_results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"literacy_evaluation_{audio_record_id}_{timestamp}_{uuid.uuid4().hex[:8]}.json"
    file_path = results_dir / filename
    
    # 保存完整的评测结果
    result_data = {
        "audio_record_id": audio_record_id,
        "timestamp": timestamp,
        "xml_result": xml_result,
        "detailed_analysis": detailed_analysis,
        "evaluation_type": "literacy_test"
    }
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)
    
    return str(file_path.relative_to(UPLOAD_DIR))


async def evaluate_literacy_audio(audio_record_id: int):
    """异步评测识字量音频"""
    session_gen = get_session()
    session = next(session_gen)
    try:
        # 获取音频记录
        record = session.get(LiteracyAudioRecord, audio_record_id)
        if not record:
            return
        
        # 更新评测状态
        record.evaluation_status = "processing"
        record.evaluation_started_at = datetime.now()
        session.commit()
        
        try:
            # 构建音频文件完整路径
            audio_path = UPLOAD_DIR / record.audio_file_path
            
            # 初始化SDK
            sdk = XfyunSpeechEvaluationSDK(
                app_id=settings.XFYUN_APP_ID,
                api_key=settings.XFYUN_API_KEY,
                api_secret=settings.XFYUN_API_SECRET
            )
            
            # 调用语音评测API
            result = await sdk.evaluate_audio_file(
                audio_file_path=str(audio_path),
                text_content=record.character,  # 期望朗读的字符
                category="read_word"  # 单字朗读
            )
            
            # 解析评测结果
            is_correct = False
            confidence_score = 0.0
            
            if result.get("success", False):
                xml_result = result.get("data", "")
                detailed_analysis = result.get("analysis", {})
                
                # 保存详细结果到文件
                result_file_path = save_evaluation_result_file(
                    xml_result, detailed_analysis, audio_record_id
                )
                record.evaluation_result_path = result_file_path
                
                # 简单的正确性判断逻辑（可根据需要调整）
                if detailed_analysis:
                    total_score = detailed_analysis.get("total_score", 0)
                    confidence_score = total_score / 100.0 if total_score else 0.0
                    is_correct = total_score >= 60  # 60分以上认为正确
            else:
                # 评测失败
                error_msg = result.get("error", "评测服务异常")
                record.error_message = error_msg
                
                # 保存错误信息到文件
                error_data = {
                    "audio_record_id": audio_record_id,
                    "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                    "error_message": error_msg,
                    "evaluation_type": "literacy_test"
                }
                
                results_dir = UPLOAD_DIR / "evaluation_results"
                results_dir.mkdir(parents=True, exist_ok=True)
                filename = f"literacy_error_{audio_record_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                error_file_path = results_dir / filename
                
                with open(error_file_path, 'w', encoding='utf-8') as f:
                    json.dump(error_data, f, ensure_ascii=False, indent=2)
                
                record.evaluation_result_path = str(error_file_path.relative_to(UPLOAD_DIR))
            
            # 更新记录
            record.is_correct = is_correct
            record.confidence_score = confidence_score
            record.evaluation_status = "completed" if result.get("success", False) else "failed"
            record.evaluation_completed_at = datetime.now()
            
            session.commit()
            
            # 检查是否所有音频都评测完成，如果是则更新测验状态
            await update_test_completion_status(record.test_id)
            
        except Exception as e:
            # 处理异常
            record.evaluation_status = "failed"
            record.error_message = str(e)
            record.evaluation_completed_at = datetime.now()
            session.commit()
    finally:
        try:
            next(session_gen)
        except StopIteration:
            pass


async def update_test_completion_status(test_id: int):
    """更新测验完成状态"""
    session_gen = get_session()
    session = next(session_gen)
    try:
        test = session.get(LiteracyTest, test_id)
        if not test:
            return
        
        # 获取所有音频记录
        stmt = select(LiteracyAudioRecord).where(LiteracyAudioRecord.test_id == test_id)
        audio_records = session.exec(stmt).all()
        
        if not audio_records:
            return
        
        # 检查是否所有评测都完成
        all_completed = all(
            record.evaluation_status in ["completed", "failed"] 
            for record in audio_records
        )
        
        if all_completed:
            # 计算总分和统计
            correct_count = sum(1 for record in audio_records if record.is_correct)
            total_count = len(audio_records)
            
            # 按组统计得分
            group_scores = {}
            total_score = 0.0
            
            for record in audio_records:
                group_id = record.group_id
                if group_id not in group_scores:
                    group_scores[group_id] = {
                        "total_characters": 0,
                        "correct_characters": 0,
                        "coefficient": record.coefficient,
                        "score": 0.0
                    }
                
                group_scores[group_id]["total_characters"] += 1
                if record.is_correct:
                    group_scores[group_id]["correct_characters"] += 1
                    group_scores[group_id]["score"] += record.coefficient
                    total_score += record.coefficient
            
            # 更新测验记录
            test.total_characters = total_count
            test.correct_characters = correct_count
            test.total_score = total_score
            test.group_scores = json.dumps(group_scores, ensure_ascii=False)
            test.status = TestStatus.COMPLETED
            test.end_time = datetime.now()
            test.evaluation_status = "completed"
            test.evaluation_completed_at = datetime.now()
            
            session.commit()
    finally:
        try:
            next(session_gen)
        except StopIteration:
            pass


def get_test_results(test_id: int) -> Optional[Dict[str, Any]]:
    """获取测验结果"""
    session_gen = get_session()
    session = next(session_gen)
    try:
        test = session.get(LiteracyTest, test_id)
        if not test:
            return None
        
        # 获取音频记录
        stmt = select(LiteracyAudioRecord).where(LiteracyAudioRecord.test_id == test_id)
        audio_records = session.exec(stmt).all()
        
        # 解析组得分
        group_scores = {}
        if test.group_scores:
            try:
                group_scores = json.loads(test.group_scores)
            except:
                pass
        
        return {
            "test_id": test.id,
            "user_id": test.user_id,
            "start_time": test.start_time,
            "end_time": test.end_time,
            "status": test.status,
            "total_characters": test.total_characters,
            "correct_characters": test.correct_characters,
            "accuracy_rate": test.accuracy_rate,
            "total_score": test.total_score,
            "group_scores": group_scores,
            "evaluation_status": test.evaluation_status,
            "audio_records": [
                {
                    "id": record.id,
                    "character": record.character,
                    "group_id": record.group_id,
                    "coefficient": record.coefficient,
                    "is_correct": record.is_correct,
                    "confidence_score": record.confidence_score,
                    "evaluation_status": record.evaluation_status,
                    "audio_file_path": record.audio_file_path
                }
                for record in audio_records
            ]
        }
    finally:
        try:
            next(session_gen)
        except StopIteration:
            pass


def get_user_tests(user_id: int) -> List[Dict[str, Any]]:
    """获取用户的所有识字量测验"""
    session_gen = get_session()
    session = next(session_gen)
    try:
        stmt = select(LiteracyTest).where(LiteracyTest.user_id == user_id).order_by(LiteracyTest.start_time.desc())
        tests = session.exec(stmt).all()
        
        return [
            {
                "test_id": test.id,
                "start_time": test.start_time,
                "end_time": test.end_time,
                "status": test.status,
                "total_characters": test.total_characters,
                "correct_characters": test.correct_characters,
                "accuracy_rate": test.accuracy_rate,
                "total_score": test.total_score,
                "evaluation_status": test.evaluation_status
            }
            for test in tests
        ]
    finally:
        try:
            next(session_gen)
        except StopIteration:
            pass