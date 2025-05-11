import os
import csv
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlmodel import Session, select, or_, update
from pathlib import Path
import csv
from config import settings
from logger_config import logger
from apps.users.models import User
from .models import (
    Trial,
    TestSession,
    TrialData,
    UserTrialData,
    TestSessionCreate,
    TestSessionUpdate,
    TestSessionResponse,
    Answer,
)


# 数据文件路径
data_dir = Path(settings.DATA_DIR)
practice_trial_path = data_dir / "教学阶段.csv"
formal_trial_path = data_dir / "正式阶段.csv"
_standard_answers: Dict[int, bool] = {}
# 缓存数据
_practice_trials = None
_formal_trials = None


def load_standard_answers() -> Dict[int, bool]:
    """从CSV文件加载标准答案"""
    global _standard_answers
    if _standard_answers:
        return _standard_answers
    answers_path = data_dir / "阅读流畅性测试标准答案.csv"
    if not answers_path.exists():
        logger.warning(f"标准答案文件不存在 {answers_path}")
        return {}
    try:
        with open(answers_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    trial_id = int(row["id"])
                    # 注意CSV中的TRUE/FALSE是字符串，需要转换为布尔值
                    is_correct = row["answer"].strip().upper() == "TRUE"
                    _standard_answers[trial_id] = is_correct
                except (ValueError, KeyError) as e:
                    logger.error(f"解析标准答案行失败: {row}, 错误: {str(e)}")
                    continue
        logger.info(f"成功加载 {len(_standard_answers)} 个标准答案")
        return _standard_answers
    except Exception as e:
        logger.error(f"加载标准答案失败: {str(e)}")
        return {}


answers = load_standard_answers()
# logger.info(answers)


# 判断用户答案是否正确
def check_answer(trial_id: int, user_answer: bool) -> bool:
    """检查用户答案是否正确"""
    # logger.debug(
    #     f"检查试题ID {trial_id} 的答案: 用户答案 {user_answer}, 标准答案 {answers[trial_id]}"
    # )
    if trial_id not in answers:
        logger.warning(f"试题ID {trial_id} 没有对应的标准答案")
        return False

    return user_answer == answers[trial_id]


def read_csv_trials(file_path: Path) -> List[str]:
    """从CSV文件读取试题"""
    if not file_path.exists():
        logger.warning(f"文件不存在 {file_path}")
        return []

    try:
        # 尝试读取CSV文件
        trials = []

        # 使用pandas读取，处理可能的编码问题
        df = pd.read_csv(file_path, header=None, encoding="utf-8")

        # 提取句子内容 (第二列或第一列)
        for _, row in df.iterrows():
            sentence = row[1] if len(row) > 1 and pd.notna(row[1]) else row[0]
            trials.append(sentence)

        return trials
    except Exception as e:
        logger.error(f"解析CSV文件失败: {file_path}, 错误: {str(e)}")
        return []


def get_trials() -> Dict[str, List[str]]:
    """获取所有试题数据"""
    global _practice_trials, _formal_trials

    # 如果已缓存则直接返回
    if _practice_trials is not None and _formal_trials is not None:
        return {"practiceTrials": _practice_trials, "formalTrials": _formal_trials}

    # 读取试题数据
    _practice_trials = read_csv_trials(practice_trial_path)
    _formal_trials = read_csv_trials(formal_trial_path)

    logger.info(f"成功加载 {len(_practice_trials)} 个练习题和 {len(_formal_trials)} 个正式题")

    return {"practiceTrials": _practice_trials, "formalTrials": _formal_trials}


def find_or_create_user(
    session: Session, name: str, school: str, grade: int, class_number: int
) -> User:
    """查找或创建用户 (向后兼容旧API)"""
    # 尝试查找已存在的用户
    query = select(User).where(
        User.name == name,
        User.school == school,
        User.grade == grade,
        User.class_number == class_number,
    )
    user = session.exec(query).first()

    # 如果不存在则创建
    if not user:
        user = User(name=name, school=school, grade=grade, class_number=class_number)
        session.add(user)
        session.commit()
        session.refresh(user)

    return user


# 同样修改直接保存试验数据的函数
def save_trial_direct(session: Session, trial_data: TrialData) -> Trial:
    """直接保存试验数据（已知用户ID），并判断答案正确性"""
    # 检查用户是否存在
    user = session.get(User, trial_data.user_id)
    if not user:
        raise ValueError(f"用户不存在: ID={trial_data.user_id}")

    # 判断用户答案是否正确
    is_correct = check_answer(trial_data.trial_id, trial_data.user_answer)

    # 创建试验记录
    trial = Trial(
        user_id=trial_data.user_id,
        test_session_id=trial_data.test_session_id,  # 可能为 None
        trial_id=trial_data.trial_id,
        user_answer=trial_data.user_answer,
        is_correct=is_correct,  # 设置是否正确
        response_time=trial_data.response_time,
    )

    session.add(trial)

    # 如果有测试会话，更新进度和正确数量
    if trial_data.test_session_id:
        test_session = session.get(TestSession, trial_data.test_session_id)
        if test_session:
            test_session.progress += 1
            if is_correct:
                test_session.correct_count += 1
            session.add(test_session)

    session.commit()
    session.refresh(trial)

    return trial


def get_test_session_results(session: Session, test_session_id: int) -> Dict[str, Any] | None:
    """获取单次测试会话的结果"""
    # 获取测试会话
    test_session = session.get(TestSession, test_session_id)
    if not test_session:
        return None

    # 获取用户
    user = session.get(User, test_session.user_id) if test_session.user_id else None

    # 获取所有试验记录
    trials = get_session_trials(session, test_session_id)

    # 计算统计信息
    total_trials = len(trials)
    correct_trials = sum(1 for trial in trials if trial.is_correct or trial.user_answer)
    avg_response_time = (
        sum(trial.response_time for trial in trials) / total_trials if total_trials > 0 else 0
    )

    # 构建结果
    results = {
        "testSession": test_session,
        "user": user,
        "trials": trials,
        "stats": {
            "totalTrials": total_trials,
            "correctTrials": correct_trials,
            "accuracy": (correct_trials / total_trials * 100) if total_trials > 0 else 0,
            "averageResponseTime": avg_response_time,
            "completionRate": (
                (test_session.progress / test_session.total_questions * 100)
                if test_session.total_questions > 0
                else 0
            ),
            "totalTimeSeconds": test_session.total_time_seconds,
        },
    }

    return results


# 测试会话相关功能
def create_test_session(session: Session, test_session_data: TestSessionCreate) -> TestSession:
    """创建新的测试会话"""
    # 检查用户是否存在
    user = session.get(User, test_session_data.user_id)
    if not user:
        raise ValueError(f"用户不存在: ID={test_session_data.user_id}")

    # 创建测试会话
    test_session = TestSession(
        user_id=test_session_data.user_id,
        total_questions=test_session_data.total_questions,
        start_time=datetime.now(),
    )

    session.add(test_session)
    session.commit()
    session.refresh(test_session)

    logger.info(f"为用户 {user.name} 创建测试会话，ID: {test_session.id}")
    return test_session


def get_test_session(session: Session, test_session_id: int) -> Optional[TestSession]:
    """获取测试会话信息"""
    return session.get(TestSession, test_session_id)


def update_test_session(
    session: Session, test_session_id: int, update_data: TestSessionUpdate
) -> Optional[TestSession]:
    """更新测试会话信息"""
    # 获取测试会话
    test_session = session.get(TestSession, test_session_id)
    if not test_session:
        return None

    # 更新字段
    update_dict = update_data.dict(exclude_unset=True)

    # 如果前端更新了 progress，但没有提供 correct_count，我们需要计算正确数量
    if "progress" in update_dict and "correct_count" not in update_dict:
        # 查询该会话中用户回答正确的试验记录数量
        correct_trials_query = select(Trial).where(
            Trial.test_session_id == test_session_id, Trial.is_correct == True
        )
        correct_trials = session.exec(correct_trials_query).all()
        update_dict["correct_count"] = len(correct_trials)
        logger.info(
            f"根据试验记录计算会话 {test_session_id} 的正确答题数: {update_dict['correct_count']}"
        )

    # 更新会话字段
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


def list_user_test_sessions(session: Session, user_id: int) -> List[TestSession]:
    """获取用户的所有测试会话"""
    query = select(TestSession).where(TestSession.user_id == user_id)
    return session.exec(query).all()


def complete_test_session(session: Session, test_session_id: int) -> Optional[TestSession]:
    """完成测试会话"""
    test_session = session.get(TestSession, test_session_id)
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


# 修改试验保存函数，支持判断是否正确
def save_trial_with_session(session: Session, test_session_id: int, trial_data: TrialData) -> Trial:
    """在指定测试会话中保存试验记录，并判断答案正确性"""
    # 获取测试会话
    test_session = session.get(TestSession, test_session_id)
    if not test_session:
        raise ValueError(f"测试会话不存在: ID={test_session_id}")

    # 判断用户答案是否正确
    is_correct = check_answer(trial_data.trial_id, trial_data.user_answer)

    # 创建试验记录
    trial = Trial(
        user_id=trial_data.user_id,
        test_session_id=test_session_id,
        trial_id=trial_data.trial_id,
        user_answer=trial_data.user_answer,
        is_correct=is_correct,  # 设置是否正确
        response_time=trial_data.response_time,
    )

    session.add(trial)

    # 更新测试会话进度和正确数量
    test_session.progress += 1
    if is_correct:
        test_session.correct_count += 1

    session.add(test_session)
    session.commit()
    session.refresh(trial)

    return trial


# 修改原始保存方法也支持判断正确性
def save_trial(session: Session, trial_data: UserTrialData) -> Trial:
    """保存试验数据（支持传入用户信息，向后兼容）"""
    # 查找或创建用户
    user = find_or_create_user(
        session=session,
        name=trial_data.name,
        school=trial_data.school,
        grade=trial_data.grade,
        class_number=trial_data.class_number,
    )

    # 判断用户答案是否正确
    is_correct = check_answer(trial_data.trial_id, trial_data.user_answer)

    # 创建试验记录
    trial = Trial(
        user_id=user.id,
        trial_id=trial_data.trial_id,
        user_answer=trial_data.user_answer,
        is_correct=is_correct,  # 设置是否正确
        response_time=trial_data.response_time,
    )

    session.add(trial)
    session.commit()
    session.refresh(trial)

    return trial


def get_user_results(session: Session, user_id: int) -> Dict[str, Any] | None:
    """获取用户实验结果"""
    # 查找用户
    user = session.get(User, user_id)
    if not user:
        return None

    # 查询用户所有试验记录
    trials_query = select(Trial).where(Trial.user_id == user_id)
    trials = session.exec(trials_query).all()

    # 查询用户的所有测试会话
    sessions_query = select(TestSession).where(TestSession.user_id == user_id)
    test_sessions = session.exec(sessions_query).all()

    # 计算结果统计
    total_trials = len(trials)
    if total_trials == 0:
        return {
            "user": user,
            "results": {
                "totalTrials": 0,
                "correctTrials": 0,
                "accuracy": 0,
                "averageResponseTime": 0,
                "totalSessions": len(test_sessions),
                "completedSessions": sum(1 for s in test_sessions if s.is_completed),
            },
            "trials": [],
            "testSessions": test_sessions,
        }

    correct_trials = sum(1 for trial in trials if trial.is_correct or trial.user_answer)
    average_response_time = sum(trial.response_time for trial in trials) / total_trials

    results = {
        "user": user,
        "results": {
            "totalTrials": total_trials,
            "correctTrials": correct_trials,
            "accuracy": (correct_trials / total_trials) * 100,
            "averageResponseTime": average_response_time,
            "totalSessions": len(test_sessions),
            "completedSessions": sum(1 for s in test_sessions if s.is_completed),
        },
        "trials": trials,
        "testSessions": test_sessions,
    }

    return results


def get_session_trials(session: Session, test_session_id: int) -> List[Trial]:
    """获取测试会话中的所有试验记录"""
    query = select(Trial).where(Trial.test_session_id == test_session_id)
    return session.exec(query).all()
