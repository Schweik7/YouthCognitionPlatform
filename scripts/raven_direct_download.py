#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
瑞文智力测验图片直接下载脚本
根据发现的URL规律直接下载所有题目和选项图片
"""

import asyncio
import aiohttp
import os
from pathlib import Path

class RavenDirectDownloader:
    def __init__(self, base_dir="backend/data/raven_test"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # URL模式
        self.question_url_template = "https://minke8.cn/Assets/images/rw/question/{}.jpg"
        self.answer_url_template = "https://minke8.cn/Assets/images/rw/answer/{}.jpg"
        
    async def download_image(self, session, url, filepath):
        """下载单个图片"""
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    with open(filepath, 'wb') as f:
                        f.write(content)
                    print(f"✓ 下载成功: {filepath}")
                    return True
                else:
                    print(f"✗ 下载失败: {url} (状态码: {response.status})")
                    return False
        except Exception as e:
            print(f"✗ 下载异常: {url} - {str(e)}")
            return False
    
    async def download_question_images(self, session, question_num):
        """下载单个题目的所有图片（1个题目图片 + 6个选项图片）"""
        print(f"\n📝 下载第 {question_num} 题的图片...")
        
        success_count = 0
        
        # 下载题目图片
        question_url = self.question_url_template.format(question_num)
        question_filename = f"question_{question_num:02d}_main.jpg"
        question_path = self.base_dir / question_filename
        
        if await self.download_image(session, question_url, question_path):
            success_count += 1
        
        # 计算该题选项的起始编号
        # 根据观察：第1题选项是1-6，第2题选项是7-12，第3题选项是13-18...
        # 公式：起始编号 = (question_num - 1) * 6 + 1
        start_answer_num = (question_num - 1) * 6 + 1
        
        # 下载6个选项图片
        for option_index in range(6):
            answer_num = start_answer_num + option_index
            answer_url = self.answer_url_template.format(answer_num)
            answer_filename = f"question_{question_num:02d}_option_{option_index + 1}.jpg"
            answer_path = self.base_dir / answer_filename
            
            if await self.download_image(session, answer_url, answer_path):
                success_count += 1
        
        print(f"  题目 {question_num}: {success_count}/7 张图片下载成功")
        return success_count
    
    async def download_all_questions(self, max_questions=72):
        """下载所有题目的图片"""
        print(f"🚀 开始下载瑞文智力测验图片...")
        print(f"目标题目数: {max_questions}")
        print(f"保存路径: {self.base_dir}")
        print(f"预计总图片数: {max_questions * 7} 张")
        
        total_success = 0
        total_images = max_questions * 7
        
        # 创建HTTP会话
        async with aiohttp.ClientSession() as session:
            # 并发下载（每次处理5题以避免过多并发）
            batch_size = 5
            
            for batch_start in range(1, max_questions + 1, batch_size):
                batch_end = min(batch_start + batch_size, max_questions + 1)
                batch_questions = range(batch_start, batch_end)
                
                print(f"\n📦 批次处理: 题目 {batch_start}-{batch_end-1}")
                
                # 并发下载当前批次的题目
                tasks = [
                    self.download_question_images(session, q) 
                    for q in batch_questions
                ]
                
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 统计成功下载的图片数
                for result in batch_results:
                    if isinstance(result, int):
                        total_success += result
                    else:
                        print(f"  ⚠️  批次处理出错: {result}")
                
                # 短暂暂停避免过于频繁的请求
                await asyncio.sleep(1)
        
        print(f"\n🎉 下载完成！")
        print(f"📊 成功下载: {total_success}/{total_images} 张图片")
        print(f"📁 图片保存在: {self.base_dir}")
        
        # 生成下载报告
        await self.generate_download_report(max_questions, total_success, total_images)
    
    async def generate_download_report(self, max_questions, success_count, total_count):
        """生成下载报告"""
        report_path = self.base_dir / "download_report.txt"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("瑞文智力测验图片下载报告\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"下载时间: {asyncio.get_event_loop().time()}\n")
            f.write(f"题目数量: {max_questions}\n")
            f.write(f"预期图片总数: {total_count}\n")
            f.write(f"成功下载数: {success_count}\n")
            f.write(f"下载成功率: {success_count/total_count*100:.1f}%\n\n")
            
            f.write("文件命名规则:\n")
            f.write("- 题目图片: question_XX_main.jpg\n")
            f.write("- 选项图片: question_XX_option_Y.jpg\n")
            f.write("  其中 XX 是题目编号(01-72)，Y 是选项编号(1-6)\n\n")
            
            f.write("URL规律:\n")
            f.write("- 题目: https://minke8.cn/Assets/images/rw/question/{题目编号}.jpg\n")
            f.write("- 选项: https://minke8.cn/Assets/images/rw/answer/{选项编号}.jpg\n")
            f.write("  选项编号计算: (题目编号-1)*6 + 选项序号\n")
        
        print(f"📄 下载报告已保存: {report_path}")

    async def verify_downloads(self, max_questions=72):
        """验证下载的文件"""
        print(f"\n🔍 验证下载的文件...")
        
        missing_files = []
        
        for question_num in range(1, max_questions + 1):
            # 检查题目图片
            main_file = self.base_dir / f"question_{question_num:02d}_main.jpg"
            if not main_file.exists():
                missing_files.append(str(main_file))
            
            # 检查选项图片
            for option_num in range(1, 7):
                option_file = self.base_dir / f"question_{question_num:02d}_option_{option_num}.jpg"
                if not option_file.exists():
                    missing_files.append(str(option_file))
        
        if missing_files:
            print(f"⚠️  发现 {len(missing_files)} 个缺失文件:")
            for file in missing_files[:10]:  # 只显示前10个
                print(f"  - {file}")
            if len(missing_files) > 10:
                print(f"  ... 还有 {len(missing_files) - 10} 个文件")
        else:
            print("✅ 所有文件下载完整！")
        
        return len(missing_files) == 0


async def main():
    """主函数"""
    downloader = RavenDirectDownloader()
    
    # 下载所有图片
    await downloader.download_all_questions(max_questions=72)
    
    # 验证下载结果
    await downloader.verify_downloads(max_questions=72)


if __name__ == "__main__":
    asyncio.run(main())