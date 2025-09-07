#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
瑞文智力测验图片爬取脚本
使用Playwright自动化获取题目和选项图片
"""

import asyncio
import aiohttp
import os
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright

class RavenImageScraper:
    def __init__(self, base_dir="backend/data/raven_test"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # 存储每题的图片信息
        self.current_question = 1
        self.question_images = []  # 当前题目收集到的图片URL
        
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
    
    def normalize_filename(self, url, question_num, is_main=False, option_num=None):
        """规范化文件名"""
        # 解析URL获取文件扩展名
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        
        # 提取扩展名
        ext = os.path.splitext(filename)[1]
        if not ext:
            ext = '.jpg'  # 默认扩展名
        
        # 生成规范化的文件名
        if is_main:
            return f"question_{question_num:02d}_main{ext}"
        else:
            return f"question_{question_num:02d}_option_{option_num}{ext}"
    
    async def handle_network_request(self, request):
        """处理网络请求，捕获图片URL"""
        url = request.url
        
        # 检查是否是图片请求
        if any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
            print(f"🖼️  发现图片URL: {url}")
            
            # 添加到当前题目的图片列表
            self.question_images.append(url)
    
    async def get_image_src_from_page(self, page):
        """从页面DOM中直接获取图片src"""
        try:
            # 获取所有img元素的src属性
            img_srcs = await page.evaluate("""
                () => {
                    const imgs = document.querySelectorAll('img');
                    return Array.from(imgs).map(img => img.src).filter(src => src && src.length > 0);
                }
            """)
            return img_srcs
        except Exception as e:
            print(f"  获取图片src失败: {e}")
            return []

    async def process_question(self, page, question_num):
        """处理单个题目"""
        print(f"\n📝 处理第 {question_num} 题...")
        self.current_question = question_num
        self.question_images.clear()
        
        # 等待页面加载完成
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(3)  # 等待图片加载
        
        # 从页面DOM中获取图片URL
        page_images = await self.get_image_src_from_page(page)
        
        # 过滤出题目相关的图片（通常包含特定路径）
        question_images = [img for img in page_images if any(keyword in img.lower() for keyword in ['iq', 'test', 'question', 'raven']) or img.startswith('data:')]
        
        # 如果没有找到特定图片，使用所有图片
        if not question_images:
            question_images = [img for img in page_images if not any(skip in img.lower() for skip in ['icon', 'logo', 'avatar', 'banner'])]
        
        print(f"  发现 {len(question_images)} 张题目相关图片")
        
        if len(question_images) >= 7:  # 预期有7张图片（1题目+6选项）
            # 下载图片
            async with aiohttp.ClientSession() as session:
                # 下载主题图片（第一张通常是题目）
                main_image_url = question_images[0]
                main_filename = self.normalize_filename(main_image_url, question_num, is_main=True)
                main_path = self.base_dir / main_filename
                await self.download_image(session, main_image_url, main_path)
                
                # 下载选项图片（接下来的6张）
                for i, option_url in enumerate(question_images[1:7], 1):
                    option_filename = self.normalize_filename(option_url, question_num, option_num=i)
                    option_path = self.base_dir / option_filename
                    await self.download_image(session, option_url, option_path)
        
        else:
            print(f"  ⚠️  图片数量不足，期望7张，实际{len(question_images)}张")
            # 仍然尝试下载可用的图片
            async with aiohttp.ClientSession() as session:
                for i, img_url in enumerate(question_images):
                    filename = f"question_{question_num:02d}_img_{i+1:02d}.jpg"
                    filepath = self.base_dir / filename
                    await self.download_image(session, img_url, filepath)
    
    async def click_next_question(self, page):
        """点击选项进入下一题"""
        try:
            # 基于Browser MCP的观察，选项图片在页面中的特定位置
            # 尝试找到选项图片并点击第一个
            
            # 方法1：通过JavaScript获取所有图片并点击第二个（第一个是题目图片）
            clicked = await page.evaluate("""
                () => {
                    const imgs = document.querySelectorAll('img');
                    const validImgs = Array.from(imgs).filter(img => 
                        img.src && 
                        !img.src.includes('icon') && 
                        !img.src.includes('logo') &&
                        img.offsetWidth > 30 && 
                        img.offsetHeight > 30
                    );
                    
                    if (validImgs.length >= 7) {
                        // 点击第二张图片（第一张是题目图片，第二张是第一个选项）
                        validImgs[1].click();
                        return true;
                    }
                    return false;
                }
            """)
            
            if clicked:
                print("  ✓ 点击选项成功")
            else:
                # 方法2：尝试点击任意可点击的图片
                images = await page.query_selector_all('img')
                if len(images) >= 2:
                    # 点击第二张图片（假设第一张是题目图片）
                    await images[1].click()
                    print("  ✓ 点击图片选项")
                else:
                    print("  ⚠️  未找到足够的图片选项")
            
            # 等待页面跳转
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"  ✗ 点击选项失败: {str(e)}")
    
    async def scrape_all_questions(self, url="https://minke8.cn/iq1.html", max_questions=72):
        """爬取所有题目"""
        print(f"🚀 开始爬取瑞文智力测验图片...")
        print(f"目标URL: {url}")
        print(f"保存路径: {self.base_dir}")
        print(f"预计题目数: {max_questions}")
        
        async with async_playwright() as p:
            # 启动浏览器
            browser = await p.chromium.launch(
                headless=False,  # 显示浏览器窗口
                args=[
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            try:
                context = await browser.new_context(
                    viewport={'width': 1280, 'height': 720},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                )
                
                page = await context.new_page()
                
                # 设置网络监听
                page.on('request', self.handle_network_request)
                
                # 访问首页
                print(f"\n🌐 访问: {url}")
                await page.goto(url, wait_until='networkidle')
                
                # 点击"开始测试"按钮
                try:
                    start_button = await page.query_selector('text=开始测试')
                    if start_button:
                        await start_button.click()
                        print("✓ 点击开始测试按钮")
                        await page.wait_for_load_state('networkidle')
                        await asyncio.sleep(2)
                    else:
                        print("⚠️  未找到开始测试按钮")
                except Exception as e:
                    print(f"点击开始测试按钮失败: {e}")
                
                # 处理每个题目
                for question_num in range(1, max_questions + 1):
                    try:
                        await self.process_question(page, question_num)
                        
                        if question_num < max_questions:
                            await self.click_next_question(page)
                            
                    except Exception as e:
                        print(f"  ✗ 处理第{question_num}题时出错: {str(e)}")
                        # 尝试继续下一题
                        try:
                            await self.click_next_question(page)
                        except:
                            pass
                        continue
                
                print(f"\n🎉 爬取完成！共处理 {max_questions} 题")
                
            finally:
                await browser.close()


async def main():
    """主函数"""
    scraper = RavenImageScraper()
    await scraper.scrape_all_questions()


if __name__ == "__main__":
    asyncio.run(main())