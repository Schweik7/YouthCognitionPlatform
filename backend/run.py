"""
启动应用程序的脚本
"""

import os
import subprocess
import sys
from pathlib import Path

def main():
    print("启动认知能力评估平台...")
    
    # 检查是否已经初始化数据库
    if not Path("data").exists():
        print("首次运行，初始化数据库...")
        try:
            subprocess.run([sys.executable, "init_db.py"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"初始化数据库失败: {e}")
            return 1
    
    # 启动应用程序
    try:
        print("启动FastAPI服务器...")
        subprocess.run(["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000", "--reload"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"启动应用程序失败: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n应用程序已停止")
        return 0
    
    return 0

if __name__ == "__main__":
    sys.exit(main())