"""
日志配置模块 - 使用 loguru 配置日志系统
"""

import sys
import os
from pathlib import Path
from loguru import logger

# 日志目录
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


def setup_logger():
    """配置 loguru 日志系统"""
    # 移除默认处理器
    logger.remove()
    
    # 添加标准输出处理器
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # 添加文件处理器
    log_file = LOG_DIR / f"app_{os.getpid()}.log"
    logger.add(
        log_file,
        rotation="20 MB",    # 当日志文件达到20MB时轮转
        compression="zip",   # 压缩轮转的日志文件
        retention="1 week",  # 保留1周的日志
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        encoding="utf-8"
    )
    
    return logger


# 设置并导出日志器
logger = setup_logger()