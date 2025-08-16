#!/usr/bin/env python3
"""
生成注意力测试的固定符号序列和目标位置数据
1. 生成一个25×17的符号矩阵并保存为txt文件
2. 为每个可能的目标符号生成位置列表保存为JSON文件
"""

import os
import json
import random
from pathlib import Path
import argparse

# 配置
SYMBOLS = ["Π", "Θ", "Ψ", "≅", "⊕", "א", "Ϡ", "ʆ", "Ԅ", "Φ"]
ROWS = 26  # 1行训练 + 25行测试
COLS = 40
PRACTICE_ROW = 0  # 练习行索引


def generate_symbol_matrix():
    """生成符号矩阵"""
    matrix = []

    for row in range(ROWS):
        row_symbols = []
        for col in range(COLS):
            # 随机选择一个符号
            symbol = random.choice(SYMBOLS)
            row_symbols.append(symbol)
        matrix.append(row_symbols)

    return matrix


def save_matrix_as_txt(matrix, output_file):
    """保存符号矩阵为txt文件"""
    with open(output_file, "w", encoding="utf-8") as f:
        for row in matrix:
            # 将每行符号无间隔连接为一个字符串
            line = "".join(row)
            f.write(line + "\n")


def find_target_positions(matrix, target_symbol):
    """在矩阵中查找目标符号的所有位置"""
    positions = []

    for row_idx, row in enumerate(matrix):
        for col_idx, symbol in enumerate(row):
            if symbol == target_symbol:
                positions.append((row_idx, col_idx))

    return positions


def generate_target_positions_json(matrix, output_file):
    """生成目标位置JSON文件"""
    # 为每个符号查找目标位置
    target_positions = {}

    for symbol in SYMBOLS:
        positions = find_target_positions(matrix, symbol)
        target_positions[symbol] = positions

    # 创建元数据
    metadata = {
        "symbols": SYMBOLS,
        "rows": ROWS,
        "cols": COLS,
        "practice_row": PRACTICE_ROW,
        "symbol_counts": {symbol: len(positions) for symbol, positions in target_positions.items()},
    }

    # 创建最终结果
    result = {"target_positions": target_positions, "metadata": metadata}

    # 保存为JSON文件
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result


def analyze_symbol_matrix(matrix):
    """分析符号矩阵的分布情况"""
    print("符号矩阵分析:")

    # 统计每种符号的数量
    symbol_counts = {symbol: 0 for symbol in SYMBOLS}

    for row in matrix:
        for symbol in row:
            symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1

    # 显示每种符号的数量和百分比
    total_symbols = ROWS * COLS
    print(f"总符号数: {total_symbols}")
    print("各符号分布:")

    for symbol, count in sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_symbols) * 100
        print(f"  {symbol}: {count} 个 ({percentage:.2f}%)")

    # 分析练习行
    practice_row = matrix[PRACTICE_ROW]
    practice_counts = {symbol: practice_row.count(symbol) for symbol in SYMBOLS}

    print("\n练习行符号分布:")
    for symbol, count in sorted(practice_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / COLS) * 100
        print(f"  {symbol}: {count} 个 ({percentage:.2f}%)")

    # 分析每个符号在每行的分布
    print("\n每行各符号分布:")
    for row_idx, row in enumerate(matrix):
        row_type = "练习" if row_idx == PRACTICE_ROW else "测试"
        print(f"第 {row_idx + 1} 行 ({row_type}):", end=" ")
        for symbol in SYMBOLS:
            count = row.count(symbol)
            if count > 0:
                print(f"{symbol}:{count}", end=" ")
        print()


def analyze_target_positions(target_positions):
    """分析目标位置数据"""
    print("\n目标位置分析:")

    for symbol, positions in target_positions.items():
        # 计算练习行和正式行的目标位置数量
        practice_count = sum(1 for pos in positions if pos[0] == PRACTICE_ROW)
        formal_count = sum(1 for pos in positions if pos[0] > PRACTICE_ROW)

        print(f"符号 {symbol}: 总共 {len(positions)} 个位置")
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
    parser = argparse.ArgumentParser(description="生成注意力测试的固定符号序列和目标位置数据")
    parser.add_argument("-d", "--data-dir", default="./data", help="数据目录路径")
    parser.add_argument(
        "-m", "--matrix-file", default="attention_matrix.txt", help="符号矩阵文件名"
    )
    parser.add_argument(
        "-t", "--targets-file", default="attention_targets.json", help="目标位置文件名"
    )
    args = parser.parse_args()

    # 确保输出目录存在
    data_dir = Path(args.data_dir)
    data_dir.mkdir(exist_ok=True)

    matrix_path = data_dir / args.matrix_file
    targets_path = data_dir / args.targets_file

    print(f"生成符号矩阵 ({ROWS}×{COLS})...")
    # 生成符号矩阵
    matrix = generate_symbol_matrix()

    # 保存矩阵为txt
    save_matrix_as_txt(matrix, matrix_path)
    print(f"符号矩阵已保存至 {matrix_path}")

    # 生成目标位置JSON
    result = generate_target_positions_json(matrix, targets_path)
    print(f"目标位置数据已保存至 {targets_path}")

    # 分析生成的数据
    analyze_symbol_matrix(matrix)
    analyze_target_positions(result["target_positions"])
