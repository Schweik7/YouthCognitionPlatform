from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List, Dict, Any

from database import get_session
from .models import TrialData, UserTrialData, ResultResponse
from .service import get_trials, save_trial, save_trial_direct, get_user_results

# 创建路由
router = APIRouter(tags=["阅读流畅性测试"])


@router.get("/trials", response_model=Dict[str, List[str]])
async def get_trials_route():
    """获取试题数据"""
    try:
        return get_trials()
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
