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
from apps.oral_reading_fluency.xfyun_sdk import XfyunSpeechEvaluationSDK, XfyunSDKFactory
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
    characters: str,  # 多个字符组成的字符串
    group_id: int,
    coefficient: float,
    audio_file_path: str,
    audio_duration: float,
    file_size: int
) -> List[LiteracyAudioRecord]:
    """保存音频记录，为每个字符创建独立记录"""
    session_gen = get_session()
    session = next(session_gen)
    try:
        records = []
        for char in characters:
            record = LiteracyAudioRecord(
                test_id=test_id,
                character=char,  # 单个字符
                group_id=group_id,
                coefficient=coefficient,
                audio_file_path=audio_file_path,
                audio_duration=audio_duration,
                file_size=file_size
            )
            session.add(record)
            records.append(record)
        
        session.commit()
        for record in records:
            session.refresh(record)
        return records
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


async def evaluate_literacy_audio(audio_record_ids: List[int]):
    """异步评测识字量音频"""
    session_gen = get_session()
    session = next(session_gen)
    try:
        # 获取第一个音频记录来获取基本信息（所有记录应该有相同的音频文件）
        first_record = session.get(LiteracyAudioRecord, audio_record_ids[0])
        if not first_record:
            return
        
        # 获取所有相关记录
        records = [session.get(LiteracyAudioRecord, record_id) for record_id in audio_record_ids]
        records = [r for r in records if r]  # 过滤None值
        
        if not records:
            return
        
        # 更新所有记录的评测状态
        for record in records:
            record.evaluation_status = "processing"
            record.evaluation_started_at = datetime.now()
        session.commit()
        
        try:
            # 构建音频文件完整路径
            audio_path = UPLOAD_DIR / first_record.audio_file_path
            
            # 获取所有需要评测的字符
            all_characters = ''.join([record.character for record in records])
            
            # 获取SDK和创建评测请求
            sdk = XfyunSDKFactory.get_sdk()
            evaluation_request = XfyunSDKFactory.create_syllable_request(all_characters)
            
            # 调用语音评测API
            result = await sdk.evaluate_audio_file(
                audio_path,
                evaluation_request
            )
            
            if result.success:
                # 为每个字符单独判断是否正确
                for record in records:
                    char = record.character
                    is_correct = char in result.correct_characters
                    confidence_score = 1.0 if is_correct else 0.0
                    
                    # 更新单个记录
                    record.is_correct = is_correct
                    record.confidence_score = confidence_score
                    record.evaluation_status = "completed"
                    record.evaluation_completed_at = datetime.now()
                
                # 保存详细结果到文件（只保存一份，代表整个组）
                detailed_analysis = {
                    "correct_characters": result.correct_characters,
                    "total_characters": result.total_characters,
                    "total_score": result.total_score,
                    "target_characters": [r.character for r in records],
                    "individual_results": [
                        {
                            "character": record.character,
                            "is_correct": record.is_correct,
                            "confidence_score": record.confidence_score
                        }
                        for record in records
                    ],
                    "xml_result": result.xml_result
                }
                result_file_path = save_evaluation_result_file(
                    result.xml_result, detailed_analysis, first_record.id
                )
                
                # 设置所有记录的结果文件路径
                for record in records:
                    record.evaluation_result_path = result_file_path
                
            else:
                # 评测失败，更新所有记录
                error_msg = result.message or "评测服务异常"
                
                for record in records:
                    record.is_correct = False
                    record.confidence_score = 0.0
                    record.evaluation_status = "failed"
                    record.evaluation_completed_at = datetime.now()
                    record.error_message = error_msg
                
                # 保存错误信息到文件
                error_data = {
                    "audio_record_ids": audio_record_ids,
                    "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                    "error_message": error_msg,
                    "evaluation_type": "literacy_test"
                }
                
                results_dir = UPLOAD_DIR / "evaluation_results"
                results_dir.mkdir(parents=True, exist_ok=True)
                filename = f"literacy_error_{first_record.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                error_file_path = results_dir / filename
                
                with open(error_file_path, 'w', encoding='utf-8') as f:
                    json.dump(error_data, f, ensure_ascii=False, indent=2)
                
                error_file_relative = str(error_file_path.relative_to(UPLOAD_DIR))
                for record in records:
                    record.evaluation_result_path = error_file_relative
            
            session.commit()
            
            # 检查是否所有音频都评测完成，如果是则更新测验状态
            await update_test_completion_status(first_record.test_id)
            
        except Exception as e:
            # 处理异常，更新所有记录
            for record in records:
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
        
        # 按组聚合音频记录
        groups_data = {}
        for record in audio_records:
            group_id = record.group_id
            if group_id not in groups_data:
                groups_data[group_id] = {
                    "group_id": group_id,
                    "coefficient": record.coefficient,
                    "characters": [],
                    "correct_count": 0,
                    "total_count": 0,
                    "group_score": 0.0,
                    "evaluation_status": "pending",
                    "audio_file_path": record.audio_file_path
                }
            
            groups_data[group_id]["characters"].append({
                "character": record.character,
                "is_correct": record.is_correct,
                "confidence_score": record.confidence_score
            })
            groups_data[group_id]["total_count"] += 1
            
            if record.is_correct:
                groups_data[group_id]["correct_count"] += 1
                groups_data[group_id]["group_score"] += record.coefficient
            
            # 更新组的评测状态
            if record.evaluation_status in ["completed", "failed"]:
                if groups_data[group_id]["evaluation_status"] == "pending":
                    groups_data[group_id]["evaluation_status"] = record.evaluation_status
        
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
            "groups": list(groups_data.values())  # 按组返回数据
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


