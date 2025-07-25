import os
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlmodel import Session, select
from config import settings
from logger_config import logger
from apps.users.models import User
from .models import (
    OralReadingFluencyTest,
    OralReadingAudioRecord,
    TestStatus,
    OralReadingFluencyTestCreate,
    OralReadingFluencySubmission,
    OralReadingFluencyTestResponse,
    OralReadingAudioRecordResponse,
    TestResultSummary
)
from .xfyun_sdk import (
    XfyunSpeechEvaluationSDK,
    XfyunSDKFactory,
    EvaluationRequest,
    EvaluationResponse
)
from .analysis import (
    analyze_reading_evaluation,
    estimate_correct_character_count
)


# 字符数据
CHARACTER_ROWS = [
    "的 一 了 我 是 不 在 上 来 有",
    "着 他 地 子 人 们 到 个 小 这",
    "里 大 天 就 说 那 去 看 下 得", 
    "时 么 你 也 过 出 起 好 要 把",
    "它 儿 头 只 多 可 中 和 家 会",
    "还 又 没 花 水 长 道 面 样 见",
    "很 走 老 开 树 生 边 想 为 能",
    "声 后 然 从 自 妈 山 回 什 用",
    "成 发 叫 前 以 手 对 点 身 候",
    "飞 白 两 方 心 动 太 听 风 三",
    "十 吃 眼 几 亲 色 雨 光 学 月",
    "高 些 进 孩 住 气 给 她 知 向",
    "船 如 种 国 呢 事 红 快 外 无",
    "再 明 西 同 日 海 真 于 己 门",
    "亮 怎 草 跑 行 最 阳 问 正 啊",
    "常 马 牛 当 笑 打 放 别 经 河",
    "做 鸟 星 东 石 物 空 才 之 吧",
    "火 许 每 间 力 已 二 四 美 次"
]

# 上传文件存储路径
UPLOAD_DIR = Path("uploads") / "oral_reading_fluency"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def get_character_data() -> List[str]:
    """获取字符表数据"""
    return CHARACTER_ROWS


def create_oral_reading_fluency_test(session: Session, test_data: OralReadingFluencyTestCreate) -> OralReadingFluencyTest:
    """创建朗读流畅性测试"""
    # 检查用户是否存在
    user = session.get(User, test_data.user_id)
    if not user:
        raise ValueError(f"用户不存在: ID={test_data.user_id}")
    
    # 创建测试
    test = OralReadingFluencyTest(
        user_id=test_data.user_id,
        status=TestStatus.PENDING,
        start_time=datetime.now()
    )
    
    session.add(test)
    session.commit()
    session.refresh(test)
    
    logger.info(f"为用户 {user.name} 创建朗读流畅性测试，ID: {test.id}")
    return test


def get_oral_reading_fluency_test(session: Session, test_id: int) -> Optional[OralReadingFluencyTest]:
    """获取朗读流畅性测试"""
    return session.get(OralReadingFluencyTest, test_id)


def save_audio_file(audio_data: bytes, filename: str) -> str:
    """保存音频文件并返回路径"""
    file_path = UPLOAD_DIR / filename
    
    # 确保目录存在
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 保存文件
    with open(file_path, 'wb') as f:
        f.write(audio_data)
    
    return str(file_path)


