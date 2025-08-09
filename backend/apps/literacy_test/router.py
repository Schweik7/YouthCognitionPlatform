import os
import asyncio
import base64
from datetime import datetime
from typing import Dict, Any, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from pydantic import BaseModel
from pathlib import Path
from config import UPLOAD_DIR
from .service import (
    get_character_groups,
    create_literacy_test,
    get_literacy_test,
    save_audio_record,
    evaluate_literacy_audio,
    get_test_results,
    get_user_tests,
    finish_test_manually
)
from .models import LiteracyAudioRecord
from database import get_session
from apps.oral_reading_fluency.xfyun_sdk import XfyunSDKFactory

router = APIRouter(tags=["识字量测验"])

# Pydantic 模型
class StartTestRequest(BaseModel):
    user_id: int

class UploadAudioRequest(BaseModel):
    test_id: int
    character: str
    group_id: int
    coefficient: float
    audio_data: str  # base64 encoded audio data
    audio_filename: str

class FinishTestRequest(BaseModel):
    unknown_characters: List[str]

class EmptyGroupRequest(BaseModel):
    test_id: int
    characters: str
    group_id: int
    coefficient: float
    is_empty: bool = True

# 初始化SDK（应该在应用启动时配置）
try:
    from config import settings
    XfyunSDKFactory.initialize(
        app_id=settings.XFYUN_APP_ID,
        api_key=settings.XFYUN_API_KEY,
        api_secret=settings.XFYUN_API_SECRET
    )
    print(f"✅ 识字量测试SDK初始化成功，APP ID: {settings.XFYUN_APP_ID[:8]}...")
except Exception as e:
    print(f"⚠️  警告: 识字量测试SDK初始化失败: {e}")
    print("💡 请在config.py中设置正确的科大讯飞API凭证")

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
async def start_literacy_test(request: StartTestRequest) -> Dict[str, Any]:
    """开始识字量测验"""
    try:
        test = create_literacy_test(request.user_id)
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
    request: UploadAudioRequest
) -> Dict[str, Any]:
    """上传识字量测验音频"""
    try:
        # 验证测验存在
        test = get_literacy_test(request.test_id)
        if not test:
            raise HTTPException(status_code=404, detail="测验不存在")
        
        # 解码base64音频数据
        try:
            audio_content = base64.b64decode(request.audio_data)
        except Exception:
            raise HTTPException(status_code=400, detail="无效的音频数据")
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = os.path.splitext(request.audio_filename)[1] or ".mp3"
        filename = f"literacy_{request.test_id}_{request.character}_{request.group_id}_{timestamp}{file_extension}"
        file_path = LITERACY_UPLOAD_DIR / filename
        
        # 保存文件
        with open(file_path, "wb") as f:
            f.write(audio_content)
        
        # 获取文件信息
        file_size = len(audio_content)
        
        # 保存音频记录到数据库（为每个字符创建独立记录）
        relative_path = str(file_path.relative_to(UPLOAD_DIR))
        audio_records = save_audio_record(
            test_id=request.test_id,
            characters=request.character,  # 多个字符的字符串
            group_id=request.group_id,
            coefficient=request.coefficient,
            audio_file_path=relative_path,
            audio_duration=0.0,  # 暂时设为0，后续可通过音频分析获取
            file_size=file_size
        )
        
        # 异步启动评测
        record_ids = [record.id for record in audio_records]
        background_tasks.add_task(evaluate_literacy_audio, record_ids)
        
        return {
            "success": True,
            "data": {
                "audio_record_ids": record_ids,
                "message": "音频上传成功，开始评测"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/upload-empty-group")
async def upload_empty_group(request: EmptyGroupRequest) -> Dict[str, Any]:
    """上传未录音组信息（标记为不认识）"""
    try:
        # 验证测验存在
        test = get_literacy_test(request.test_id)
        if not test:
            raise HTTPException(status_code=404, detail="测验不存在")
        
        # 为每个字符创建记录，标记为不认识
        session_gen = get_session()
        session = next(session_gen)
        try:
            record_ids = []
            for char in request.characters:
                record = LiteracyAudioRecord(
                    test_id=request.test_id,
                    character=char,
                    group_id=request.group_id,
                    coefficient=request.coefficient,
                    audio_file_path="",  # 空路径表示未录音
                    audio_duration=0.0,
                    file_size=0,
                    is_correct=False,  # 标记为不认识
                    confidence_score=0.0,
                    evaluation_status="not_recorded"  # 特殊状态表示未录音
                )
                session.add(record)
                record_ids.append(record.id)
            
            session.commit()
            
            return {
                "success": True,
                "data": {
                    "record_ids": record_ids,
                    "message": f"已标记组 {request.group_id} 的 {len(request.characters)} 个字符为不认识"
                }
            }
            
        finally:
            try:
                next(session_gen)
            except StopIteration:
                pass
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"标记失败: {str(e)}")


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


@router.post("/test/{test_id}/finish")
async def finish_literacy_test(
    test_id: int,
    request: FinishTestRequest
) -> Dict[str, Any]:
    """手动完成识字量测验"""
    try:
        result = finish_test_manually(test_id, request.unknown_characters)
        if result:
            return {
                "success": True,
                "message": "测验完成",
                "data": {
                    "test_id": test_id
                }
            }
        else:
            raise HTTPException(status_code=404, detail="测验不存在或无法完成")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"完成测验失败: {str(e)}")