def finish_test_manually(test_id: int, unknown_characters: List[str]) -> bool:
    """手动完成测验，将未录音的字符标记为不认识"""
    session_gen = get_session()
    session = next(session_gen)
    try:
        test = session.get(LiteracyTest, test_id)
        if not test:
            return False
        
        # 获取所有字符组数据
        character_groups_data = load_literacy_test_data()
        all_characters = []
        character_to_group = {}  # 字符到组的映射
        
        for group in character_groups_data["character_groups"]:
            if group["characters"]:  # 只处理有字符的组
                for char in group["characters"]:
                    all_characters.append(char)
                    character_to_group[char] = {
                        "group_id": group["group_id"],
                        "coefficient": group["coefficient"]
                    }
        
        # 获取已有的音频记录
        stmt = select(LiteracyAudioRecord).where(LiteracyAudioRecord.test_id == test_id)
        existing_records = session.exec(stmt).all()
        
        # 获取已录音的组ID（基于音频记录）
        recorded_groups = {record.group_id for record in existing_records}
        
        # 找出未录音的组，将整个组的所有字符标记为不认识
        for group in character_groups_data["character_groups"]:
            if group["characters"] and group["group_id"] not in recorded_groups:
                # 整个组未录音，将该组所有字符标记为不认识
                for char in group["characters"]:
                    dummy_record = LiteracyAudioRecord(
                        test_id=test_id,
                        character=char,
                        group_id=group["group_id"],
                        coefficient=group["coefficient"],
                        audio_file_path="",  # 空路径表示未录音
                        audio_duration=0.0,
                        file_size=0,
                        is_correct=False,  # 标记为不认识
                        confidence_score=0.0,
                        evaluation_status="not_recorded"  # 特殊状态表示未录音
                    )
                    session.add(dummy_record)
        
        # 对于手动标记的不认识字符，如果其组已录音但该字符没有录音记录，也要创建记录
        recorded_characters = {record.character for record in existing_records}
        for char in unknown_characters:
            if char not in recorded_characters and char in character_to_group:
                group_info = character_to_group[char]
                dummy_record = LiteracyAudioRecord(
                    test_id=test_id,
                    character=char,
                    group_id=group_info["group_id"],
                    coefficient=group_info["coefficient"],
                    audio_file_path="",  # 空路径表示未录音
                    audio_duration=0.0,
                    file_size=0,
                    is_correct=False,  # 标记为不认识
                    confidence_score=0.0,
                    evaluation_status="manually_marked_unknown"  # 特殊状态表示手动标记不认识
                )
                session.add(dummy_record)
        
        # 更新测验状态为完成
        test.status = TestStatus.COMPLETED
        test.end_time = datetime.now()
        
        session.commit()
        
        # 计算最终分数将在session commit后同步计算
        calculate_final_scores_sync(test_id)
        
        return True
        
    finally:
        try:
            next(session_gen)
        except StopIteration:
            pass


def calculate_final_scores_sync(test_id: int):
    """计算测验的最终分数"""
    session_gen = get_session()
    session = next(session_gen)
    try:
        test = session.get(LiteracyTest, test_id)
        if not test:
            return
        
        # 获取所有记录（包括真实录音和虚拟记录）
        stmt = select(LiteracyAudioRecord).where(LiteracyAudioRecord.test_id == test_id)
        all_records = session.exec(stmt).all()
        
        # 计算总分和统计
        correct_count = sum(1 for record in all_records if record.is_correct)
        total_count = len(all_records)
        
        # 按组统计得分
        group_scores = {}
        total_score = 0.0
        
        for record in all_records:
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
        test.evaluation_status = "completed"
        test.evaluation_completed_at = datetime.now()
        
        session.commit()
        
    finally:
        try:
            next(session_gen)
        except StopIteration:
            pass