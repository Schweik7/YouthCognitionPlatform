from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlmodel import Session
from typing import List, Dict, Any
from pathlib import Path

from logger_config import logger
from database import get_session
from config import settings
from .models import (
    RavenTestSession,
    RavenAnswer,
    RavenSessionCreate,
    RavenSessionUpdate,
    RavenSessionResponse,
    RavenAnswerCreate,
    RavenAnswerBatchCreate,
    QuestionInfo,
)
from .service import (
    create_test_session,
    get_test_session,
    update_test_session,
    save_answer,
    save_answers_batch,
    complete_test_session,
    get_session_answers,
    get_test_results,
    list_user_test_sessions,
    get_question_info,
    TOTAL_QUESTIONS,
)

# 创建路由
router = APIRouter(tags=["瑞文智力测验"])

# 图片目录路径
IMAGES_DIR = Path(settings.DATA_DIR) / "raven_test"


@router.post("/sessions", response_model=RavenSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session_route(
    session_data: RavenSessionCreate, session: Session = Depends(get_session)
):
    """创建新的测试会话"""
    try:
        test_session = create_test_session(session, session_data)
        return test_session
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"创建测试会话失败: {str(e)}"
        )


@router.get("/sessions/{test_session_id}", response_model=RavenSessionResponse)
async def get_session_route(test_session_id: int, session: Session = Depends(get_session)):
    """获取测试会话信息"""
    test_session = get_test_session(session, test_session_id)
    if not test_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试会话不存在")
    return test_session


@router.put("/sessions/{test_session_id}", response_model=RavenSessionResponse)
async def update_session_route(
    test_session_id: int,
    update_data: RavenSessionUpdate,
    session: Session = Depends(get_session),
):
    """更新测试会话信息"""
    test_session = update_test_session(session, test_session_id, update_data)
    if not test_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试会话不存在")
    return test_session


@router.get("/users/{user_id}/sessions", response_model=List[RavenSessionResponse])
async def list_user_sessions_route(user_id: int, session: Session = Depends(get_session)):
    """获取用户的所有测试会话"""
    return list_user_test_sessions(session, user_id)


@router.post("/sessions/{test_session_id}/complete", response_model=RavenSessionResponse)
async def complete_session_route(test_session_id: int, session: Session = Depends(get_session)):
    """完成测试会话"""
    test_session = complete_test_session(session, test_session_id)
    if not test_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试会话不存在")
    return test_session


@router.post("/answers", status_code=status.HTTP_201_CREATED)
async def save_answer_route(
    answer_data: RavenAnswerCreate, session: Session = Depends(get_session)
):
    """保存单个答题记录"""
    try:
        answer = save_answer(session, answer_data)
        return {"message": "答案保存成功", "id": answer.id}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"保存答案失败: {str(e)}"
        )


@router.post("/answers/batch", status_code=status.HTTP_201_CREATED)
async def save_answers_batch_route(
    batch_data: RavenAnswerBatchCreate, session: Session = Depends(get_session)
):
    """批量保存答题记录"""
    try:
        count = save_answers_batch(session, batch_data)
        return {"message": "答案保存成功", "count": count}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"批量保存答案失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"批量保存答案失败: {str(e)}"
        )


@router.get("/sessions/{test_session_id}/answers")
async def get_session_answers_route(test_session_id: int, session: Session = Depends(get_session)):
    """获取测试会话的所有答题记录"""
    test_session = get_test_session(session, test_session_id)
    if not test_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试会话不存在")
    return get_session_answers(session, test_session_id)


@router.get("/sessions/{test_session_id}/results", response_model=Dict[str, Any])
async def get_session_results_route(test_session_id: int, session: Session = Depends(get_session)):
    """获取测试结果"""
    results = get_test_results(session, test_session_id)
    if not results:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试会话不存在")
    return results


@router.get("/questions/{question_id}", response_model=QuestionInfo)
async def get_question_route(
    question_id: int, test_session_id: int = None, session: Session = Depends(get_session)
):
    """获取题目信息"""
    if question_id < 1 or question_id > TOTAL_QUESTIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"题目ID必须在1-{TOTAL_QUESTIONS}之间"
        )

    # 如果提供了test_session_id，检查是否已有答案
    user_answer = None
    if test_session_id:
        answers = get_session_answers(session, test_session_id)
        for answer in answers:
            if answer.question_id == question_id:
                user_answer = answer.user_answer
                break

    return get_question_info(question_id, user_answer)


@router.get("/questions", response_model=List[QuestionInfo])
async def get_all_questions_route(
    test_session_id: int = None, session: Session = Depends(get_session)
):
    """获取所有题目信息"""
    # 如果提供了test_session_id，加载用户已有答案
    user_answers = {}
    if test_session_id:
        answers = get_session_answers(session, test_session_id)
        for answer in answers:
            user_answers[answer.question_id] = answer.user_answer

    # 生成所有题目信息
    questions = []
    for question_id in range(1, TOTAL_QUESTIONS + 1):
        user_answer = user_answers.get(question_id)
        questions.append(get_question_info(question_id, user_answer))

    return questions


@router.get("/images/{image_name}")
async def get_image_route(image_name: str):
    """获取题目图片"""
    image_path = IMAGES_DIR / image_name

    if not image_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图片不存在")

    return FileResponse(image_path, media_type="image/jpeg")
