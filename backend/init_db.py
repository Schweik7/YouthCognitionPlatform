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
from apps.calculation_test.models import (
    CalculationTestSession,
    CalculationProblem,
)  # 新增计算流畅性测试模型


def main():
    """主函数"""
    logger.info("开始初始化数据库...")
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
