import os
import asyncio
from datetime import datetime
from typing import Dict, Any, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from pathlib import Path
from config import UPLOAD_DIR
from .service import (
    get_character_groups,
    create_literacy_test,
    get_literacy_test,
    save_audio_record,
    evaluate_literacy_audio,
    get_test_results,
    get_user_tests
)

router = APIRouter(tags=["识字量测验"])

# 确保上传目录存在
LITERACY_UPLOAD_DIR = UPLOAD_DIR / "literacy_test"
LITERACY_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/character-groups")
async def get_literacy_character_groups() -> Dict[str, Any]:
    """获取识字量测验字符组"""
    try:
        groups = get_character_groups()
        return {
            "success": True,
            "data": groups
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取字符组失败: {str(e)}")


@router.post("/start-test")
async def start_literacy_test(user_id: int = Form(...)) -> Dict[str, Any]:
    """开始识字量测验"""
    try:
        test = create_literacy_test(user_id)
        return {
            "success": True,
            "data": {
                "test_id": test.id,
                "start_time": test.start_time,
                "status": test.status
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建测验失败: {str(e)}")


@router.post("/upload-audio")
async def upload_literacy_audio(
    background_tasks: BackgroundTasks,
    test_id: int = Form(...),
    character: str = Form(...),
    group_id: int = Form(...),
    coefficient: float = Form(...),
    audio_file: UploadFile = File(...)
) -> Dict[str, Any]:
    """上传识字量测验音频"""
    try:
        # 验证测验存在
        test = get_literacy_test(test_id)
        if not test:
            raise HTTPException(status_code=404, detail="测验不存在")
        
        # 验证文件类型
        if not audio_file.content_type or not audio_file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="请上传音频文件")
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = os.path.splitext(audio_file.filename or "audio.mp3")[1] or ".mp3"
        filename = f"literacy_{test_id}_{character}_{group_id}_{timestamp}{file_extension}"
        file_path = LITERACY_UPLOAD_DIR / filename
        
        # 保存文件
        content = await audio_file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # 获取文件信息
        file_size = len(content)
        
        # 保存音频记录到数据库
        relative_path = str(file_path.relative_to(UPLOAD_DIR))
        audio_record = save_audio_record(
            test_id=test_id,
            character=character,
            group_id=group_id,
            coefficient=coefficient,
            audio_file_path=relative_path,
            audio_duration=0.0,  # 暂时设为0，后续可通过音频分析获取
            file_size=file_size
        )
        
        # 异步启动评测
        background_tasks.add_task(evaluate_literacy_audio, audio_record.id)
        
        return {
            "success": True,
            "data": {
                "audio_record_id": audio_record.id,
                "message": "音频上传成功，开始评测"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.get("/test/{test_id}")
async def get_literacy_test_info(test_id: int) -> Dict[str, Any]:
    """获取识字量测验信息"""
    try:
        test = get_literacy_test(test_id)
        if not test:
            raise HTTPException(status_code=404, detail="测验不存在")
        
        return {
            "success": True,
            "data": {
                "test_id": test.id,
                "user_id": test.user_id,
                "start_time": test.start_time,
                "end_time": test.end_time,
                "status": test.status,
                "evaluation_status": test.evaluation_status
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取测验信息失败: {str(e)}")


@router.get("/test/{test_id}/results")
async def get_literacy_test_results(test_id: int) -> Dict[str, Any]:
    """获取识字量测验结果"""
    try:
        results = get_test_results(test_id)
        if not results:
            raise HTTPException(status_code=404, detail="测验结果不存在")
        
        return {
            "success": True,
            "data": results
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取测验结果失败: {str(e)}")


@router.get("/user/{user_id}/tests")
async def get_user_literacy_tests(user_id: int) -> Dict[str, Any]:
    """获取用户的所有识字量测验"""
    try:
        tests = get_user_tests(user_id)
        return {
            "success": True,
            "data": tests
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户测验列表失败: {str(e)}")