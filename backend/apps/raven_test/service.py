import json
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from pathlib import Path
from sqlmodel import Session, select

from config import settings
from logger_config import logger
from apps.users.models import User
from .models import (
    RavenTestSession,
    RavenAnswer,
    RavenSessionCreate,
    RavenSessionUpdate,
    RavenAnswerCreate,
    RavenAnswerBatchCreate,
    QuestionInfo,
)
from .scoring import calculate_score

# 数据文件路径
DATA_DIR = Path(settings.DATA_DIR)
ANSWER_KEY_PATH = DATA_DIR / "CRT_answer.json"

# 题目配置
GROUPS = ["A", "AB", "B", "C", "D", "E"]
QUESTIONS_PER_GROUP = 12
TOTAL_QUESTIONS = 72

# 缓存答案数据
_answer_key = None


def load_answer_key() -> Dict[str, List[int]]:
    """加载答案"""
    global _answer_key

    if _answer_key is not None:
        return _answer_key

    try:
        with open(ANSWER_KEY_PATH, "r", encoding="utf-8") as f:
            _answer_key = json.load(f)
        logger.info(f"成功加载答案数据")
        return _answer_key
    except Exception as e:
        logger.error(f"加载答案数据失败: {str(e)}")
        return {}


def get_question_info(question_id: int, user_answer: Optional[int] = None) -> QuestionInfo:
    """
    获取题目信息

    Args:
        question_id: 题目ID（1-72）
        user_answer: 用户已选答案

    Returns:
        QuestionInfo对象
    """
    # 计算组名和组内题号
    group_index = (question_id - 1) // QUESTIONS_PER_GROUP
    group_name = GROUPS[group_index]
    question_in_group = ((question_id - 1) % QUESTIONS_PER_GROUP) + 1

    # 前三组（A, AB, B）6个选项，后三组（C, D, E）8个选项
    num_options = 6 if group_index < 3 else 8

    # 构建图片URL
    # 主图片：/api/raven-test/images/question_{question_id:02d}_main.jpg
    main_image_url = f"/api/raven-test/images/question_{question_id:02d}_main.jpg"

    # 选项图片：/api/raven-test/images/question_{question_id:02d}_option_{option_id}.jpg
    option_image_urls = [
        f"/api/raven-test/images/question_{question_id:02d}_option_{i}.jpg"
        for i in range(1, num_options + 1)
    ]

    return QuestionInfo(
        question_id=question_id,
        group_name=group_name,
        question_in_group=question_in_group,
        num_options=num_options,
        main_image_url=main_image_url,
        option_image_urls=option_image_urls,
        user_answer=user_answer,
    )


def calculate_age(birth_date: date, test_date: date = None) -> float:
    """
    计算年龄（岁，小数）

    Args:
        birth_date: 出生日期
        test_date: 测试日期，默认为今天

    Returns:
        年龄（岁）
    """
    if test_date is None:
        test_date = date.today()

    # 计算年龄
    age = test_date.year - birth_date.year

    # 调整月份和日期
    if (test_date.month, test_date.day) < (birth_date.month, birth_date.day):
        age -= 1

    # 计算小数部分（基于天数）
    # 简化计算：使用365.25天
    if test_date.month >= birth_date.month and test_date.day >= birth_date.day:
        days_into_year = (test_date - date(test_date.year, birth_date.month, birth_date.day)).days
    else:
        days_into_year = (test_date - date(test_date.year - 1, birth_date.month, birth_date.day)).days

    age_decimal = age + (days_into_year / 365.25)

    return round(age_decimal, 2)


def create_test_session(session: Session, session_data: RavenSessionCreate) -> RavenTestSession:
    """创建新的瑞文测试会话"""
    # 检查用户是否存在
    user = session.get(User, session_data.user_id)
    if not user:
        raise ValueError(f"用户不存在: ID={session_data.user_id}")

    # 计算用户年龄
    user_age = None
    if user.birth_date:
        user_age = calculate_age(user.birth_date)
        logger.info(f"用户年龄: {user_age}岁")

    # 创建测试会话
    test_session = RavenTestSession(
        user_id=session_data.user_id,
        start_time=datetime.now(),
        user_age=user_age,
    )

    session.add(test_session)
    session.commit()
    session.refresh(test_session)

    logger.info(f"为用户 {user.name} 创建瑞文测试会话，ID: {test_session.id}")
    return test_session


def get_test_session(session: Session, test_session_id: int) -> Optional[RavenTestSession]:
    """获取测试会话信息"""
    return session.get(RavenTestSession, test_session_id)


def update_test_session(
    session: Session, test_session_id: int, update_data: RavenSessionUpdate
) -> Optional[RavenTestSession]:
    """更新测试会话信息"""
    test_session = session.get(RavenTestSession, test_session_id)
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


