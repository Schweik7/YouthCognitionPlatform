from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlmodel import Session, select

from logger_config import logger
from apps.users.models import User
from .models import (
    CalculationTestSession,
    CalculationProblem,
    TestSessionCreate,
    TestSessionUpdate,
    ProblemData,
)


def create_test_session(
    session: Session, test_session_data: TestSessionCreate
) -> CalculationTestSession:
    """创建新的计算流畅性测试会话"""
    # 检查用户是否存在
    user = session.get(User, test_session_data.user_id)
    if not user:
        raise ValueError(f"用户不存在: ID={test_session_data.user_id}")

    # 创建测试会话
    test_session = CalculationTestSession(
        user_id=test_session_data.user_id,
        grade_level=test_session_data.grade_level,
        total_questions=test_session_data.total_questions,
        start_time=datetime.now(),
    )

    session.add(test_session)
    session.commit()
    session.refresh(test_session)

    logger.info(
        f"为用户 {user.name} 创建计算流畅性测试会话，ID: {test_session.id}, 年级: {test_session.grade_level}"
    )
    return test_session


def get_test_session(session: Session, test_session_id: int) -> Optional[CalculationTestSession]:
    """获取测试会话信息"""
    return session.get(CalculationTestSession, test_session_id)


def update_test_session(
    session: Session, test_session_id: int, update_data: TestSessionUpdate
) -> Optional[CalculationTestSession]:
    """更新测试会话信息"""
    # 获取测试会话
    test_session = session.get(CalculationTestSession, test_session_id)
    if not test_session:
        return None

    # 更新字段
    update_dict = update_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(test_session, key, value)

    # 如果已完成且未设置结束时间，自动设置
    if update_data.is_completed and not test_session.end_time:
        test_session.end_time = datetime.now()
        # 计算总用时（秒）
        delta = test_session.end_time - test_session.start_time
        test_session.total_time_seconds = int(delta.total_seconds())

    session.add(test_session)
    session.commit()
    session.refresh(test_session)

    return test_session


def list_user_test_sessions(session: Session, user_id: int) -> List[CalculationTestSession]:
    """获取用户的所有测试会话"""
    query = select(CalculationTestSession).where(CalculationTestSession.user_id == user_id)
    return list(session.exec(query).all())


def complete_test_session(
    session: Session, test_session_id: int
) -> Optional[CalculationTestSession]:
    """完成测试会话"""
    test_session = session.get(CalculationTestSession, test_session_id)
    if not test_session:
        return None

    # 标记为完成并设置结束时间
    test_session.is_completed = True
    test_session.end_time = datetime.now()

    # 计算总用时（秒）
    delta = test_session.end_time - test_session.start_time
    test_session.total_time_seconds = int(delta.total_seconds())

    session.add(test_session)
    session.commit()
    session.refresh(test_session)

    return test_session


def save_problem(
    session: Session, test_session_id: int, problem_data: ProblemData
) -> CalculationProblem:
    """保存计算题目记录"""
    # 检查会话是否存在
    test_session = session.get(CalculationTestSession, test_session_id)
    if not test_session:
        raise ValueError(f"测试会话不存在: ID={test_session_id}")

    # 检查用户是否存在
    user = session.get(User, problem_data.user_id)
    if not user:
        raise ValueError(f"用户不存在: ID={problem_data.user_id}")

    # 验证用户答案是否正确
    is_correct = problem_data.user_answer == problem_data.correct_answer

    # 创建计算题目记录
    problem = CalculationProblem(
        user_id=problem_data.user_id,
        test_session_id=test_session_id,
        problem_index=problem_data.problem_index,
        problem_text=problem_data.problem_text,
        correct_answer=problem_data.correct_answer,
        user_answer=problem_data.user_answer,
        is_correct=is_correct,
        response_time=problem_data.response_time,
    )

    session.add(problem)

    # 更新测试会话进度和正确数量
    test_session.progress += 1
    if is_correct:
        test_session.correct_count += 1

    session.add(test_session)
    session.commit()
    session.refresh(problem)

    return problem


def get_session_problems(session: Session, test_session_id: int) -> List[CalculationProblem]:
    """获取测试会话中的所有计算题目记录"""
    query = (
        select(CalculationProblem)
        .where(CalculationProblem.test_session_id == test_session_id)
        .order_by(CalculationProblem.problem_index)
    )

    return list(session.exec(query).all())


