#!/usr/bin/env python3
"""
添加 problem_type 列到 calc_problems 表的迁移脚本
"""

import mysql.connector
from mysql.connector import Error
import os
import sys

# 添加父目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings

def run_migration():
    """运行数据库迁移"""
    connection = None
    try:
        # 连接数据库
        connection = mysql.connector.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME
        )
        
        cursor = connection.cursor()
        
        print("开始执行迁移：添加 problem_type 列")
        
        # 检查列是否已存在
        check_column_sql = """
        SELECT COUNT(*) 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = %s 
        AND TABLE_NAME = 'calc_problems' 
        AND COLUMN_NAME = 'problem_type'
        """
        
        cursor.execute(check_column_sql, (settings.DB_NAME,))
        column_exists = cursor.fetchone()[0]
        
        if column_exists > 0:
            print("列 problem_type 已存在，跳过迁移")
            return
        
        # 添加 problem_type 列
        add_column_sql = """
        ALTER TABLE calc_problems 
        ADD COLUMN problem_type VARCHAR(50) NULL 
        AFTER problem_text
        """
        
        cursor.execute(add_column_sql)
        
        # 添加索引
        add_index_sql = """
        CREATE INDEX idx_calc_problems_type 
        ON calc_problems(problem_type)
        """
        
        cursor.execute(add_index_sql)
        
        # 提交更改
        connection.commit()
        
        print("迁移完成：已添加 problem_type 列和索引")
        
    except Error as e:
        print(f"数据库错误: {e}")
        if connection:
            connection.rollback()
        raise
    except Exception as e:
        print(f"迁移失败: {e}")
        if connection:
            connection.rollback()
        raise
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    run_migration()