from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List, Dict, Any, Optional

from logger_config import logger
from database import get_session
from ..users.models import User
from .models import (
    AttentionTestSession,
    AttentionRecord,
    AttentionSessionCreate,
    AttentionSessionUpdate,
    AttentionSessionResponse,
    AttentionResultResponse,
    AttentionRecordCreate,
    AttentionClickedRecordsCreate,
    SymbolRowResponse,
)
from .service import (
    generate_practice_sequence,
    generate_test_sequence,
    create_test_session,
    get_test_session,
    update_test_session,
    list_user_test_sessions,
    complete_test_session,
    save_attention_record,
    save_clicked_records,
    get_test_session_records,
    get_test_session_results,
    select_random_target_symbol,
)

# 创建路由
router = APIRouter(tags=["注意力筛查测试"])


@router.get("/practice-sequence", response_model=List[Dict[str, Any]])
async def get_practice_sequence(target_symbol: Optional[str] = None):
    """获取练习阶段序列，如果未指定目标符号则随机选择一个"""
    try:
        # 如果未指定目标符号，随机选择一个
        if not target_symbol:
            target_symbol = select_random_target_symbol()

        return generate_practice_sequence(target_symbol)
    except Exception as e:
        logger.error(f"获取练习序列失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取练习序列失败: {str(e)}"
        )


@router.get("/test-sequence", response_model=List[Dict[str, Any]])
async def get_test_sequence(target_symbol: Optional[str] = None):
    """获取测试阶段序列，如果未指定目标符号则随机选择一个"""
    try:
        # 如果未指定目标符号，随机选择一个
        if not target_symbol:
            target_symbol = select_random_target_symbol()

        return generate_test_sequence(target_symbol)
    except Exception as e:
        logger.error(f"获取测试序列失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取测试序列失败: {str(e)}"
        )


@router.post(
    "/sessions", response_model=AttentionSessionResponse, status_code=status.HTTP_201_CREATED
)
async def create_session_route(
    test_session_data: AttentionSessionCreate, session: Session = Depends(get_session)
):
    """创建新的测试会话"""
    try:
        test_session = create_test_session(session, test_session_data)
        return test_session
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"创建测试会话失败: {str(e)}"
        )


@router.get("/sessions/{test_session_id}", response_model=AttentionSessionResponse)
async def get_session_route(test_session_id: int, session: Session = Depends(get_session)):
    """获取测试会话信息"""
    test_session = get_test_session(session, test_session_id)
    if not test_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试会话不存在")
    return test_session


@router.put("/sessions/{test_session_id}", response_model=AttentionSessionResponse)
async def update_session_route(
    test_session_id: int,
    update_data: AttentionSessionUpdate,
    session: Session = Depends(get_session),
):
    """更新测试会话信息"""
    test_session = update_test_session(session, test_session_id, update_data)
    if not test_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试会话不存在")
    return test_session


@router.get("/users/{user_id}/sessions", response_model=List[AttentionSessionResponse])
async def list_user_sessions_route(user_id: int, session: Session = Depends(get_session)):
    """获取用户的所有测试会话"""
    return list_user_test_sessions(session, user_id)


@router.post("/sessions/{test_session_id}/complete", response_model=AttentionSessionResponse)
async def complete_session_route(test_session_id: int, session: Session = Depends(get_session)):
    """完成测试会话"""
    test_session = complete_test_session(session, test_session_id)
    if not test_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试会话不存在")
    return test_session


@router.post("/records", status_code=status.HTTP_201_CREATED)
async def create_record_route(
    record_data: AttentionRecordCreate, session: Session = Depends(get_session)
):
    """保存单个注意力测试记录"""
    try:
        record = save_attention_record(session, record_data)
        return {"message": "数据保存成功", "id": record.id}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"保存记录失败: {str(e)}"
        )


@router.post("/sessions/{test_session_id}/clicked-records", status_code=status.HTTP_201_CREATED)
async def save_clicked_records_route(
    test_session_id: int, 
    data: AttentionClickedRecordsCreate,
    session: Session = Depends(get_session)
):
    """保存用户点击的位置记录"""
    try:
        # 检查会话是否存在
        test_session = session.get(AttentionTestSession, test_session_id)
        if not test_session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试会话不存在")
        
        # 检查用户是否存在
        user = session.get(User, data.user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
        
        # 确保test_session_id与请求路径中的一致
        if test_session_id != data.test_session_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="会话ID不匹配")
        
        # 保存点击记录
        records_count = save_clicked_records(session, data)
        
        return {"message": "数据保存成功", "count": records_count}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"保存点击记录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"保存数据失败: {str(e)}"
        )


@router.get("/sessions/{test_session_id}/records")
async def get_session_records_route(test_session_id: int, session: Session = Depends(get_session)):
    """获取测试会话中的所有记录"""
    test_session = get_test_session(session, test_session_id)
    if not test_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试会话不存在")
    return get_test_session_records(session, test_session_id)


@router.get("/sessions/{test_session_id}/results", response_model=Dict[str, Any])
async def get_session_results_route(test_session_id: int, session: Session = Depends(get_session)):
    """获取测试会话的结果"""
    results = get_test_session_results(session, test_session_id)
    if not results:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试会话不存在")
    return results