def get_test_session_results(session: Session, test_session_id: int) -> Dict[str, Any] | None:
    """获取单次测试会话的结果"""
    # 获取测试会话
    test_session = session.get(CalculationTestSession, test_session_id)
    if not test_session:
        return None

    # 获取用户
    user = session.get(User, test_session.user_id) if test_session.user_id else None

    # 获取所有计算题目记录
    problems = get_session_problems(session, test_session_id)

    # 计算各类题型的正确率
    # 一年级: 加法题和减法题
    # 二年级: 两数加减法和三数加减法
    # 三年级: 两位数加减法、三位数加减法和三位数三数加减法

    # 初始化统计数据
    stats = {
        "totalProblems": len(problems),
        "correctProblems": sum(1 for p in problems if p.is_correct),
        "accuracy": test_session.accuracy,
        "completionRate": test_session.completion_rate,
        "totalTimeSeconds": test_session.total_time_seconds,
        "averageResponseTime": sum(p.response_time for p in problems) / max(len(problems), 1),
        "problemTypeStats": {},
    }

    # 根据年级分析题型
    if test_session.grade_level == 1:
        # 一年级: 加法题和减法题
        addition_problems = [p for p in problems if "+" in p.problem_text]
        subtraction_problems = [p for p in problems if "-" in p.problem_text]

        stats["problemTypeStats"] = {
            "addition": {
                "total": len(addition_problems),
                "correct": sum(1 for p in addition_problems if p.is_correct),
                "accuracy": sum(1 for p in addition_problems if p.is_correct)
                / max(len(addition_problems), 1)
                * 100,
            },
            "subtraction": {
                "total": len(subtraction_problems),
                "correct": sum(1 for p in subtraction_problems if p.is_correct),
                "accuracy": sum(1 for p in subtraction_problems if p.is_correct)
                / max(len(subtraction_problems), 1)
                * 100,
            },
        }
    elif test_session.grade_level == 2:
        # 二年级: 两数加减法和三数加减法
        two_num_problems = [
            p for p in problems if p.problem_text.count("+") + p.problem_text.count("-") == 1
        ]
        three_num_problems = [
            p for p in problems if p.problem_text.count("+") + p.problem_text.count("-") == 2
        ]

        stats["problemTypeStats"] = {
            "twoNumbers": {
                "total": len(two_num_problems),
                "correct": sum(1 for p in two_num_problems if p.is_correct),
                "accuracy": sum(1 for p in two_num_problems if p.is_correct)
                / max(len(two_num_problems), 1)
                * 100,
            },
            "threeNumbers": {
                "total": len(three_num_problems),
                "correct": sum(1 for p in three_num_problems if p.is_correct),
                "accuracy": sum(1 for p in three_num_problems if p.is_correct)
                / max(len(three_num_problems), 1)
                * 100,
            },
        }
    elif test_session.grade_level == 3:
        # 三年级: 分类统计
        # 简化统计，只按照操作数的位数分类
        stats["problemTypeStats"] = {
            "twoDigitOperations": {
                "total": sum(1 for p in problems if p.problem_index <= 10),
                "correct": sum(1 for p in problems if p.problem_index <= 10 and p.is_correct),
                "accuracy": sum(1 for p in problems if p.problem_index <= 10 and p.is_correct)
                / max(sum(1 for p in problems if p.problem_index <= 10), 1)
                * 100,
            },
            "threeDigitOperations": {
                "total": sum(1 for p in problems if 10 < p.problem_index <= 30),
                "correct": sum(1 for p in problems if 10 < p.problem_index <= 30 and p.is_correct),
                "accuracy": sum(1 for p in problems if 10 < p.problem_index <= 30 and p.is_correct)
                / max(sum(1 for p in problems if 10 < p.problem_index <= 30), 1)
                * 100,
            },
            "threeDigitThreeNumbers": {
                "total": sum(1 for p in problems if p.problem_index > 30),
                "correct": sum(1 for p in problems if p.problem_index > 30 and p.is_correct),
                "accuracy": sum(1 for p in problems if p.problem_index > 30 and p.is_correct)
                / max(sum(1 for p in problems if p.problem_index > 30), 1)
                * 100,
            },
        }

    # 构建结果
    results = {
        "user": user,
        "session": test_session,
        "problems": problems,
        "stats": stats,
    }

    return results
