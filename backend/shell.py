#!/usr/bin/env python3
"""
交互式调试脚本，类似于 Flask Shell
使用: python shell.py
"""

import os
import sys
from sqlmodel import Session, select
from datetime import datetime, timedelta
import IPython

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入项目模块
from database import engine
from config import settings
from apps.users.models import User
from apps.reading_fluency.models import TestSession, Trial

# 创建会话
session = Session(engine)


def get_recent_schools_debug():
    """调试获取最近学校列表的函数"""
    try:
        # 尝试1: 使用distinct()查询
        print("尝试1: 使用distinct()查询")
        query1 = select(User.school).distinct()
        print(f"SQL查询: {query1}")

        try:
            schools1 = [school for (school,) in session.exec(query1)]
            print(f"结果: {schools1}")
        except Exception as e1:
            print(f"错误1: {str(e1)}")

        # 尝试2: 使用group_by()查询
        print("\n尝试2: 使用group_by()查询")
        query2 = select(User.school).group_by(User.school)
        print(f"SQL查询: {query2}")

        try:
            schools2 = [school for (school,) in session.exec(query2)]
            print(f"结果: {schools2}")
        except Exception as e2:
            print(f"错误2: {str(e2)}")

        # 尝试3: 使用原始SQL查询
        print("\n尝试3: 使用原始SQL查询")
        try:
            from sqlalchemy import text

            raw_query = "SELECT DISTINCT school FROM users"
            result = session.exec(text(raw_query))
            schools3 = [row[0] for row in result]
            print(f"结果: {schools3}")
        except Exception as e3:
            print(f"错误3: {str(e3)}")

        # 尝试4: 查询所有记录并在Python中去重
        print("\n尝试4: 查询所有记录并在Python中去重")
        query4 = select(User.school)
        print(f"SQL查询: {query4}")

        try:
            all_schools = [school for (school,) in session.exec(query4)]
            unique_schools = list(set(all_schools))
            print(f"结果: {unique_schools}")
        except Exception as e4:
            print(f"错误4: {str(e4)}")

    except Exception as e:
        print(f"整体错误: {str(e)}")


# 打印帮助信息
print("=" * 50)
print("交互式调试环境已加载")
print("=" * 50)
print("可用对象:")
print("- session: 数据库会话")
print("- User: 用户模型")
print("- TestSession: 测试会话模型")
print("- Trial: 试验记录模型")
print("- select(): SQLModel 查询函数")
print("\n可用函数:")
print("- get_recent_schools_debug(): 调试获取最近学校列表")
print("=" * 50)
print("\n示例:")
print("1. 调试获取学校列表:\n   get_recent_schools_debug()")
print("2. 查询所有用户:\n   users = session.exec(select(User)).all()")
print("3. 查看第一个用户:\n   first_user = session.exec(select(User)).first()")
print("=" * 50)

# 启动交互式 Shell
if __name__ == "__main__":
    IPython.embed()
