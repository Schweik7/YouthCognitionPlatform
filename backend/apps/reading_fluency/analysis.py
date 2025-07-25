#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
朗读流畅性测试结果分析模块
集成自 ise-demo/语音评测结果分析.py
"""

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """错误类型枚举"""
    CORRECT = 0     # 正确
    MISSED = 16     # 漏读
    ADDED = 32      # 增读
    REPEATED = 64   # 回读
    REPLACED = 128  # 替换


@dataclass
class PhoneAnalysis:
    """音素分析结果"""
    content: str = ""           # 音素内容
    beg_pos: int = 0           # 开始位置（帧）
    end_pos: int = 0           # 结束位置（帧）
    time_len: int = 0          # 时长（帧）
    dp_message: int = 0        # 增漏信息
    perr_msg: int = 0          # 错误信息
    perr_level_msg: int = 0    # 置信度（1最好，3最差）
    is_yun: int = 0            # 0:声母, 1:韵母
    rec_node_type: str = ""    # 节点类型
    mono_tone: Optional[str] = None  # 调型

    @property
    def duration_ms(self) -> int:
        """持续时间（毫秒）"""
        return self.time_len * 10

    @property
    def error_type(self) -> ErrorType:
        """错误类型"""
        return ErrorType(self.dp_message)

    @property
    def is_correct(self) -> bool:
        """是否正确"""
        if self.rec_node_type != "paper":
            return True  # 非试卷内容不算错误
        return self.dp_message == 0

    @property
    def confidence_level(self) -> str:
        """置信度等级"""
        levels = {1: "高", 2: "中", 3: "低"}
        return levels.get(self.perr_level_msg, "未知")

    @property
    def error_description(self) -> str:
        """错误描述"""
        if self.dp_message == 0 and self.rec_node_type == "paper":
            return "正确"

        descriptions = []
        
        # 增漏信息判断
        error_map = {
            16: "漏读",
            32: "增读", 
            64: "回读",
            128: "替换"
        }
        
        if self.dp_message in error_map:
            descriptions.append(error_map[self.dp_message])

        # 辅助错误信息
        if self.dp_message == 0 and self.perr_msg != 0:
            if self.is_yun == 0:  # 声母
                if self.perr_msg == 1:
                    descriptions.append("声母发音不标准")
            else:  # 韵母
                error_map = {
                    1: "韵母发音不标准",
                    2: "调型不标准", 
                    3: "韵母和调型不标准"
                }
                if self.perr_msg in error_map:
                    descriptions.append(error_map[self.perr_msg])

        return "; ".join(descriptions) if descriptions else (
            "非试卷内容" if self.rec_node_type != "paper" else "正确"
        )


@dataclass
class SyllableAnalysis:
    """音节分析结果"""
    content: str = ""           # 音节内容
    symbol: str = ""            # 拼音（带声调）
    beg_pos: int = 0           # 开始位置（帧）
    end_pos: int = 0           # 结束位置（帧）
    time_len: int = 0          # 时长（帧）
    dp_message: int = 0        # 增漏信息
    rec_node_type: str = ""    # 节点类型
    phones: List[PhoneAnalysis] = None

    def __post_init__(self):
        if self.phones is None:
            self.phones = []

    @property
    def duration_ms(self) -> int:
        """持续时间（毫秒）"""
        return self.time_len * 10

    @property
    def error_type(self) -> ErrorType:
        """错误类型"""
        return ErrorType(self.dp_message)

    @property
    def is_paper_content(self) -> bool:
        """是否为试卷内容"""
        return self.rec_node_type == "paper"

    @property
    def is_correct(self) -> bool:
        """音节是否正确"""
        if not self.is_paper_content:
            return True
        return self.dp_message == 0

    @property
    def tone(self) -> Optional[int]:
        """声调"""
        if not self.symbol:
            return None
        for char in reversed(self.symbol):
            if char.isdigit():
                tone = int(char)
                return 0 if tone == 5 else tone  # 5表示轻声
        return None

    @property
    def error_summary(self) -> str:
        """错误摘要"""
        if self.is_correct:
            return "正确"

        errors = []
        error_map = {
            16: "漏读",
            32: "增读",
            64: "回读", 
            128: "替换"
        }

        if self.dp_message in error_map:
            errors.append(error_map[self.dp_message])

        # 检查音素细节
        if self.dp_message == 0:
            phone_errors = []
            for phone in self.phones:
                if phone.rec_node_type == "paper" and phone.perr_msg != 0:
                    phone_errors.append(f"{phone.content}发音不标准")
            if phone_errors:
                errors.extend(phone_errors)

        return "; ".join(errors) if errors else "未知错误"


@dataclass
class CharacterAnalysis:
    """单字分析结果"""
    character: str = ""               # 汉字
    expected_pinyin: str = ""         # 期望拼音
    beg_pos: int = 0                 # 开始位置（帧）
    end_pos: int = 0                 # 结束位置（帧）
    time_len: int = 0                # 总时长（帧）
    syllables: List[SyllableAnalysis] = None

    def __post_init__(self):
        if self.syllables is None:
            self.syllables = []

    @property
    def duration_ms(self) -> int:
        """持续时间（毫秒）"""
        return self.time_len * 10

    @property
    def paper_syllables(self) -> List[SyllableAnalysis]:
        """只返回试卷内容的音节"""
        return [syll for syll in self.syllables if syll.is_paper_content]

    @property
    def is_read(self) -> bool:
        """是否被朗读"""
        return len(self.paper_syllables) > 0

    @property
    def is_correct(self) -> bool:
        """是否正确"""
        if not self.is_read:
            return False
        return all(syll.is_correct for syll in self.paper_syllables)

    @property
    def actual_pinyin(self) -> str:
        """实际读出的拼音"""
        paper_sylls = self.paper_syllables
        if paper_sylls:
            return paper_sylls[0].symbol
        return ""

    @property
    def status_summary(self) -> str:
        """状态摘要"""
        if not self.is_read:
            return "漏读"
        elif self.is_correct:
            return "正确"
        else:
            paper_sylls = self.paper_syllables
            if paper_sylls:
                return paper_sylls[0].error_summary
            return "未知错误"


@dataclass
class EvaluationAnalysis:
    """完整的评测分析结果"""
    # 基本信息
    analysis_time: datetime = None
    
    # 整体分数
    overall_score: float = 0.0
    phone_score: float = 0.0
    tone_score: float = 0.0
    fluency_score: float = 0.0
    integrity_score: float = 0.0
    
    # 状态信息
    is_rejected: bool = False
    except_info: Optional[str] = None
    total_time: int = 0  # 总时长（帧）
    
    # 详细分析
    characters: List[CharacterAnalysis] = None
    
    # 原始数据
    raw_xml: str = ""

    def __post_init__(self):
        if self.analysis_time is None:
            self.analysis_time = datetime.now()
        if self.characters is None:
            self.characters = []

    @property
    def total_duration_ms(self) -> int:
        """总时长（毫秒）"""
        return self.total_time * 10

    @property
    def total_characters(self) -> int:
        """总字数"""
        return len(self.characters)

    @property
    def read_characters(self) -> int:
        """已朗读字数"""
        return len([char for char in self.characters if char.is_read])

    @property
    def correct_characters(self) -> int:
        """正确字数"""
        return len([char for char in self.characters if char.is_correct])

    @property
    def character_accuracy_rate(self) -> float:
        """字准确率"""
        if self.total_characters == 0:
            return 0.0
        return self.correct_characters / self.total_characters * 100

    @property
    def reading_completion_rate(self) -> float:
        """朗读完成率"""
        if self.total_characters == 0:
            return 0.0
        return self.read_characters / self.total_characters * 100


class XfyunXMLAnalyzer:
    """科大讯飞XML分析器"""

    @staticmethod
    def analyze_xml_content(xml_content: str) -> EvaluationAnalysis:
        """分析XML内容"""
        result = EvaluationAnalysis()
        result.raw_xml = xml_content

        try:
            root = ET.fromstring(xml_content)
            
            # 查找评测结果节点
            read_syllable = root.find(".//rec_paper/read_syllable")
            
            if read_syllable is not None:
                # 解析整体分数
                result.overall_score = float(read_syllable.get("total_score", 0))
                result.phone_score = float(read_syllable.get("phone_score", 0))
                result.tone_score = float(read_syllable.get("tone_score", 0))
                result.fluency_score = float(read_syllable.get("fluency_score", 0))
                result.integrity_score = float(read_syllable.get("integrity_score", 0))
                
                # 解析状态信息
                result.except_info = read_syllable.get("except_info")
                result.total_time = int(read_syllable.get("time_len", 0))
                
                # 解析字符详情
                result.characters = XfyunXMLAnalyzer._parse_characters(read_syllable)
            else:
                logger.warning("未找到rec_paper内的read_syllable节点")

            logger.info(f"XML解析完成，总分: {result.overall_score}")

        except ET.ParseError as e:
            logger.error(f"XML解析失败: {e}")
            raise
        except Exception as e:
            logger.error(f"结果解析过程中发生错误: {e}")
            raise

        return result

    @staticmethod
    def _parse_characters(read_syllable_node) -> List[CharacterAnalysis]:
        """解析字符节点"""
        characters = []

        # 每个sentence对应一个字
        for sentence_node in read_syllable_node.findall(".//sentence"):
            char_content = sentence_node.get("content", "")
            if not char_content:
                continue

            character = CharacterAnalysis(
                character=char_content,
                beg_pos=int(sentence_node.get("beg_pos", 0)),
                end_pos=int(sentence_node.get("end_pos", 0)),
                time_len=int(sentence_node.get("time_len", 0)),
            )

            # 获取word节点中的期望拼音
            word_node = sentence_node.find(".//word")
            if word_node is not None:
                character.expected_pinyin = word_node.get("symbol", "")
                
                # 解析所有音节
                character.syllables = XfyunXMLAnalyzer._parse_syllables_in_word(word_node)

            characters.append(character)

        return characters

    @staticmethod
    def _parse_syllables_in_word(word_node) -> List[SyllableAnalysis]:
        """解析word中的所有音节"""
        syllables = []

        for syll_node in word_node.findall(".//syll"):
            syllable = SyllableAnalysis(
                content=syll_node.get("content", ""),
                symbol=syll_node.get("symbol", ""),
                beg_pos=int(syll_node.get("beg_pos", 0)),
                end_pos=int(syll_node.get("end_pos", 0)),
                time_len=int(syll_node.get("time_len", 0)),
                dp_message=int(syll_node.get("dp_message", 0)),
                rec_node_type=syll_node.get("rec_node_type", ""),
            )

            # 解析音素
            syllable.phones = XfyunXMLAnalyzer._parse_phones_in_syllable(syll_node)
            syllables.append(syllable)

        return syllables

    @staticmethod
    def _parse_phones_in_syllable(syll_node) -> List[PhoneAnalysis]:
        """解析音节中的音素"""
        phones = []

        for phone_node in syll_node.findall(".//phone"):
            phone = PhoneAnalysis(
                content=phone_node.get("content", ""),
                beg_pos=int(phone_node.get("beg_pos", 0)) if phone_node.get("beg_pos") else 0,
                end_pos=int(phone_node.get("end_pos", 0)) if phone_node.get("end_pos") else 0,
                time_len=int(phone_node.get("time_len", 0)) if phone_node.get("time_len") else 0,
                dp_message=int(phone_node.get("dp_message", 0)),
                perr_msg=int(phone_node.get("perr_msg", 0)),
                perr_level_msg=int(phone_node.get("perr_level_msg", 0)),
                is_yun=int(phone_node.get("is_yun", 0)),
                rec_node_type=phone_node.get("rec_node_type", ""),
                mono_tone=phone_node.get("mono_tone"),
            )
            phones.append(phone)

        return phones


def analyze_reading_evaluation(xml_result: str) -> Dict[str, Any]:
    """分析朗读评测结果的入口函数"""
    try:
        analyzer = XfyunXMLAnalyzer()
        analysis = analyzer.analyze_xml_content(xml_result)
        
        # 构建简化的分析结果
        analysis_result = {
            "success": True,
            "overall_score": analysis.overall_score,
            "phone_score": analysis.phone_score,
            "tone_score": analysis.tone_score,
            "fluency_score": analysis.fluency_score,
            "integrity_score": analysis.integrity_score,
            "total_characters": analysis.total_characters,
            "read_characters": analysis.read_characters,
            "correct_characters": analysis.correct_characters,
            "character_accuracy_rate": analysis.character_accuracy_rate,
            "reading_completion_rate": analysis.reading_completion_rate,
            "total_duration_ms": analysis.total_duration_ms,
            "analysis_time": analysis.analysis_time.isoformat(),
            "character_details": [
                {
                    "character": char.character,
                    "expected_pinyin": char.expected_pinyin,
                    "actual_pinyin": char.actual_pinyin,
                    "is_read": char.is_read,
                    "is_correct": char.is_correct,
                    "status": char.status_summary,
                    "duration_ms": char.duration_ms
                }
                for char in analysis.characters
            ]
        }
        
        return analysis_result
        
    except Exception as e:
        logger.error(f"分析朗读评测结果失败: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "analysis_time": datetime.now().isoformat()
        }


def estimate_correct_character_count(xml_result: str, max_chars: int = 10) -> int:
    """基于XML结果估算正确朗读的字符数"""
    try:
        analysis_result = analyze_reading_evaluation(xml_result)
        if analysis_result["success"]:
            # 基于正确字符数和准确率估算
            correct_chars = analysis_result["correct_characters"]
            return min(max_chars, correct_chars)
        else:
            # 解析失败时，基于总分估算
            try:
                root = ET.fromstring(xml_result)
                read_syllable = root.find(".//rec_paper/read_syllable")
                if read_syllable is not None:
                    total_score = float(read_syllable.get("total_score", 0))
                    return min(max_chars, int(max_chars * total_score / 100))
            except:
                pass
            return 0
    except Exception as e:
        logger.error(f"估算正确字符数失败: {str(e)}")
        return 0