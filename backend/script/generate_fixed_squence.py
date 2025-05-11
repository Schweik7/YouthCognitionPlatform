#!/usr/bin/env python3
"""
生成注意力测试的固定符号序列
为每个符号创建目标位置列表
"""

import os
import json
import random
from pathlib import Path
import argparse

# 配置
SYMBOLS = ["Π", "Θ", "Ψ", "≅", "⊕", "א", "Ϡ", "ʆ", "Ԅ", "Φ"]
ROWS = 17  # 1行训练 + 16行测试
COLS = 25
PRACTICE_ROW = 0

# 目标符号在每行中的数量
TARGETS_PER_PRACTICE_ROW = 4  # 练习行中的目标符号数
TARGETS_PER_FORMAL_ROW = 3  # 正式行中的目标符号数


def generate_target_positions():
    """为每个可能的目标符号生成位置列表"""
    # 创建每个符号的目标位置字典
    target_positions = {symbol: [] for symbol in SYMBOLS}

    # 为每个符号生成目标位置
    for symbol in SYMBOLS:
        # 生成练习行的目标位置 (第0行)
        practice_positions = generate_positions_for_row(PRACTICE_ROW, TARGETS_PER_PRACTICE_ROW)
        target_positions[symbol].extend(practice_positions)

        # 生成测试行的目标位置
        for row in range(1, ROWS):
            formal_positions = generate_positions_for_row(row, TARGETS_PER_FORMAL_ROW)
            target_positions[symbol].extend(formal_positions)

    return target_positions


def generate_positions_for_row(row, target_count):
    """为特定行生成目标位置"""
    # 随机选择列位置
    columns = random.sample(range(COLS), target_count)
    # 返回位置元组列表 [(row, col), ...]
    return [(row, col) for col in columns]


def generate_sequence_json(output_file=None):
    """生成固定的符号序列位置并保存为JSON"""
    # 为每个符号生成目标位置
    target_positions = generate_target_positions()

    # 计算每个符号的目标位置数量
    target_counts = {symbol: len(positions) for symbol, positions in target_positions.items()}

    # 创建元数据
    metadata = {
        "symbols": SYMBOLS,
        "rows": ROWS,
        "cols": COLS,
        "practice_row": PRACTICE_ROW,
        "target_counts": target_counts,
        "targets_per_practice_row": TARGETS_PER_PRACTICE_ROW,
        "targets_per_formal_row": TARGETS_PER_FORMAL_ROW,
    }

    # 创建最终结果
    result = {"target_positions": target_positions, "metadata": metadata}

    # 保存为JSON文件
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"符号序列已保存至 {output_file}")

    return result


def analyze_target_positions(target_positions):
    """分析目标位置数据"""
    print("目标位置分析:")

    for symbol, positions in target_positions.items():
        # 计算练习行和正式行的目标位置数量
        practice_count = sum(1 for pos in positions if pos[0] == PRACTICE_ROW)
        formal_count = sum(1 for pos in positions if pos[0] > PRACTICE_ROW)

        print(f"符号 {symbol}: 总共 {len(positions)} 个目标位置")
        print(f"  - 练习行: {practice_count} 个")
        print(f"  - 正式行: {formal_count} 个")

        # 分析每行的目标数
        row_counts = {}
        for row, _ in positions:
            row_counts[row] = row_counts.get(row, 0) + 1

        print("  - 行分布:")
        for row in sorted(row_counts.keys()):
            row_type = "练习" if row == PRACTICE_ROW else "测试"
            print(f"    第 {row + 1} 行 ({row_type}): {row_counts[row]} 个目标")

        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成注意力测试的符号目标位置")
    parser.add_argument(
        "-o", "--output", default="./data/attention_targets.json", help="输出文件路径"
    )
    args = parser.parse_args()

    # 确保输出目录存在
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    # 生成序列
    result = generate_sequence_json(args.output)

    # 分析目标位置
    analyze_target_positions(result["target_positions"])

    print(f"\n目标位置数据已保存至 {args.output}")
