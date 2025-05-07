import os
import csv
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlmodel import Session, select, or_
from pathlib import Path

from config import settings
from apps.users.models import User
from .models import Trial, TrialData, UserTrialData

# 数据文件路径
data_dir = Path(settings.DATA_DIR)
practice_trial_path = data_dir / "教学阶段.csv"
formal_trial_path = data_dir / "正式阶段.csv"

# 缓存数据
_practice_trials = None
_formal_trials = None


def read_csv_trials(file_path: Path) -> List[str]:
    """从CSV文件读取试题"""
    if not file_path.exists():
        print(f"警告: 文件不存在 {file_path}")
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
        print(f"解析CSV文件失败: {file_path}, 错误: {str(e)}")
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

    print(f"成功加载 {len(_practice_trials)} 个练习题和 {len(_formal_trials)} 个正式题")

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


def save_trial(session: Session, trial_data: UserTrialData) -> Trial:
    """保存试验数据（支持传入用户信息）"""
    # 查找或创建用户
    user = find_or_create_user(
        session=session,
        name=trial_data.name,
        school=trial_data.school,
        grade=trial_data.grade,
        class_number=trial_data.class_number,
    )

    # 创建试验记录
    trial = Trial(
        user_id=user.id,
        trial_id=trial_data.trial_id,
        user_answer=trial_data.user_answer,
        response_time=trial_data.response_time,
    )

    session.add(trial)
    session.commit()
    session.refresh(trial)

    return trial


def save_trial_direct(session: Session, trial_data: TrialData) -> Trial:
    """直接保存试验数据（已知用户ID）"""
    # 检查用户是否存在
    user = session.get(User, trial_data.user_id)
    if not user:
        raise ValueError(f"用户不存在: ID={trial_data.user_id}")

    # 创建试验记录
    trial = Trial(
        user_id=trial_data.user_id,
        trial_id=trial_data.trial_id,
        user_answer=trial_data.user_answer,
        response_time=trial_data.response_time,
    )

    session.add(trial)
    session.commit()
    session.refresh(trial)

    return trial


def get_user_results(session: Session, user_id: int) -> Dict[str, Any]:
    """获取用户实验结果"""
    # 查找用户
    user = session.get(User, user_id)
    if not user:
        return None

    # 查询用户所有试验记录
    trials_query = select(Trial).where(Trial.user_id == user_id)
    trials = session.exec(trials_query).all()

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
            },
            "trials": [],
        }

    correct_trials = sum(1 for trial in trials if trial.user_answer)
    average_response_time = sum(trial.response_time for trial in trials) / total_trials

    results = {
        "user": user,
        "results": {
            "totalTrials": total_trials,
            "correctTrials": correct_trials,
            "accuracy": (correct_trials / total_trials) * 100,
            "averageResponseTime": average_response_time,
        },
        "trials": trials,
    }

    return results
