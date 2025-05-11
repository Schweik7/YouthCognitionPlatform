"""
数据库初始化和数据迁移脚本
"""

import os
import shutil
from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session
import pandas as pd
from logger_config import logger

from config import settings
from database import create_db_and_tables
from apps.users.models import User
from apps.reading_fluency.models import Trial, TestSession
from apps.attention_test.models import AttentionTestSession, AttentionRecord

# 确保数据目录存在
data_dir = Path(settings.DATA_DIR)
data_dir.mkdir(exist_ok=True)


# 检查并复制CSV文件
def ensure_csv_files():
    """确保CSV数据文件存在"""
    # 复制教学阶段CSV
    practice_src = Path("server/教学阶段.csv")
    practice_dst = data_dir / "教学阶段.csv"

    # 复制正式阶段CSV
    formal_src = Path("server/正式阶段.csv")
    formal_dst = data_dir / "正式阶段.csv"

    # 检查源文件是否存在
    if practice_src.exists() and not practice_dst.exists():
        logger.info(f"复制教学阶段CSV: {practice_src} -> {practice_dst}")
        shutil.copy2(practice_src, practice_dst)
    else:
        if not practice_dst.exists():
            logger.warning(f"未找到教学阶段CSV文件 {practice_src}")
            # 创建示例教学阶段CSV
            example_data = [
                ["1", "太阳从西边升起。（      ）"],
                ["2", "燕子会飞。（       ）"],
                ["3", "写字要用手。（       ）"],
            ]
            pd.DataFrame(example_data).to_csv(practice_dst, header=False, index=False)
            logger.info(f"已创建示例教学阶段CSV: {practice_dst}")

    if formal_src.exists() and not formal_dst.exists():
        logger.info(f"复制正式阶段CSV: {formal_src} -> {formal_dst}")
        shutil.copy2(formal_src, formal_dst)
    else:
        if not formal_dst.exists():
            logger.warning(f"未找到正式阶段CSV文件 {formal_src}")
            # 创建示例正式阶段CSV
            example_data = [
                ["1", "天安门在北京。（       ）"],
                ["2", "老虎喜欢吃青草。（        ）"],
                ["3", "蚂蚁比大象小很多。（        ）"],
                ["4", "汽车比火车长很多。（       ）"],
                ["5", "猫是捉老鼠的能手。（        ）"],
            ]
            pd.DataFrame(example_data).to_csv(formal_dst, header=False, index=False)
            logger.info(f"已创建示例正式阶段CSV: {formal_dst}")


def main():
    """主函数"""
    logger.info("开始初始化数据库...")

    # 确保CSV文件存在
    ensure_csv_files()

    # 创建数据库表
    create_db_and_tables()
    logger.info("数据库表创建完成")

    # 打印表信息
    metadata = SQLModel.metadata
    logger.info(f"已创建以下表:")
    for table_name in metadata.tables.keys():
        logger.info(f" - {table_name}")

    logger.info("数据库初始化完成")


if __name__ == "__main__":
    main()
