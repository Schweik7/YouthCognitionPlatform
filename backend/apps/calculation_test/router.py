from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List, Dict, Any

from database import get_session
from .models import (
    CalculationProblem,
    CalculationTestSession,
    ProblemData,
    BatchProblemData,
    TestSessionCreate,
    TestSessionUpdate,
    TestSessionResponse,
    ResultResponse,
)
from .service import (
    create_test_session,
    get_test_session,
    update_test_session,
    list_user_test_sessions,
    complete_test_session,
    save_problem,
    save_batch_problems,
    get_session_problems,
    get_test_session_results,
)

# 创建路由
router = APIRouter(tags=["计算流畅性测试"])


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


@router.post("/sessions/{test_session_id}/problems", status_code=status.HTTP_201_CREATED)
async def save_problem_route(
    test_session_id: int, problem_data: ProblemData, session: Session = Depends(get_session)
):
    """保存计算题目记录"""
    try:
        problem = save_problem(session, test_session_id, problem_data)
        return {"message": "数据保存成功", "id": problem.id}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"保存题目数据失败: {str(e)}"
        )


@router.get("/sessions/{test_session_id}/problems")
async def get_session_problems_route(test_session_id: int, session: Session = Depends(get_session)):
    """获取测试会话中的所有计算题目记录"""
    test_session = get_test_session(session, test_session_id)
    if not test_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试会话不存在")
    return get_session_problems(session, test_session_id)


@router.get("/sessions/{test_session_id}/results", response_model=Dict[str, Any])
async def get_session_results_route(test_session_id: int, session: Session = Depends(get_session)):
    """获取测试会话的结果"""
    results = get_test_session_results(session, test_session_id)
    if not results:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试会话不存在")
    return results


@router.post("/sessions/{test_session_id}/problems-batch", status_code=status.HTTP_201_CREATED)
async def save_batch_problems_route(
    test_session_id: int, batch_data: BatchProblemData, session: Session = Depends(get_session)
):
    """批量保存计算题目记录"""
    try:
        results = save_batch_problems(session, test_session_id, batch_data)
        return {"message": "批量数据保存成功", "saved_count": len(results)}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"保存批量题目数据失败: {str(e)}"
        )