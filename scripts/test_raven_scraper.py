#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
瑞文智力测验图片爬取测试脚本
简化版本用于测试流程
"""

import asyncio
import aiohttp
import os
from pathlib import Path
from playwright.async_api import async_playwright

async def test_raven_page():
    """测试访问瑞文测试页面"""
    print("🚀 测试访问瑞文智力测验页面...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        try:
            context = await browser.new_context()
            page = await context.new_page()
            
            # 网络监听
            image_requests = []
            
            async def handle_request(request):
                url = request.url
                if any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                    print(f"🖼️  发现图片: {url}")
                    image_requests.append(url)
            
            page.on('request', handle_request)
            
            # 访问页面
            print("🌐 访问页面...")
            await page.goto("https://minke8.cn/iq1.html", wait_until='networkidle')
            
            # 等待页面完全加载
            await asyncio.sleep(5)
            
            print(f"📊 发现 {len(image_requests)} 张图片")
            for i, url in enumerate(image_requests, 1):
                print(f"  {i}. {url}")
            
            # 尝试找到选项并点击
            print("\n🔍 查找页面元素...")
            
            # 获取页面标题
            title = await page.title()
            print(f"页面标题: {title}")
            
            # 截图保存
            screenshot_path = Path("scripts/page_screenshot.png")
            await page.screenshot(path=screenshot_path)
            print(f"📷 页面截图保存到: {screenshot_path}")
            
            # 查找可能的选项元素
            images = await page.query_selector_all('img')
            print(f"📋 发现 {len(images)} 个img元素")
            
            links = await page.query_selector_all('a')
            print(f"🔗 发现 {len(links)} 个链接元素")
            
            # 等待用户操作
            print("\n⏳ 等待10秒钟观察页面...")
            await asyncio.sleep(10)
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_raven_page())