#!/usr/bin/env python3
"""
生成Cambria字体子集的Python脚本
包含注意力筛查字符集中的10个特殊符号
"""

import os
import sys
import subprocess
from pathlib import Path
import platform
import shutil
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# 根据操作系统确定Cambria字体的默认路径
def get_default_font_path():
    """获取不同操作系统下Cambria字体的默认路径"""
    system = platform.system()

    if system == "Windows":
        return r"C:\Windows\Fonts\cambria.ttc"
    elif system == "Darwin":  # macOS
        return "/Library/Fonts/Cambria.ttc"
    elif system == "Linux":
        # Linux上字体位置可能不同
        possible_paths = [
            "/usr/share/fonts/truetype/msttcorefonts/cambria.ttf",
            "/usr/share/fonts/TTF/cambria.ttf",
            "/usr/local/share/fonts/cambria.ttf",
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None
    return None


def create_font_subset(symbol_set_path, output_dir, font_path=None):
    """
    创建Cambria字体子集，只包含指定符号

    Args:
        symbol_set_path: 包含要保留符号的文件路径
        output_dir: 输出目录路径
        font_path: Cambria字体路径，如果为None则使用默认路径

    Returns:
        bool: 操作是否成功
    """
    try:
        # 确保输出目录存在
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 设置输出文件路径
        output_font_path = output_dir / "cambria-subset.woff2"
        css_output_path = output_dir / "symbols-font.css"

        # 如果未指定字体路径，使用默认路径
        if not font_path:
            font_path = get_default_font_path()
            if not font_path:
                logger.error("无法找到Cambria字体，请手动指定字体路径")
                return False

        # 检查字体文件是否存在
        if not os.path.exists(font_path):
            logger.error(f"字体文件不存在: {font_path}")
            return False

        # 检查符号集文件是否存在
        symbol_set_path = Path(symbol_set_path)
        if not symbol_set_path.exists():
            logger.error(f"符号集文件不存在: {symbol_set_path}")
            return False

        # 读取符号集
        with open(symbol_set_path, "r", encoding="utf-8") as f:
            symbols = f.read().strip()

        logger.info(f"读取到的符号集: {symbols}")

        # 检查fonttools是否安装
        try:
            import fontTools

            logger.info("找到fontTools库")
        except ImportError:
            logger.error("未找到fontTools库，尝试安装...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "fonttools", "brotli"])

        # 使用pyftsubset创建子集
        # pyftsubset命令格式: pyftsubset [字体文件] --output-file=[输出文件] --text=[字符集] --flavor=woff2
        from fontTools.subset import main as subset_main

        logger.info(f"开始创建字体子集从 {font_path}")

        # 构建pyftsubset的参数
        args = [
            str(font_path),
            f"--output-file={output_font_path}",
            f"--text={symbols}",
            "--flavor=woff2",
            # specify a font number between 0 and 1 (inclusive)
            "--font-number=0",
        ]

        # 调用pyftsubset
        subset_main(args)

        # 检查输出文件是否创建成功
        if not output_font_path.exists():
            logger.error(f"创建字体子集失败，输出文件不存在: {output_font_path}")
            return False

        logger.info(f"字体子集已生成: {output_font_path}")

        # 创建CSS文件
        css_content = f"""@font-face {{
  font-family: 'CambriaSymbols';
  src: url('/fonts/cambria-subset.woff2') format('woff2');
  font-weight: normal;
  font-style: normal;
  font-display: swap;
}}
"""

        with open(css_output_path, "w", encoding="utf-8") as f:
            f.write(css_content)

        logger.info(f"CSS文件已生成: {css_output_path}")

        return True

    except Exception as e:
        logger.error(f"生成字体子集时出错: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        return False


def main():
    """主函数"""
    import argparse

    # 解析命令行参数
    parser = argparse.ArgumentParser(description="生成Cambria字体子集")
    parser.add_argument("--font-path", help="指定Cambria字体文件路径")
    parser.add_argument("--symbol-set", help="指定符号集文件路径")
    parser.add_argument("--output-dir", help="指定输出目录")
    args = parser.parse_args()

    # 项目根目录
    project_dir = Path(__file__).parent.parent

    # 符号集文件路径
    symbol_set_path = (
        Path(args.symbol_set) if args.symbol_set else project_dir / "data" / "注意力筛查字符集.txt"
    )

    # 输出目录
    output_dir = (
        Path(args.output_dir) if args.output_dir else project_dir.parent / "public" / "fonts"
    )

    # 创建字体子集
    success = create_font_subset(symbol_set_path, output_dir, args.font_path)

    if success:
        logger.info("✅ 字体子集生成成功!")
    else:
        logger.error("❌ 字体子集生成失败!")
        sys.exit(1)


if __name__ == "__main__":
    main()