def save_answer(session: Session, answer_data: RavenAnswerCreate) -> RavenAnswer:
    """保存单个答题记录"""
    # 检查会话是否存在
    test_session = session.get(RavenTestSession, answer_data.test_session_id)
    if not test_session:
        raise ValueError(f"测试会话不存在: ID={answer_data.test_session_id}")

    # 检查用户是否存在
    user = session.get(User, answer_data.user_id)
    if not user:
        raise ValueError(f"用户不存在: ID={answer_data.user_id}")

    # 加载答案
    answer_key = load_answer_key()

    # 获取题目信息
    question_id = answer_data.question_id
    group_index = (question_id - 1) // QUESTIONS_PER_GROUP
    group_name = GROUPS[group_index]
    question_in_group = ((question_id - 1) % QUESTIONS_PER_GROUP)

    # 获取正确答案
    correct_answer = answer_key[group_name][question_in_group]

    # 判断是否正确
    is_correct = answer_data.user_answer == correct_answer

    # 检查是否已存在该题的答案，如果存在则更新
    existing_answer = session.exec(
        select(RavenAnswer).where(
            RavenAnswer.test_session_id == answer_data.test_session_id,
            RavenAnswer.question_id == question_id,
        )
    ).first()

    if existing_answer:
        # 更新现有答案
        existing_answer.user_answer = answer_data.user_answer
        existing_answer.is_correct = is_correct
        existing_answer.response_time = answer_data.response_time
        session.add(existing_answer)
        session.commit()
        session.refresh(existing_answer)
        return existing_answer
    else:
        # 创建新答案
        answer = RavenAnswer(
            user_id=answer_data.user_id,
            test_session_id=answer_data.test_session_id,
            question_id=question_id,
            group_name=group_name,
            user_answer=answer_data.user_answer,
            correct_answer=correct_answer,
            is_correct=is_correct,
            response_time=answer_data.response_time,
        )

        session.add(answer)
        session.commit()
        session.refresh(answer)

        return answer


def save_answers_batch(session: Session, batch_data: RavenAnswerBatchCreate) -> int:
    """批量保存答题记录"""
    # 检查会话是否存在
    test_session = session.get(RavenTestSession, batch_data.test_session_id)
    if not test_session:
        raise ValueError(f"测试会话不存在: ID={batch_data.test_session_id}")

    # 检查用户是否存在
    user = session.get(User, batch_data.user_id)
    if not user:
        raise ValueError(f"用户不存在: ID={batch_data.user_id}")

    # 加载答案
    answer_key = load_answer_key()

    count = 0
    for answer_item in batch_data.answers:
        question_id = answer_item["question_id"]
        user_answer = answer_item["user_answer"]
        response_time = answer_item.get("response_time")

        # 获取题目信息
        group_index = (question_id - 1) // QUESTIONS_PER_GROUP
        group_name = GROUPS[group_index]
        question_in_group = ((question_id - 1) % QUESTIONS_PER_GROUP)

        # 获取正确答案
        correct_answer = answer_key[group_name][question_in_group]

        # 判断是否正确
        is_correct = user_answer == correct_answer

        # 检查是否已存在该题的答案
        existing_answer = session.exec(
            select(RavenAnswer).where(
                RavenAnswer.test_session_id == batch_data.test_session_id,
                RavenAnswer.question_id == question_id,
            )
        ).first()

        if existing_answer:
            # 更新现有答案
            existing_answer.user_answer = user_answer
            existing_answer.is_correct = is_correct
            existing_answer.response_time = response_time
            session.add(existing_answer)
        else:
            # 创建新答案
            answer = RavenAnswer(
                user_id=batch_data.user_id,
                test_session_id=batch_data.test_session_id,
                question_id=question_id,
                group_name=group_name,
                user_answer=user_answer,
                correct_answer=correct_answer,
                is_correct=is_correct,
                response_time=response_time,
            )
            session.add(answer)

        count += 1

    # 批量提交
    session.commit()

    return count


def complete_test_session(session: Session, test_session_id: int) -> Optional[RavenTestSession]:
    """完成测试会话并计算结果"""
    test_session = session.get(RavenTestSession, test_session_id)
    if not test_session:
        return None

    # 获取所有答题记录
    answers = session.exec(
        select(RavenAnswer).where(RavenAnswer.test_session_id == test_session_id)
    ).all()

    # 计算原始分数
    raw_score = sum(1 for answer in answers if answer.is_correct)

    # 更新当前进度
    test_session.current_question = len(answers)

    # 计算百分位、Z分数和IQ
    if test_session.user_age is not None:
        percentile, z_score, iq = calculate_score(test_session.user_age, raw_score)
        test_session.percentile = percentile
        test_session.z_score = z_score
        test_session.iq = iq
    else:
        logger.warning(f"用户年龄未知，无法计算标准分数")

    # 更新测试会话
    test_session.is_completed = True
    test_session.end_time = datetime.now()
    test_session.raw_score = raw_score

    # 计算总用时（秒）
    delta = test_session.end_time - test_session.start_time
    test_session.total_time_seconds = int(delta.total_seconds())

    session.add(test_session)
    session.commit()
    session.refresh(test_session)

    logger.info(f"完成测试会话 {test_session_id}, 原始分数: {raw_score}, IQ: {test_session.iq}")
    return test_session


def get_session_answers(session: Session, test_session_id: int) -> List[RavenAnswer]:
    """获取测试会话的所有答题记录"""
    query = (
        select(RavenAnswer)
        .where(RavenAnswer.test_session_id == test_session_id)
        .order_by(RavenAnswer.question_id)
    )

    return session.exec(query).all()


def get_test_results(session: Session, test_session_id: int) -> Optional[Dict[str, Any]]:
    """获取测试结果"""
    test_session = session.get(RavenTestSession, test_session_id)
    if not test_session:
        return None

    # 获取用户
    user = session.get(User, test_session.user_id) if test_session.user_id else None

    # 获取所有答题记录
    answers = get_session_answers(session, test_session_id)

    # 构建结果
    results = {
        "user": user,
        "session": test_session,
        "answers": answers,
        "stats": {
            "totalQuestions": TOTAL_QUESTIONS,
            "answeredQuestions": len(answers),
            "correctAnswers": test_session.raw_score,
            "rawScore": test_session.raw_score,
            "percentile": test_session.percentile,
            "zScore": test_session.z_score,
            "iq": test_session.iq,
            "totalTimeSeconds": test_session.total_time_seconds,
        },
    }

    return results


def list_user_test_sessions(session: Session, user_id: int) -> List[RavenTestSession]:
    """获取用户的所有测试会话"""
    query = select(RavenTestSession).where(RavenTestSession.user_id == user_id)
    return session.exec(query).all()
