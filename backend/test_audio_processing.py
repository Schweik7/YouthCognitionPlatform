#!/usr/bin/env python3
"""
测试音频文件处理脚本
"""
import asyncio
from pathlib import Path
from apps.oral_reading_fluency.xfyun_sdk import XfyunSDKFactory, EvaluationRequest

async def test_audio_file():
    """测试单个音频文件的处理"""
    
    # 音频文件路径
    audio_file = Path("uploads/oral_reading_fluency/test_1_round1_row0_20250725_152645.webm")
    
    if not audio_file.exists():
        print(f"❌ 音频文件不存在: {audio_file}")
        return
    
    print(f"✅ 找到音频文件: {audio_file}")
    print(f"📊 文件大小: {audio_file.stat().st_size} bytes")
    
    # 测试文件是否可读
    try:
        with open(audio_file, 'rb') as f:
            data = f.read(1024)  # 读取前1KB
            print(f"✅ 文件可读，前1KB数据长度: {len(data)}")
    except Exception as e:
        print(f"❌ 文件读取失败: {e}")
        return
    
    # 创建评测请求
    try:
        # 使用真实的API凭证
        from config import settings
        XfyunSDKFactory.initialize(
            app_id=settings.XFYUN_APP_ID,
            api_key=settings.XFYUN_API_KEY,
            api_secret=settings.XFYUN_API_SECRET
        )
        sdk = XfyunSDKFactory.get_sdk()
        print("✅ SDK创建成功")
        print(f"📱 APP ID: {settings.XFYUN_APP_ID}")
        
        # 准备评测请求
        request = EvaluationRequest(
            category="read_sentence",  # 使用句子评测
            text="我 是 一 个 好 孩 子 学 习 要",  # 第0行的文本
            audio_format="mp3",  # 使用MP3格式
            aue="lame",  # MP3格式使用lame编码
            sample_rate=44100,  # MP3标准采样率
            language="cn_vip",
            group="pupil"
        )
        
        print("✅ 评测请求创建成功")
        print(f"📝 评测文本: {request.text}")
        
        # 实际调用API进行评测
        print("📡 开始发送评测请求...")
        
        try:
            result = await sdk.evaluate_audio_file(audio_file, request)
            print(f"✅ 评测成功!")
            print(f"📊 总分: {result.total_score}")
            print(f"🎵 发音分: {result.phone_score}")
            print(f"🎯 语调分: {result.tone_score}")
            print(f"🌊 流畅度: {result.fluency_score}")
            print(f"📝 完整度: {result.integrity_score}")
            
        except Exception as api_error:
            print(f"❌ API调用失败: {api_error}")
            print("🔄 这可能是由于网络问题或API配置问题")
        
    except Exception as e:
        print(f"❌ SDK测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🎵 开始测试音频文件处理...")
    asyncio.run(test_audio_file())
    print("🎵 测试完成!")