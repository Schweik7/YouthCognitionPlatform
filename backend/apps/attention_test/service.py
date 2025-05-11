import os
import json
import random
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlmodel import Session, select, or_, update
from pathlib import Path

from config import settings
from logger_config import logger
from apps.users.models import User
from .models import (
    AttentionTestSession,
    AttentionRecord,
    AttentionRecordCreate,
    AttentionSessionCreate,
    AttentionSessionUpdate,
)

# 数据文件路径
data_dir = Path(settings.DATA_DIR)
symbol_set_path = data_dir / "注意力筛查字符集.txt"
matrix_path = data_dir / "attention_matrix.txt"
targets_path = data_dir / "attention_targets.json"

# 缓存数据
_symbol_set = None
_symbol_matrix = None
_target_positions = None
_metadata = None

# 行列配置
SYMBOLS_PER_ROW =40  # 每行符号数
TOTAL_ROWS = 26  # 总行数
PRACTICE_ROWS = 1  # 练习阶段行数


def load_symbol_set() -> List[str]:
    """从文件加载字符集"""
    global _symbol_set

    if _symbol_set:
        return _symbol_set

    if not symbol_set_path.exists():
        logger.warning(f"字符集文件不存在 {symbol_set_path}")
        return ["Π", "Θ", "Ψ", "≅", "⊕", "א", "Ϡ", "ʆ", "Ԅ", "Φ"]  # 默认字符集

    try:
        with open(symbol_set_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            _symbol_set = list(content)
        logger.info(f"成功加载 {len(_symbol_set)} 个字符")
        return _symbol_set
    except Exception as e:
        logger.error(f"加载字符集失败: {str(e)}")
        return ["Π", "Θ", "Ψ", "≅", "⊕", "א", "Ϡ", "ʆ", "Ԅ", "Φ"]  # 默认字符集


def load_symbol_matrix() -> List[List[str]]:
    """加载符号矩阵"""
    global _symbol_matrix

    if _symbol_matrix:
        return _symbol_matrix

    if not matrix_path.exists():
        logger.warning(f"符号矩阵文件不存在 {matrix_path}")
        return []

    try:
        matrix = []
        with open(matrix_path, "r", encoding="utf-8") as f:
            for line in f:
                # 将每行字符串转换为字符列表
                row = list(line.strip())
                matrix.append(row)

        _symbol_matrix = matrix
        logger.info(f"成功加载符号矩阵，大小: {len(matrix)}×{len(matrix[0]) if matrix else 0}")
        return _symbol_matrix
    except Exception as e:
        logger.error(f"加载符号矩阵失败: {str(e)}")
        return []


def load_target_positions() -> Tuple[Dict[str, List[Tuple[int, int]]], Dict[str, Any]]:
    """从JSON文件加载目标位置数据"""
    global _target_positions, _metadata

    if _target_positions is not None and _metadata is not None:
        return _target_positions, _metadata

    if not targets_path.exists():
        logger.warning(f"目标位置文件不存在 {targets_path}，将使用随机生成的位置")
        return {}, {}

    try:
        with open(targets_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 将字符串格式的位置元组转换回Python元组
            _target_positions = {}
            for symbol, positions in data["target_positions"].items():
                _target_positions[symbol] = [(int(pos[0]), int(pos[1])) for pos in positions]

            _metadata = data["metadata"]

        logger.info(f"成功加载目标位置数据，包含 {len(_target_positions)} 个符号的位置")
        return _target_positions, _metadata
    except Exception as e:
        logger.error(f"加载目标位置数据失败: {str(e)}")
        return {}, {}


def select_random_target_symbol() -> str:
    """随机选择一个目标符号"""
    symbols = load_symbol_set()
    return random.choice(symbols)


def generate_symbol_grid(target_symbol: str, is_practice: bool = False) -> List[Dict[str, Any]]:
    """根据指定的目标符号生成符号网格"""
    # 加载符号矩阵和目标位置数据
    matrix = load_symbol_matrix()
    target_positions, _ = load_target_positions()

    if not matrix:
        logger.error("符号矩阵为空，无法生成网格")
        return []

    # 确定生成的行
    start_row = 0
    end_row = 1 if is_practice else len(matrix)  # 练习模式只返回第一行

    # 生成网格
    grid = []

    # 获取目标符号的位置集合
    target_positions_set = set(target_positions.get(target_symbol, []))

    # 为每行每列生成符号项
    for row in range(start_row, end_row):
        if row >= len(matrix):
            continue

        for col in range(len(matrix[row])):
            # 获取矩阵中的实际符号
            actual_symbol = matrix[row][col]

            # 判断是否是目标位置
            is_target = (row, col) in target_positions_set

            # 将符号添加到网格
            grid.append(
                {
                    "row_index": row,
                    "col_index": col,
                    "symbol": actual_symbol,
                    "is_target": is_target and actual_symbol == target_symbol,
                    "is_clicked": False,
                }
            )

    return grid


def generate_practice_sequence(target_symbol: str) -> List[Dict[str, Any]]:
    """生成练习阶段序列"""
    return generate_symbol_grid(target_symbol, is_practice=True)


def generate_test_sequence(target_symbol: str) -> List[Dict[str, Any]]:
    """生成测试阶段序列"""
    return generate_symbol_grid(target_symbol, is_practice=False)


def create_test_session(
    session: Session, test_session_data: AttentionSessionCreate
) -> AttentionTestSession:
    """创建新的注意力测试会话"""
    # 检查用户是否存在
    user = session.get(User, test_session_data.user_id)
    if not user:
        raise ValueError(f"用户不存在: ID={test_session_data.user_id}")

    # 如果未指定目标符号，随机选择一个
    # target_symbol = test_session_data.target_symbol
    # logger.info(f"用户指定目标符号：{target_symbol}")
    # if not target_symbol:
    target_symbol = select_random_target_symbol()
    logger.info(f"随机选择目标符号：{target_symbol}")
    # 创建测试会话
    test_session = AttentionTestSession(
        user_id=test_session_data.user_id,
        target_symbol=target_symbol,
        start_time=datetime.now(),
    )

    session.add(test_session)
    session.commit()
    session.refresh(test_session)

    logger.info(
        f"为用户 {user.name} 创建注意力测试会话，ID: {test_session.id}, 目标符号: {target_symbol}"
    )
    return test_session


def get_test_session(session: Session, test_session_id: int) -> Optional[AttentionTestSession]:
    """获取测试会话信息"""
    return session.get(AttentionTestSession, test_session_id)


def update_test_session(
    session: Session, test_session_id: int, update_data: AttentionSessionUpdate
) -> Optional[AttentionTestSession]:
    """更新测试会话信息"""
    # 获取测试会话
    test_session = session.get(AttentionTestSession, test_session_id)
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


def list_user_test_sessions(session: Session, user_id: int) -> List[AttentionTestSession]:
    """获取用户的所有测试会话"""
    query = select(AttentionTestSession).where(AttentionTestSession.user_id == user_id)
    return session.exec(query).all()


def analyze_user_submissions(session: Session, test_session_id: int) -> Dict[str, Any]:
    """分析用户的提交并计算结果"""
    # 获取测试会话
    test_session = session.get(AttentionTestSession, test_session_id)
    if not test_session:
        raise ValueError(f"测试会话不存在: ID={test_session_id}")

    # 获取用户的所有点击记录
    records_query = select(AttentionRecord).where(
        AttentionRecord.test_session_id == test_session_id
    )
    user_records = session.exec(records_query).all()

    # 获取目标符号
    target_symbol = test_session.target_symbol

    # 计算结果
    correct_count = sum(1 for record in user_records if record.is_target and record.is_clicked)
    incorrect_count = sum(
        1 for record in user_records if not record.is_target and record.is_clicked
    )

    # 计算遗漏的目标符号
    # 首先获取所有标记为目标的记录
    target_records_query = select(AttentionRecord).where(
        AttentionRecord.test_session_id == test_session_id, AttentionRecord.is_target == True
    )
    target_records = session.exec(target_records_query).all()

    # 遗漏数是目标记录中未被点击的数量
    missed_count = sum(1 for record in target_records if not record.is_clicked)

    # 计算总分
    total_score = correct_count - incorrect_count - (0.5 * missed_count)
    total_score = max(0, total_score)  # 不允许负分

    return {
        "correct_count": correct_count,
        "incorrect_count": incorrect_count,
        "missed_count": missed_count,
        "total_score": total_score,
    }


def complete_test_session(session: Session, test_session_id: int) -> Optional[AttentionTestSession]:
    """完成测试会话并计算结果"""
    test_session = session.get(AttentionTestSession, test_session_id)
    if not test_session:
        return None

    # 分析用户提交并计算结果
    results = analyze_user_submissions(session, test_session_id)

    # 更新测试会话
    test_session.is_completed = True
    test_session.end_time = datetime.now()
    test_session.correct_count = results["correct_count"]
    test_session.incorrect_count = results["incorrect_count"]
    test_session.missed_count = results["missed_count"]
    test_session.total_score = results["total_score"]

    # 计算总用时（秒）
    delta = test_session.end_time - test_session.start_time
    test_session.total_time_seconds = int(delta.total_seconds())

    session.add(test_session)
    session.commit()
    session.refresh(test_session)

    logger.info(f"完成测试会话 {test_session_id}, 得分: {test_session.total_score}")
    return test_session


def save_attention_record(session: Session, record_data: AttentionRecordCreate) -> AttentionRecord:
    """保存注意力测试记录"""
    # 检查会话是否存在
    test_session = session.get(AttentionTestSession, record_data.test_session_id)
    if not test_session:
        raise ValueError(f"测试会话不存在: ID={record_data.test_session_id}")

    # 检查用户是否存在
    user = session.get(User, record_data.user_id)
    if not user:
        raise ValueError(f"用户不存在: ID={record_data.user_id}")

    # 判断是否正确
    is_correct = (record_data.is_target and record_data.is_clicked) or (
        not record_data.is_target and not record_data.is_clicked
    )

    # 创建记录
    record = AttentionRecord(
        user_id=record_data.user_id,
        test_session_id=record_data.test_session_id,
        row_index=record_data.row_index,
        col_index=record_data.col_index,
        symbol=record_data.symbol,
        is_target=record_data.is_target,
        is_clicked=record_data.is_clicked,
        is_correct=is_correct,
        response_time=record_data.response_time,
    )

    session.add(record)
    session.commit()
    session.refresh(record)

    return record


def get_test_session_records(session: Session, test_session_id: int) -> List[AttentionRecord]:
    """获取测试会话中的所有记录"""
    query = (
        select(AttentionRecord)
        .where(AttentionRecord.test_session_id == test_session_id)
        .order_by(AttentionRecord.row_index, AttentionRecord.col_index)
    )

    return session.exec(query).all()


def get_test_session_results(session: Session, test_session_id: int) -> Dict[str, Any]:
    """获取单次测试会话的结果"""
    # 获取测试会话
    test_session = session.get(AttentionTestSession, test_session_id)
    if not test_session:
        return None

    # 获取用户
    user = session.get(User, test_session.user_id) if test_session.user_id else None

    # 获取所有记录
    records = get_test_session_records(session, test_session_id)

    # 构建结果
    results = {
        "user": user,
        "session": test_session,
        "records": records,
        "stats": {
            "correctCount": test_session.correct_count,
            "incorrectCount": test_session.incorrect_count,
            "missedCount": test_session.missed_count,
            "totalScore": test_session.total_score,
            "accuracy": test_session.accuracy,
            "totalTimeSeconds": test_session.total_time_seconds,
        },
    }

    return results
