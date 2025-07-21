from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List, Dict, Any
from fastapi import Query

from database import get_session
from .models import (
    Trial,
    TestSession,
    TrialData,
    UserTrialData,
    ResultResponse,
    TestSessionCreate,
    TestSessionUpdate,
    TestSessionResponse,
)
from .service import (
    get_trials,
    save_trial,
    save_trial_direct,
    save_trial_with_session,
    get_user_results,
    create_test_session,
    get_test_session,
    update_test_session,
    list_user_test_sessions,
    complete_test_session,
    get_session_trials,
    get_test_session_results,
)

# 创建路由
router = APIRouter(tags=["阅读流畅性测试"])


@router.get("/trials")
async def get_trials_route(
    level: str = Query(None, description="测试级别: elementary 或 junior_high"), 
    grade: int = Query(None, description="用户年级，用于自动确定测试级别")
):
    """获取试题数据 - 支持按级别或年级获取"""
    try:
        return get_trials(level=level, grade=grade)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取试题数据失败: {str(e)}"
        )


@router.post("/save-trial", status_code=status.HTTP_201_CREATED)
async def save_trial_route(trial_data: UserTrialData, session: Session = Depends(get_session)):
    """保存试验数据（向后兼容，包含用户信息）"""
    try:
        trial = save_trial(session, trial_data)
        return {"message": "数据保存成功", "id": trial.id}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"保存试验数据失败: {str(e)}"
        )


@router.post("/trials", status_code=status.HTTP_201_CREATED)
async def create_trial_route(trial_data: TrialData, session: Session = Depends(get_session)):
    """直接保存试验数据（新API）"""
    try:
        trial = save_trial_direct(session, trial_data)
        return {"message": "数据保存成功", "id": trial.id}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"保存试验数据失败: {str(e)}"
        )


@router.get("/results/{user_id}", response_model=ResultResponse)
async def get_results_route(user_id: int, session: Session = Depends(get_session)):
    """获取指定用户的实验结果"""
    try:
        results = get_user_results(session, user_id)
        if not results:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
        return results
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取结果失败: {str(e)}"
        )


# 测试会话相关路由
@router.post("/sessions", response_model=TestSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session_route(
    test_session_data: TestSessionCreate, session: Session = Depends(get_session)
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


@router.get("/sessions/{test_session_id}", response_model=TestSessionResponse)
async def get_session_route(test_session_id: int, session: Session = Depends(get_session)):
    """获取测试会话信息"""
    test_session = get_test_session(session, test_session_id)
    if not test_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试会话不存在")
    return test_session


@router.put("/sessions/{test_session_id}", response_model=TestSessionResponse)
async def update_session_route(
    test_session_id: int, update_data: TestSessionUpdate, session: Session = Depends(get_session)
):
    """更新测试会话信息"""
    test_session = update_test_session(session, test_session_id, update_data)
    if not test_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试会话不存在")
    return test_session


@router.get("/users/{user_id}/sessions", response_model=List[TestSessionResponse])
async def list_user_sessions_route(user_id: int, session: Session = Depends(get_session)):
    """获取用户的所有测试会话"""
    return list_user_test_sessions(session, user_id)


@router.post("/sessions/{test_session_id}/complete", response_model=TestSessionResponse)
async def complete_session_route(test_session_id: int, session: Session = Depends(get_session)):
    """完成测试会话"""
    test_session = complete_test_session(session, test_session_id)
    if not test_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试会话不存在")
    return test_session


@router.post("/sessions/{test_session_id}/trials", status_code=status.HTTP_201_CREATED)
async def create_session_trial_route(
    test_session_id: int, trial_data: TrialData, session: Session = Depends(get_session)
):
    """在指定测试会话中保存试验记录"""
    try:
        trial = save_trial_with_session(session, test_session_id, trial_data)
        return {"message": "数据保存成功", "id": trial.id}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        # raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"保存试验数据失败: {str(e)}"
        )


@router.get("/sessions/{test_session_id}/trials")
async def get_session_trials_route(test_session_id: int, session: Session = Depends(get_session)):
    """获取测试会话中的所有试验记录"""
    test_session = get_test_session(session, test_session_id)
    if not test_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试会话不存在")
    return get_session_trials(session, test_session_id)


@router.get("/sessions/{test_session_id}/results")
async def get_session_results_route(test_session_id: int, session: Session = Depends(get_session)):
    """获取测试会话的结果"""
    results = get_test_session_results(session, test_session_id)
    if not results:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试会话不存在")
    return results
