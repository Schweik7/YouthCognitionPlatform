"""
日志记录模块 - 将控制台输出同时重定向到日志文件
"""

import sys
import os
import time
from datetime import datetime
from pathlib import Path
from typing import TextIO, Optional

# 日志目录
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


class Logger:
    """
    日志记录器 - 同时将输出发送到控制台和日志文件
    """
    def __init__(self, filename: str = None):
        # 如果没有提供文件名，使用当前时间创建一个
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"app_{timestamp}.log"
        
        # 确保日志目录存在
        self.log_file_path = LOG_DIR / filename
        
        # 打开日志文件
        self.log_file = open(self.log_file_path, "a", encoding="utf-8")
        
        # 保存原始的stdout和stderr
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        
        # 重定向stdout和stderr
        sys.stdout = self
        sys.stderr = self
        
        self.log(f"===== 日志开始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} =====")
    
    def write(self, message: str):
        """写入消息到控制台和日志文件"""
        # 写入到原始stdout
        self.stdout.write(message)
        self.stdout.flush()
        
        # 写入到日志文件
        self.log_file.write(message)
        self.log_file.flush()
    
    def flush(self):
        """刷新输出缓冲区"""
        self.stdout.flush()
        self.log_file.flush()
    
    def log(self, message: str, level: str = "INFO"):
        """记录带有时间戳和级别的日志消息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}\n"
        
        # 写入到日志文件
        self.log_file.write(log_line)
        self.log_file.flush()
        
        # 写入到原始stdout
        self.stdout.write(log_line)
        self.stdout.flush()
    
    def close(self):
        """关闭日志记录器"""
        self.log(f"===== 日志结束: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} =====")
        
        # 恢复原始的stdout和stderr
        sys.stdout = self.stdout
        sys.stderr = self.stderr
        
        # 关闭日志文件
        if self.log_file and not self.log_file.closed:
            self.log_file.close()
    
    def __del__(self):
        """析构函数，确保日志文件被关闭"""
        self.close()


# 全局日志记录器实例
_logger = None

def init_logger(filename: str = None) -> Logger:
    """初始化全局日志记录器"""
    global _logger
    if _logger is None:
        _logger = Logger(filename)
    return _logger

def get_logger() -> Logger:
    """获取全局日志记录器"""
    global _logger
    if _logger is None:
        _logger = init_logger()
    return _logger

def log(message: str, level: str = "INFO"):
    """使用全局日志记录器记录消息"""
    logger = get_logger()
    logger.log(message, level)

def close_logger():
    """关闭全局日志记录器"""
    global _logger
    if _logger is not None:
        _logger.close()
        _logger = None