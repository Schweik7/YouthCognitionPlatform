import os
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

# 缓存数据
_symbol_set = None

# 行列配置
SYMBOLS_PER_ROW = 25  # 每行符号数
TOTAL_ROWS = 16      # 总行数
PRACTICE_ROWS = 1    # 练习阶段行数

def load_symbol_set() -> List[str]:
    """从文件加载字符集"""
    global _symbol_set
    
    if _symbol_set:
        return _symbol_set
        
    if not symbol_set_path.exists():
        logger.warning(f"字符集文件不存在 {symbol_set_path}")
        return ["Π", "Θ", "Ψ", "≅", "⊕", "א", "Ϡ", "ʆ", "Ԅ", "Φ"]  # 默认字符集

    try:
        with open(symbol_set_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            _symbol_set = list(content)
            
        logger.info(f"成功加载 {len(_symbol_set)} 个字符")
        return _symbol_set
    except Exception as e:
        logger.error(f"加载字符集失败: {str(e)}")
        return ["Π", "Θ", "Ψ", "≅", "⊕", "א", "Ϡ", "ʆ", "Ԅ", "Φ"]  # 默认字符集


def generate_symbol_row(row_index: int, target_symbol: str, is_practice: bool = False) -> List[Dict[str, Any]]:
    """生成一行符号"""
    symbols = load_symbol_set()
    
    # 生成随机符号序列
    row_symbols = []
    
    # 确定目标符号的数量
    if is_practice:
        # 练习阶段，放置3-5个目标符号
        target_count = random.randint(3, 5)
    else:
        # 正式阶段，放置2-4个目标符号
        target_count = random.randint(2, 4)
    
    # 随机选择目标符号的位置
    target_positions = random.sample(range(SYMBOLS_PER_ROW), target_count)
    
    # 生成序列
    for col_index in range(SYMBOLS_PER_ROW):
        is_target = col_index in target_positions
        if is_target:
            symbol = target_symbol
        else:
            # 从非目标符号中随机选择
            available_symbols = [s for s in symbols if s != target_symbol]
            symbol = random.choice(available_symbols)
        
        row_symbols.append({
            "row_index": row_index,
            "col_index": col_index,
            "symbol": symbol,
            "is_target": is_target,
            "is_clicked": False
        })
    
    return row_symbols


def generate_practice_sequence(target_symbol: str) -> List[Dict[str, Any]]:
    """生成练习阶段序列"""
    sequence = []
    
    for row_index in range(PRACTICE_ROWS):
        row_symbols = generate_symbol_row(row_index, target_symbol, is_practice=True)
        sequence.extend(row_symbols)
    
    return sequence


def generate_test_sequence(target_symbol: str) -> List[Dict[str, Any]]:
    """生成测试阶段序列"""
    sequence = []
    
    for row_index in range(TOTAL_ROWS):
        row_symbols = generate_symbol_row(row_index, target_symbol, is_practice=False)
        sequence.extend(row_symbols)
    
    return sequence


def create_test_session(session: Session, test_session_data: AttentionSessionCreate) -> AttentionTestSession:
    """创建新的注意力测试会话"""
    # 检查用户是否存在
    user = session.get(User, test_session_data.user_id)
    if not user:
        raise ValueError(f"用户不存在: ID={test_session_data.user_id}")

    # 创建测试会话
    test_session = AttentionTestSession(
        user_id=test_session_data.user_id,
        target_symbol=test_session_data.target_symbol,
        start_time=datetime.now(),
    )

    session.add(test_session)
    session.commit()
    session.refresh(test_session)

    logger.info(f"为用户 {user.name} 创建注意力测试会话，ID: {test_session.id}")
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


def complete_test_session(session: Session, test_session_id: int) -> Optional[AttentionTestSession]:
    """完成测试会话并计算结果"""
    test_session = session.get(AttentionTestSession, test_session_id)
    if not test_session:
        return None

    # 查询所有记录
    records_query = select(AttentionRecord).where(AttentionRecord.test_session_id == test_session_id)
    records = session.exec(records_query).all()
    
    # 统计结果
    correct_count = 0  # 正确点击
    incorrect_count = 0  # 错误点击
    missed_count = 0  # 遗漏
    
    for record in records:
        if record.is_target and record.is_clicked:
            correct_count += 1
        elif record.is_target and not record.is_clicked:
            missed_count += 1
        elif not record.is_target and record.is_clicked:
            incorrect_count += 1
    
    # 计算总分
    total_score = correct_count - incorrect_count - (0.5 * missed_count)
    
    # 更新测试会话
    test_session.is_completed = True
    test_session.end_time = datetime.now()
    test_session.correct_count = correct_count
    test_session.incorrect_count = incorrect_count
    test_session.missed_count = missed_count
    test_session.total_score = total_score
    
    # 计算总用时（秒）
    delta = test_session.end_time - test_session.start_time
    test_session.total_time_seconds = int(delta.total_seconds())

    session.add(test_session)
    session.commit()
    session.refresh(test_session)

    logger.info(f"完成测试会话 {test_session_id}, 得分: {total_score}")
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
    is_correct = (record_data.is_target and record_data.is_clicked) or (not record_data.is_target and not record_data.is_clicked)
    
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
        response_time=record_data.response_time
    )
    
    session.add(record)
    session.commit()
    session.refresh(record)
    
    return record


def save_row_records(
    session: Session, test_session_id: int, user_id: int, row_data: List[Dict[str, Any]]
) -> List[AttentionRecord]:
    """保存一行符号的所有记录"""
    records = []
    
    for symbol_data in row_data:
        record_data = AttentionRecordCreate(
            user_id=user_id,
            test_session_id=test_session_id,
            row_index=symbol_data["row_index"],
            col_index=symbol_data["col_index"],
            symbol=symbol_data["symbol"],
            is_target=symbol_data["is_target"],
            is_clicked=symbol_data["is_clicked"],
            response_time=symbol_data.get("response_time")
        )
        
        record = save_attention_record(session, record_data)
        records.append(record)
    
    return records


def get_test_session_records(session: Session, test_session_id: int) -> List[AttentionRecord]:
    """获取测试会话中的所有记录"""
    query = select(AttentionRecord).where(
        AttentionRecord.test_session_id == test_session_id
    ).order_by(AttentionRecord.row_index, AttentionRecord.col_index)
    
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