"""
模拟语音评测功能
用于在没有真实科大讯飞API凭证时进行测试
"""
import json
import random
from pathlib import Path
from typing import Dict, Any


def mock_audio_evaluation(audio_file_path: str, text: str) -> Dict[str, Any]:
    """
    模拟音频评测功能
    
    Args:
        audio_file_path: 音频文件路径
        text: 评测文本
        
    Returns:
        模拟的评测结果
    """
    
    # 检查文件是否存在
    if not Path(audio_file_path).exists():
        raise FileNotFoundError(f"音频文件不存在: {audio_file_path}")
    
    # 模拟音频文件大小检查
    file_size = Path(audio_file_path).stat().st_size
    if file_size < 1000:  # 小于1KB认为是无效音频
        raise ValueError("音频文件过小，可能无效")
    
    # 模拟评测结果
    characters = text.split()
    character_count = len(characters)
    
    # 随机生成评分（模拟真实评测的波动性）
    base_score = random.uniform(75, 95)  # 基础分数
    total_score = round(base_score + random.uniform(-5, 5), 1)
    phone_score = round(base_score + random.uniform(-8, 8), 1)
    tone_score = round(base_score + random.uniform(-6, 6), 1)
    fluency_score = round(base_score + random.uniform(-10, 10), 1)
    integrity_score = round(base_score + random.uniform(-3, 3), 1)
    
    # 模拟正确朗读字数（基于评分）
    accuracy_rate = total_score / 100
    correct_count = max(1, round(character_count * accuracy_rate))
    
    # 构造模拟的XML结果
    mock_xml = f"""<?xml version="1.0" encoding="utf-8"?>
<xml>
    <ret>0</ret>
    <sid>speech_eval_001</sid>
    <data>
        <total_score>{total_score}</total_score>
        <phone_score>{phone_score}</phone_score>
        <tone_score>{tone_score}</tone_score>
        <fluency_score>{fluency_score}</fluency_score>
        <integrity_score>{integrity_score}</integrity_score>
        <sentence>
            <index>1</index>
            <score>{total_score}</score>
            <word_count>{character_count}</word_count>
"""
    
    # 为每个字符添加详细评分
    for i, char in enumerate(characters):
        char_score = round(total_score + random.uniform(-15, 15), 1)
        mock_xml += f"""            <word>
                <index>{i+1}</index>
                <text>{char}</text>
                <score>{char_score}</score>
                <phone_score>{round(char_score + random.uniform(-5, 5), 1)}</phone_score>
                <tone_score>{round(char_score + random.uniform(-3, 3), 1)}</tone_score>
            </word>
"""
    
    mock_xml += """        </sentence>
    </data>
</xml>"""
    
    # 构造返回结果
    evaluation_result = {
        "success": True,
        "xml_result": mock_xml,
        "total_score": total_score,
        "phone_score": phone_score,
        "tone_score": tone_score,
        "fluency_score": fluency_score,
        "integrity_score": integrity_score,
        "correct_character_count": correct_count,
        "character_accuracy_rate": round(accuracy_rate, 3),
        "mock": True  # 标识这是模拟结果
    }
    
    return evaluation_result


def analyze_mock_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """分析模拟评测结果"""
    return {
        "overall_score": result["total_score"],
        "phone_score": result["phone_score"],
        "tone_score": result["tone_score"],
        "fluency_score": result["fluency_score"],
        "integrity_score": result["integrity_score"],
        "character_accuracy_rate": result["character_accuracy_rate"],
        "correct_character_count": result["correct_character_count"],
        "is_mock": True,
        "character_details": [],  # 简化处理
        "detailed_analysis": {
            "pronunciation_analysis": "模拟评测：发音基本准确",
            "fluency_analysis": "模拟评测：朗读较为流畅", 
            "tone_analysis": "模拟评测：语调自然",
            "integrity_analysis": "模拟评测：内容完整"
        }
    }