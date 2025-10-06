"""
瑞文测验CRT-CC_20计分规则实现
基于CRT_CC_20.m和CRT_CC_20_norm.csv
"""
import csv
from pathlib import Path
from typing import Tuple, Optional
from config import settings

# 常模数据路径
NORM_DATA_PATH = Path(settings.DATA_DIR) / "CRT_CC_20_norm.csv"

# 缓存常模数据
_norm_data = None


def load_norm_data():
    """加载常模数据"""
    global _norm_data

    if _norm_data is not None:
        return _norm_data

    _norm_data = []
    with open(NORM_DATA_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        for row in reader:
            # 将'/'转换为None，其他转换为浮点数
            processed_row = []
            for val in row:
                if val == '/' or val == '':
                    processed_row.append(None)
                else:
                    try:
                        processed_row.append(float(val))
                    except ValueError:
                        processed_row.append(val)
            _norm_data.append(processed_row)

    return _norm_data


def calculate_score(age: float, raw_score: int) -> Tuple[Optional[float], Optional[float], Optional[int]]:
    """
    根据年龄和原始分数计算百分位、Z分数和IQ

    Args:
        age: 年龄（岁），可以是小数
        raw_score: 原始分数（0-72）

    Returns:
        (percentile, z_score, iq) 元组
        - percentile: 百分位
        - z_score: Z分数
        - iq: 智商

    计分规则说明（基于CRT_CC_20.m）：
    1. 根据年龄找到对应的年龄类别列（整年查找，如满7岁未满8岁查7.5岁组）
    2. 在该列中找到原始分数对应的分数类别行
    3. 从该行的第1列读取百分位P，第14列读取Z分数，第15列读取IQ
    """
    norm = load_norm_data()

    # 第一行是列标题：P, 5.5, 6.5, 7.5, ..., 16.5, Z, IQ
    # 找到年龄对应的列索引
    # 根据MATLAB代码逻辑：使用整年查找
    # 如age=7.3，应该查7.5岁组（>=7且<8）
    # 常模表中：5.5, 6.5, 7.5, ..., 16.5
    # 对应年龄范围：[5,6), [6,7), [7,8), ..., [16,17)

    # 年龄列从索引1开始（索引0是P列）
    age_col = None
    for j in range(1, len(norm[0]) - 2):  # 减去最后的Z和IQ列
        try:
            age_category = float(norm[0][j])
            # 检查age是否在 [age_category-0.5, age_category+0.5) 范围内
            if age >= (age_category - 0.5) and age < (age_category + 0.5):
                age_col = j
                break
        except (ValueError, TypeError):
            continue

    if age_col is None:
        # 年龄超出范围（小于5或大于等于17）
        return None, None, None

    # 在年龄列中找到原始分数对应的行
    # 从第4行开始（索引3），因为前3行是特殊百分位值
    # 查找逻辑：找到第一个分数值 >= raw_score的行
    score_row = None

    # 先处理边界情况
    # 检查是否所有可用行的分数都小于raw_score（超高分情况）
    all_less = True
    for k in range(3, len(norm) - 2):  # 从第4行到倒数第3行
        cell_value = norm[k][age_col]
        if cell_value is not None and cell_value >= raw_score:
            all_less = False
            break

    if all_less:
        # 所有分数都小于raw_score，使用最高分行（第3行，索引2）
        score_row = 2
    else:
        # 检查是否所有可用行的分数都大于raw_score（超低分情况）
        all_greater = True
        for k in range(3, len(norm) - 2):
            cell_value = norm[k][age_col]
            if cell_value is not None and cell_value <= raw_score:
                all_greater = False
                break

        if all_greater:
            # 所有分数都大于raw_score，使用最低分行（倒数第3行）
            score_row = len(norm) - 3
        else:
            # 正常情况：找到分数范围
            # 根据MATLAB代码逻辑：
            # 找到第一个 score >= norm[k][age_col] 的k作为upper
            # 然后找到最后一个 score == norm[k][age_col] 的k+1作为lower
            # 取floor(0.5*(upper+lower))作为最终行

            upper = None
            for k in range(3, len(norm) - 2):
                cell_value = norm[k][age_col]
                if cell_value is not None and raw_score >= cell_value:
                    upper = k
                    break

            if upper is None:
                upper = 3  # 默认第一个有效行

            # 找lower
            lower = upper
            for k in range(upper, len(norm) - 2):
                cell_value = norm[k][age_col]
                if cell_value is not None and raw_score == cell_value:
                    lower = k + 1
                else:
                    break

            # 计算中间行
            score_row = int(0.5 * (upper + lower))

    # 从对应行读取百分位、Z分数和IQ
    # 第1列（索引0）是百分位P
    # 倒数第2列是Z分数
    # 倒数第1列是IQ
    percentile = norm[score_row][0]
    z_score = norm[score_row][-2]
    iq = norm[score_row][-1]

    # 转换IQ为整数
    if iq is not None:
        iq = int(iq)

    return percentile, z_score, iq