def process_reading_submission(
    session: Session, 
    test_id: int, 
    submission_data: OralReadingFluencySubmission,
    audio_files: Dict[str, bytes]
) -> OralReadingFluencyTest:
    """处理朗读流畅性测试提交"""
    # 获取测试
    test = session.get(OralReadingFluencyTest, test_id)
    if not test:
        raise ValueError(f"测试不存在: ID={test_id}")
    
    # 解析提交结果
    results = submission_data.results
    round1_data = results.get("round1", {})
    round2_data = results.get("round2", {})
    
    # 更新测试基本信息
    test.status = TestStatus.COMPLETED
    test.end_time = datetime.now()
    test.round1_duration = round1_data.get("duration", 0)
    test.round1_character_count = round1_data.get("characterCount", 0)
    test.round1_completed = True
    
    test.round2_duration = round2_data.get("duration", 0)
    test.round2_character_count = round2_data.get("characterCount", 0)
    test.round2_completed = True
    
    # 计算平均成绩
    if test.round1_character_count and test.round2_character_count:
        test.average_score = (test.round1_character_count + test.round2_character_count) / 2
    
    # 统计已上传的音频文件数量（音频文件已通过单独接口上传）
    from sqlmodel import select
    audio_query = select(OralReadingAudioRecord).where(OralReadingAudioRecord.test_id == test_id)
    existing_audio_records = session.exec(audio_query).all()
    total_audio_files = len(existing_audio_records)
    
    test.total_audio_files = total_audio_files
    test.evaluation_status = "pending"
    
    session.add(test)
    session.commit()
    session.refresh(test)
    
    logger.info(f"朗读流畅性测试提交完成: {test.id}, 音频文件数: {total_audio_files}")
    return test


async def evaluate_audio_record(session: Session, audio_record_id: int) -> bool:
    """评测单个音频记录"""
    try:
        # 获取音频记录
        audio_record = session.get(OralReadingAudioRecord, audio_record_id)
        if not audio_record:
            logger.error(f"音频记录不存在: {audio_record_id}")
            return False
        
        # 获取对应行的文本
        if 0 <= audio_record.row_index < len(CHARACTER_ROWS):
            text_to_evaluate = CHARACTER_ROWS[audio_record.row_index]
        else:
            logger.error(f"行索引超出范围: {audio_record.row_index}")
            return False
        
        # 更新状态为处理中
        audio_record.evaluation_status = "processing"
        session.add(audio_record)
        session.commit()
        
        # 创建评测请求
        evaluation_request = XfyunSDKFactory.create_syllable_request(text_to_evaluate)
        
        # 获取SDK并进行评测
        sdk = XfyunSDKFactory.get_sdk()
        audio_path = Path(audio_record.audio_file_path)
        
        if not audio_path.exists():
            logger.error(f"音频文件不存在: {audio_path}")
            audio_record.evaluation_status = "failed"
            session.add(audio_record)
            session.commit()
            return False
        
        # 执行评测
        result = await sdk.evaluate_audio_file(
            audio_path, 
            evaluation_request,
            progress_callback=lambda msg: logger.info(f"评测进度 [{audio_record_id}]: {msg}")
        )
        
        # 保存评测结果
        if result.success:
            audio_record.evaluation_status = "completed"
            audio_record.total_score = result.total_score
            audio_record.phone_score = result.phone_score
            audio_record.tone_score = result.tone_score
            audio_record.fluency_score = result.fluency_score
            audio_record.integrity_score = result.integrity_score
            
            # 使用详细分析估算正确字数
            max_chars_in_row = 10  # 每行10个字
            audio_record.correct_character_count = estimate_correct_character_count(
                result.xml_result, max_chars_in_row
            )
            
            # 保存详细结果（包含解析后的分析）
            detailed_analysis = analyze_reading_evaluation(result.xml_result)
            evaluation_result_data = {
                "xml_result": result.xml_result,
                "analysis_time": result.analysis_time.isoformat(),
                "message": result.message,
                "detailed_analysis": detailed_analysis
            }
            audio_record.evaluation_result = json.dumps(evaluation_result_data, ensure_ascii=False)
            
            logger.info(f"音频评测成功: {audio_record_id}, 总分: {result.total_score}")
        else:
            audio_record.evaluation_status = "failed"
            audio_record.evaluation_result = json.dumps({
                "error": result.message,
                "analysis_time": result.analysis_time.isoformat()
            }, ensure_ascii=False)
            logger.error(f"音频评测失败: {audio_record_id}, 错误: {result.message}")
        
        session.add(audio_record)
        session.commit()
        
        return result.success
        
    except Exception as e:
        logger.error(f"评测音频记录时发生异常: {audio_record_id}, 错误: {str(e)}")
        
        # 更新状态为失败
        try:
            audio_record = session.get(OralReadingAudioRecord, audio_record_id)
            if audio_record:
                audio_record.evaluation_status = "failed"
                audio_record.evaluation_result = json.dumps({"error": str(e)}, ensure_ascii=False)
                session.add(audio_record)
                session.commit()
        except Exception as db_error:
            logger.error(f"更新音频记录状态失败: {db_error}")
        
        return False


