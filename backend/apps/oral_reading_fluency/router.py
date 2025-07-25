import asyncio
from fastapi import APIRouter, Depends, HTTPException, status, Form, File, UploadFile
from fastapi.responses import JSONResponse
from sqlmodel import Session
from typing import List, Dict, Any, Optional
from datetime import datetime

from database import get_session
from .models import (
    OralReadingFluencyTest,
    OralReadingAudioRecord,
    OralReadingFluencyTestCreate,
    OralReadingFluencySubmission,
    OralReadingFluencyTestResponse,
    OralReadingAudioRecordResponse,
    TestResultSummary
)
from .service import (
    get_character_data,
    create_oral_reading_fluency_test,
    get_oral_reading_fluency_test,
    process_reading_submission,
    batch_evaluate_test_audio,
    get_test_results,
    list_user_oral_reading_tests
)
from .xfyun_sdk import XfyunSDKFactory

# 创建路由
router = APIRouter(tags=["朗读流畅性测试"])

# 初始化SDK（应该在应用启动时配置）
try:
    from config import settings
    XfyunSDKFactory.initialize(
        app_id=settings.XFYUN_APP_ID,
        api_key=settings.XFYUN_API_KEY,
        api_secret=settings.XFYUN_API_SECRET
    )
    print(f"✅ 讯飞SDK初始化成功，APP ID: {settings.XFYUN_APP_ID[:8]}...")
except Exception as e:
    print(f"⚠️  警告: 语音评测SDK初始化失败: {e}")
    print("💡 请在config.py中设置正确的科大讯飞API凭证")


@router.get("/characters")
async def get_characters():
    """获取朗读字符表数据"""
    try:
        return {
            "success": True,
            "data": get_character_data(),
            "total_rows": len(get_character_data()),
            "chars_per_row": 10
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取字符数据失败: {str(e)}"
        )


@router.post("/tests", status_code=status.HTTP_201_CREATED)
async def create_test(
    test_data: OralReadingFluencyTestCreate, 
    session: Session = Depends(get_session)
):
    """创建朗读流畅性测试"""
    try:
        test = create_oral_reading_fluency_test(session, test_data)
        return {
            "success": True,
            "message": "测试创建成功",
            "test_id": test.id,
            "test": {
                "id": test.id,
                "user_id": test.user_id,
                "start_time": test.start_time,
                "status": test.status
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建测试失败: {str(e)}"
        )


@router.get("/tests/{test_id}")
async def get_test(test_id: int, session: Session = Depends(get_session)):
    """获取朗读流畅性测试信息"""
    test = get_oral_reading_fluency_test(session, test_id)
    if not test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试不存在")
    
    return {
        "success": True,
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
            "is_completed": test.is_completed,
            "total_duration": test.total_duration,
            "total_character_count": test.total_character_count
        }
    }



@router.post("/tests/{test_id}/submit")
async def submit_test(
    test_id: int,
    testType: str = Form(...),
    results: str = Form(...),
    session: Session = Depends(get_session),
    files: List[UploadFile] = File(default=[])
):
    """提交朗读流畅性测试结果"""
    try:
        import json
        
        # 解析提交数据
        results_data = json.loads(results)
        submission_data = OralReadingFluencySubmission(
            testType=testType,
            results=results_data
        )
        
        # 音频文件已经通过单独接口上传，这里只处理测试结果
        audio_files = {}  # 空字典，因为音频已单独上传
        
        # 处理提交
        test = process_reading_submission(session, test_id, submission_data, audio_files)
        
        # 异步启动语音评测
        asyncio.create_task(batch_evaluate_test_audio(session, test_id))
        
        return {
            "success": True,
            "message": "测试提交成功，语音评测正在后台处理",
            "test_id": test.id,
            "audio_files_count": len(audio_files),
            "evaluation_status": "processing"
        }
        
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"JSON数据解析失败: {str(e)}"
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提交测试失败: {str(e)}"
        )


@router.post("/tests/{test_id}/upload-audio")
async def upload_single_audio(
    test_id: int,
    round_number: int = Form(...),
    row_index: int = Form(...),
    session: Session = Depends(get_session),
    audio_file: UploadFile = File(...)
):
    """上传单个音频文件并立即开始评测"""
    try:
        # 检查测试是否存在
        test = get_oral_reading_fluency_test(session, test_id)
        if not test:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试不存在")
        
        # 读取音频数据
        audio_data = await audio_file.read()
        
        # 固定使用mp3后缀，文件更小更适合传输
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_{test_id}_round{round_number}_row{row_index}_{timestamp}.mp3"
        
        # 保存文件
        from .service import save_audio_file
        file_path = save_audio_file(audio_data, filename)
        
        # 创建音频记录
        audio_record = OralReadingAudioRecord(
            test_id=test_id,
            round_number=round_number,
            row_index=row_index,
            audio_file_path=file_path,
            evaluation_status="pending"
        )
        
        session.add(audio_record)
        session.commit()
        session.refresh(audio_record)
        
        # 异步启动评测
        from .service import evaluate_audio_record
        asyncio.create_task(evaluate_audio_record(session, audio_record.id))
        
        return {
            "success": True,
            "message": "音频上传成功，评测已开始",
            "audio_record_id": audio_record.id,
            "round_number": round_number,
            "row_index": row_index
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"音频上传失败: {str(e)}"
        )


@router.post("/tests/{test_id}/evaluate")
async def evaluate_test_audio(test_id: int, session: Session = Depends(get_session)):
    """手动触发测试音频评测"""
    try:
        # 检查测试是否存在
        test = get_oral_reading_fluency_test(session, test_id)
        if not test:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试不存在")
        
        # 执行批量评测
        result = await batch_evaluate_test_audio(session, test_id)
        
        return {
            "success": result["success"],
            "message": "语音评测完成" if result["success"] else "语音评测失败",
            "evaluation_result": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"语音评测失败: {str(e)}"
        )


@router.get("/tests/{test_id}/results")
async def get_test_results_route(test_id: int, session: Session = Depends(get_session)):
    """获取测试结果"""
    try:
        results = get_test_results(session, test_id)
        if not results:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试不存在")
        
        return {
            "success": True,
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取测试结果失败: {str(e)}"
        )


@router.get("/users/{user_id}/tests")
async def list_user_tests(user_id: int, session: Session = Depends(get_session)):
    """获取用户的所有朗读流畅性测试"""
    try:
        tests = list_user_oral_reading_tests(session, user_id)
        
        test_list = []
        for test in tests:
            test_list.append({
                "id": test.id,
                "start_time": test.start_time,
                "end_time": test.end_time,
                "status": test.status,
                "round1_completed": test.round1_completed,
                "round2_completed": test.round2_completed,
                "average_score": test.average_score,
                "evaluation_status": test.evaluation_status,
                "is_completed": test.is_completed
            })
        
        return {
            "success": True,
            "tests": test_list,
            "total_count": len(test_list)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户测试列表失败: {str(e)}"
        )


@router.get("/tests/{test_id}/status")
async def get_test_status(test_id: int, session: Session = Depends(get_session)):
    """获取测试状态（用于轮询评测进度）"""
    try:
        test = get_oral_reading_fluency_test(session, test_id)
        if not test:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试不存在")
        
        return {
            "success": True,
            "test_id": test.id,
            "status": test.status,
            "evaluation_status": test.evaluation_status,
            "evaluation_completed_at": test.evaluation_completed_at,
            "is_completed": test.is_completed,
            "round1_completed": test.round1_completed,
            "round2_completed": test.round2_completed,
            "average_score": test.average_score
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取测试状态失败: {str(e)}"
        )