async def batch_evaluate_test_audio(session: Session, test_id: int) -> Dict[str, Any]:
    """批量评测测试的所有音频"""
    try:
        # 获取测试
        test = session.get(OralReadingFluencyTest, test_id)
        if not test:
            raise ValueError(f"测试不存在: ID={test_id}")
        
        # 获取所有待评测的音频记录
        query = select(OralReadingAudioRecord).where(
            OralReadingAudioRecord.test_id == test_id,  
            OralReadingAudioRecord.evaluation_status == "pending"
        )
        audio_records = session.exec(query).all()
        
        if not audio_records:
            logger.info(f"测试 {test_id} 没有待评测的音频")
            return {"success": True, "message": "没有待评测的音频", "evaluated_count": 0}
        
        # 更新测试状态
        test.evaluation_status = "processing"
        session.add(test)
        session.commit()
        
        logger.info(f"开始批量评测测试 {test_id} 的 {len(audio_records)} 个音频文件")
        
        # 并发评测音频（控制并发数以避免过载）
        semaphore = asyncio.Semaphore(3)  # 最多同时评测3个音频
        
        async def evaluate_with_semaphore(audio_record_id):
            async with semaphore:
                return await evaluate_audio_record(session, audio_record_id)
        
        # 执行批量评测
        tasks = [evaluate_with_semaphore(record.id) for record in audio_records]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 统计结果
        success_count = sum(1 for result in results if result is True)
        failed_count = len(results) - success_count
        
        # 更新测试的评测完成状态
        if failed_count == 0:
            test.evaluation_status = "completed"
        else:
            test.evaluation_status = "partial_completed"
        
        test.evaluation_completed_at = datetime.now()
        
        # 重新计算基于评测结果的字符数
        completed_records_query = select(OralReadingAudioRecord).where(
            OralReadingAudioRecord.test_id == test_id,
            OralReadingAudioRecord.evaluation_status == "completed"
        )
        completed_records = session.exec(completed_records_query).all()
        
        # 按轮次统计正确字符数
        round1_correct = sum(
            record.correct_character_count or 0 
            for record in completed_records 
            if record.round_number == 1
        )
        round2_correct = sum(
            record.correct_character_count or 0 
            for record in completed_records 
            if record.round_number == 2
        )
        
        # 更新测试结果（使用评测得出的准确字数）
        test.round1_character_count = round1_correct
        test.round2_character_count = round2_correct
        
        if round1_correct > 0 or round2_correct > 0:
            test.average_score = (round1_correct + round2_correct) / 2
        
        session.add(test)
        session.commit()
        
        result_info = {
            "success": True,
            "test_id": test_id,
            "total_audio_files": len(audio_records),
            "evaluated_successfully": success_count,
            "evaluation_failures": failed_count,
            "round1_correct_chars": round1_correct,
            "round2_correct_chars": round2_correct,
            "average_score": test.average_score,
            "evaluation_status": test.evaluation_status
        }
        
        logger.info(f"批量评测完成: {result_info}")
        return result_info
        
    except Exception as e:
        logger.error(f"批量评测测试音频时发生异常: {test_id}, 错误: {str(e)}")
        
        # 更新测试状态为失败
        try:
            test = session.get(OralReadingFluencyTest, test_id)
            if test:
                test.evaluation_status = "failed"
                session.add(test)
                session.commit()
        except Exception as db_error:
            logger.error(f"更新测试状态失败: {db_error}")
        
        return {
            "success": False,
            "test_id": test_id,
            "error": str(e)
        }


def get_test_results(session: Session, test_id: int) -> Optional[Dict[str, Any]]:
    """获取测试结果"""
    # 获取测试
    test = session.get(OralReadingFluencyTest, test_id)
    if not test:
        return None
    
    # 获取用户信息
    user = session.get(User, test.user_id) if test.user_id else None
    
    # 获取所有音频记录
    query = select(OralReadingAudioRecord).where(OralReadingAudioRecord.test_id == test_id)
    audio_records = session.exec(query).all()
    
    # 统计评测完成情况
    total_audio_files = len(audio_records)
    completed_evaluations = len([r for r in audio_records if r.evaluation_status == "completed"])
    evaluation_completion_rate = (completed_evaluations / total_audio_files * 100) if total_audio_files > 0 else 0
    
    # 按轮次分组音频记录
    round1_records = [r for r in audio_records if r.round_number == 1]
    round2_records = [r for r in audio_records if r.round_number == 2]
    
    result = {
        "test": {
            "id": test.id,
            "user_id": test.user_id,
            "start_time": test.start_time,
            "end_time": test.end_time,
            "status": test.status,
            "round1_duration": test.round1_duration,
            "round1_character_count": test.round1_character_count,
            "round1_completed": test.round1_completed,
            "round2_duration": test.round2_duration,
            "round2_character_count": test.round2_character_count,
            "round2_completed": test.round2_completed,
            "average_score": test.average_score,
            "total_audio_files": test.total_audio_files,
            "evaluation_status": test.evaluation_status,
            "evaluation_completed_at": test.evaluation_completed_at,
            "is_completed": test.is_completed,
            "total_duration": test.total_duration,
            "total_character_count": test.total_character_count
        },
        "user": {
            "id": user.id if user else None,
            "name": user.name if user else None,
            "school": user.school if user else None,
            "grade": user.grade if user else None,
            "class_number": user.class_number if user else None
        } if user else None,
        "statistics": {
            "total_audio_files": total_audio_files,
            "completed_evaluations": completed_evaluations,
            "evaluation_completion_rate": evaluation_completion_rate,
            "round1_audio_count": len(round1_records),
            "round2_audio_count": len(round2_records),
            "average_total_score": sum(r.total_score or 0 for r in audio_records if r.total_score) / completed_evaluations if completed_evaluations > 0 else 0,
            "average_phone_score": sum(r.phone_score or 0 for r in audio_records if r.phone_score) / completed_evaluations if completed_evaluations > 0 else 0,
            "average_tone_score": sum(r.tone_score or 0 for r in audio_records if r.tone_score) / completed_evaluations if completed_evaluations > 0 else 0
        },
        "audio_records": [
            {
                "id": record.id,
                "round_number": record.round_number,
                "row_index": record.row_index,
                "evaluation_status": record.evaluation_status,
                "total_score": record.total_score,
                "phone_score": record.phone_score,
                "tone_score": record.tone_score,
                "fluency_score": record.fluency_score,
                "integrity_score": record.integrity_score,
                "correct_character_count": record.correct_character_count,
                "upload_time": record.upload_time,
                "evaluation_result": json.loads(record.evaluation_result) if record.evaluation_result else None
            } for record in audio_records
        ]
    }
    
    return result


def list_user_oral_reading_tests(session: Session, user_id: int) -> List[OralReadingFluencyTest]:
    """获取用户的所有朗读流畅性测试"""
    query = select(OralReadingFluencyTest).where(OralReadingFluencyTest.user_id == user_id)
    return list(session.exec(query).all())
