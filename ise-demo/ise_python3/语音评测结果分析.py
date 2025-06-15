"""
修正版科大讯飞语音评测XML分析器
基于实际XML数据结构重新设计
"""

import xml.etree.ElementTree as ET
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """错误类型枚举"""

    CORRECT = 0  # 正确
    MISSED = 16  # 漏读
    ADDED = 32  # 增读
    REPEATED = 64  # 回读
    REPLACED = 128  # 替换


class NodeType(Enum):
    """节点类型枚举"""

    PAPER = "paper"  # 试卷内容
    SIL = "sil"  # 静音
    FIL = "fil"  # 噪音


@dataclass
class PhoneAnalysis:
    """音素分析结果"""

    content: str = ""  # 音素内容
    beg_pos: int = 0  # 开始位置（帧）
    end_pos: int = 0  # 结束位置（帧）
    time_len: int = 0  # 时长（帧）
    dp_message: int = 0  # 增漏信息
    perr_msg: int = 0  # 错误信息
    perr_level_msg: int = 0  # 置信度（1最好，3最差）
    is_yun: int = 0  # 0:声母, 1:韵母
    rec_node_type: str = ""  # 节点类型
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
        return (
            self.dp_message == 0
            and self.perr_msg == 0
            and self.rec_node_type == "paper"
        )

    @property
    def confidence_level(self) -> str:
        """置信度等级"""
        if self.perr_level_msg == 1:
            return "高"
        elif self.perr_level_msg == 2:
            return "中"
        elif self.perr_level_msg == 3:
            return "低"
        else:
            return "未知"

    @property
    def error_description(self) -> str:
        """错误描述"""
        if self.is_correct:
            return "正确"

        descriptions = []

        # 增漏信息
        if self.dp_message == 16:
            descriptions.append("漏读")
        elif self.dp_message == 32:
            descriptions.append("增读")
        elif self.dp_message == 64:
            descriptions.append("回读")
        elif self.dp_message == 128:
            descriptions.append("替换")

        # 音素错误信息
        if self.is_yun == 0:  # 声母
            if self.perr_msg == 1:
                descriptions.append("声母错误")
        else:  # 韵母
            if self.perr_msg == 1:
                descriptions.append("韵母错误")
            elif self.perr_msg == 2:
                descriptions.append("调型错误")
            elif self.perr_msg == 3:
                descriptions.append("韵母和调型错误")

        return "; ".join(descriptions) if descriptions else "未知错误"


@dataclass
class SyllableAnalysis:
    """音节分析结果"""

    content: str = ""  # 音节内容
    symbol: str = ""  # 拼音（带声调）
    beg_pos: int = 0  # 开始位置（帧）
    end_pos: int = 0  # 结束位置（帧）
    time_len: int = 0  # 时长（帧）
    dp_message: int = 0  # 增漏信息
    rec_node_type: str = ""  # 节点类型
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
            return True  # 非试卷内容（如静音）不算错误

        return self.dp_message == 0 and all(
            phone.is_correct for phone in self.phones if phone.rec_node_type == "paper"
        )

    @property
    def pinyin_without_tone(self) -> str:
        """不带声调的拼音"""
        if not self.symbol:
            return ""
        # 移除数字声调
        return "".join(char for char in self.symbol if not char.isdigit())

    @property
    def tone(self) -> Optional[int]:
        """声调"""
        if not self.symbol:
            return None
        # 提取最后的数字
        for char in reversed(self.symbol):
            if char.isdigit():
                tone = int(char)
                return 0 if tone == 5 else tone  # 5表示轻声，转换为0
        return None

    @property
    def error_summary(self) -> str:
        """错误摘要"""
        if self.is_correct:
            return "正确"

        errors = []

        # 音节级错误
        if self.dp_message != 0:
            errors.append(f"音节{self.error_type.name}")

        # 音素级错误
        for phone in self.phones:
            if phone.rec_node_type == "paper" and not phone.is_correct:
                errors.append(f"{phone.content}({phone.error_description})")

        return "; ".join(errors) if errors else "未知错误"


@dataclass
class CharacterAnalysis:
    """单字分析结果"""

    character: str = ""  # 汉字
    expected_pinyin: str = ""  # 期望拼音
    beg_pos: int = 0  # 开始位置（帧）
    end_pos: int = 0  # 结束位置（帧）
    time_len: int = 0  # 总时长（帧）
    syllables: List[SyllableAnalysis] = None  # 所有音节（包括sil/fil/paper）

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
    def sil_syllables(self) -> List[SyllableAnalysis]:
        """静音音节"""
        return [syll for syll in self.syllables if syll.rec_node_type == "sil"]

    @property
    def fil_syllables(self) -> List[SyllableAnalysis]:
        """噪音音节"""
        return [syll for syll in self.syllables if syll.rec_node_type == "fil"]

    @property
    def is_read(self) -> bool:
        """是否被朗读（有paper内容）"""
        return len(self.paper_syllables) > 0

    @property
    def is_correct(self) -> bool:
        """是否正确"""
        if not self.is_read:
            return False  # 没有朗读就是错误

        # 只检查试卷内容的音节
        return all(syll.is_correct for syll in self.paper_syllables)

    @property
    def actual_pinyin(self) -> str:
        """实际读出的拼音"""
        paper_sylls = self.paper_syllables
        if paper_sylls:
            return paper_sylls[0].symbol  # 通常一个字只有一个试卷音节
        return ""

    @property
    def total_silence_duration(self) -> int:
        """总静音时长（毫秒）"""
        return sum(syll.duration_ms for syll in self.sil_syllables)

    @property
    def actual_speech_duration(self) -> int:
        """实际语音时长（毫秒）"""
        return sum(syll.duration_ms for syll in self.paper_syllables)

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
    xml_file: str = ""
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
    def missed_characters(self) -> int:
        """漏读字数"""
        return len([char for char in self.characters if not char.is_read])

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
    """科大讯飞XML分析器 - 基于实际数据结构"""

    @staticmethod
    def analyze_xml_file(xml_file_path: Path) -> EvaluationAnalysis:
        """分析XML文件"""
        try:
            with open(xml_file_path, "r", encoding="utf-8") as f:
                xml_content = f.read()

            result = XfyunXMLAnalyzer.analyze_xml_content(xml_content)
            result.xml_file = str(xml_file_path)
            return result

        except Exception as e:
            logger.error(f"分析XML文件失败: {e}")
            raise

    @staticmethod
    def analyze_xml_content(xml_content: str) -> EvaluationAnalysis:
        """分析XML内容"""
        result = EvaluationAnalysis()
        result.raw_xml = xml_content

        try:
            root = ET.fromstring(xml_content)

            # 查找评测结果节点
            read_syllable = root.find(".//read_syllable")

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

                # 解析所有音节（包括sil/fil/paper）
                character.syllables = XfyunXMLAnalyzer._parse_syllables_in_word(
                    word_node
                )

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
                beg_pos=int(phone_node.get("beg_pos", 0))
                if phone_node.get("beg_pos")
                else 0,
                end_pos=int(phone_node.get("end_pos", 0))
                if phone_node.get("end_pos")
                else 0,
                time_len=int(phone_node.get("time_len", 0))
                if phone_node.get("time_len")
                else 0,
                dp_message=int(phone_node.get("dp_message", 0)),
                perr_msg=int(phone_node.get("perr_msg", 0)),
                perr_level_msg=int(phone_node.get("perr_level_msg", 0)),
                is_yun=int(phone_node.get("is_yun", 0)),
                rec_node_type=phone_node.get("rec_node_type", ""),
                mono_tone=phone_node.get("mono_tone"),
            )
            phones.append(phone)

        return phones


class AnalysisReporter:
    """分析报告生成器"""

    @staticmethod
    def print_detailed_analysis(analysis: EvaluationAnalysis):
        """打印详细分析结果"""
        print("\n" + "=" * 80)
        print("🎙️  科大讯飞语音评测详细分析")
        print("=" * 80)

        # 基本信息
        print(f"📁 XML文件: {analysis.xml_file}")
        print(f"🕐 分析时间: {analysis.analysis_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(
            f"⏱️  总时长: {analysis.total_duration_ms}ms ({analysis.total_duration_ms / 1000:.1f}秒)"
        )

        # 整体分数
        print(f"\n📊 整体评分")
        print("-" * 50)
        print(
            f"总分: {analysis.overall_score:6.2f} | 声韵分: {analysis.phone_score:6.2f}"
        )
        print(
            f"调型分: {analysis.tone_score:6.2f} | 流畅度: {analysis.fluency_score:6.2f}"
        )
        print(f"完整度: {analysis.integrity_score:6.2f}")

        # 统计信息
        print(f"\n📈 统计信息")
        print("-" * 50)
        print(
            f"总字数: {analysis.total_characters:3d} | 已读字数: {analysis.read_characters:3d} | 正确字数: {analysis.correct_characters:3d}"
        )
        print(
            f"漏读字数: {analysis.missed_characters:3d} | 字准确率: {analysis.character_accuracy_rate:5.1f}% | 完成率: {analysis.reading_completion_rate:5.1f}%"
        )

        # 详细字符分析
        print(f"\n🔍 逐字详细分析")
        print("-" * 80)

        for i, char in enumerate(analysis.characters, 1):
            # 字符基本信息
            status_icon = "✅" if char.is_correct else ("⭕" if char.is_read else "❌")
            print(
                f"\n{i:2d}. 字符: {char.character:2s} [{char.expected_pinyin:8s}] {status_icon} {char.status_summary}"
            )
            print(
                f"    总时长: {char.duration_ms:4d}ms | 语音: {char.actual_speech_duration:3d}ms | 静音: {char.total_silence_duration:3d}ms"
            )

            if char.actual_pinyin and char.actual_pinyin != char.expected_pinyin:
                print(f"    实际读音: {char.actual_pinyin}")

            # 音节详情
            if char.syllables:
                print(f"    音节详情:")
                for j, syll in enumerate(char.syllables):
                    syll_type = {"paper": "📝", "sil": "🔇", "fil": "🔊"}.get(
                        syll.rec_node_type, "❓"
                    )
                    if syll.rec_node_type == "paper":
                        syll_status = "✅" if syll.is_correct else "❌"
                        print(
                            f"      {j + 1}. {syll_type} {syll.content:4s} [{syll.symbol:6s}] {syll_status} {syll.duration_ms:3d}ms"
                        )
                        if not syll.is_correct:
                            print(f"         错误: {syll.error_summary}")

                        # 音素详情
                        phone_line = "         音素: "
                        for phone in syll.phones:
                            if phone.rec_node_type == "paper":
                                phone_status = "✅" if phone.is_correct else "❌"
                                phone_type = "韵" if phone.is_yun else "声"
                                phone_line += (
                                    f"{phone.content}({phone_type}){phone_status} "
                                )
                        if phone_line.strip().endswith("音素:"):
                            phone_line += "无"
                        print(phone_line)
                    else:
                        print(
                            f"      {j + 1}. {syll_type} {syll.rec_node_type:4s} {syll.duration_ms:3d}ms"
                        )

        # 错误统计
        error_stats = AnalysisReporter._calculate_error_statistics(analysis)
        if error_stats:
            print(f"\n📉 错误统计")
            print("-" * 50)
            for error_type, count in error_stats.items():
                print(f"{error_type}: {count}次")

        # 时间分析
        print(f"\n⏱️  时间分析")
        print("-" * 50)
        if analysis.characters:
            read_chars = [c for c in analysis.characters if c.is_read]
            if read_chars:
                avg_char_time = sum(c.actual_speech_duration for c in read_chars) / len(
                    read_chars
                )
                avg_total_time = sum(c.duration_ms for c in analysis.characters) / len(
                    analysis.characters
                )
                total_speech_time = sum(
                    c.actual_speech_duration for c in analysis.characters
                )
                total_silence_time = sum(
                    c.total_silence_duration for c in analysis.characters
                )

                print(f"平均字语音时长: {avg_char_time:.0f}ms")
                print(f"平均字总时长: {avg_total_time:.0f}ms")
                print(
                    f"总语音时长: {total_speech_time}ms ({total_speech_time / 1000:.1f}秒)"
                )
                print(
                    f"总静音时长: {total_silence_time}ms ({total_silence_time / 1000:.1f}秒)"
                )

                if analysis.total_duration_ms > 0:
                    speech_ratio = total_speech_time / analysis.total_duration_ms * 100
                    print(f"语音占比: {speech_ratio:.1f}%")

    @staticmethod
    def _calculate_error_statistics(analysis: EvaluationAnalysis) -> Dict[str, int]:
        """计算错误统计"""
        error_stats = {}

        for char in analysis.characters:
            if not char.is_read:
                error_stats["漏读"] = error_stats.get("漏读", 0) + 1
            elif not char.is_correct:
                for syll in char.paper_syllables:
                    if not syll.is_correct:
                        for phone in syll.phones:
                            if phone.rec_node_type == "paper" and not phone.is_correct:
                                error_desc = phone.error_description
                                error_stats[error_desc] = (
                                    error_stats.get(error_desc, 0) + 1
                                )

        return dict(sorted(error_stats.items(), key=lambda x: x[1], reverse=True))

    @staticmethod
    def export_to_csv(analysis: EvaluationAnalysis, output_path: Path) -> bool:
        """导出到CSV"""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)

                # 写入表头
                headers = [
                    "序号",
                    "汉字",
                    "期望拼音",
                    "实际拼音",
                    "状态",
                    "是否正确",
                    "总时长(ms)",
                    "语音时长(ms)",
                    "静音时长(ms)",
                    "错误描述",
                    "开始位置(帧)",
                    "结束位置(帧)",
                ]
                writer.writerow(headers)

                # 写入数据
                for i, char in enumerate(analysis.characters, 1):
                    row = [
                        i,
                        char.character,
                        char.expected_pinyin,
                        char.actual_pinyin,
                        "已读" if char.is_read else "漏读",
                        "正确" if char.is_correct else "错误",
                        char.duration_ms,
                        char.actual_speech_duration,
                        char.total_silence_duration,
                        char.status_summary,
                        char.beg_pos,
                        char.end_pos,
                    ]
                    writer.writerow(row)

            logger.info(f"CSV已导出: {output_path}")
            return True

        except Exception as e:
            logger.error(f"导出CSV失败: {e}")
            return False

    @staticmethod
    def generate_summary_report(
        analysis: EvaluationAnalysis, output_path: Path
    ) -> bool:
        """生成摘要报告"""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write("科大讯飞语音评测分析报告\n")
                f.write("=" * 60 + "\n\n")

                # 基本信息
                f.write("📋 基本信息\n")
                f.write("-" * 30 + "\n")
                f.write(f"XML文件: {analysis.xml_file}\n")
                f.write(
                    f"分析时间: {analysis.analysis_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                f.write(
                    f"总时长: {analysis.total_duration_ms}ms ({analysis.total_duration_ms / 1000:.1f}秒)\n\n"
                )

                # 整体评分
                f.write("📊 整体评分\n")
                f.write("-" * 30 + "\n")
                f.write(f"总分: {analysis.overall_score:.2f}\n")
                f.write(f"声韵分: {analysis.phone_score:.2f}\n")
                f.write(f"调型分: {analysis.tone_score:.2f}\n")
                f.write(f"流畅度分: {analysis.fluency_score:.2f}\n")
                f.write(f"完整度分: {analysis.integrity_score:.2f}\n\n")

                # 统计摘要
                f.write("📈 统计摘要\n")
                f.write("-" * 30 + "\n")
                f.write(f"总字数: {analysis.total_characters}\n")
                f.write(f"已读字数: {analysis.read_characters}\n")
                f.write(f"正确字数: {analysis.correct_characters}\n")
                f.write(f"漏读字数: {analysis.missed_characters}\n")
                f.write(f"字准确率: {analysis.character_accuracy_rate:.1f}%\n")
                f.write(f"朗读完成率: {analysis.reading_completion_rate:.1f}%\n\n")

                # 错误分析
                error_stats = AnalysisReporter._calculate_error_statistics(analysis)
                if error_stats:
                    f.write("❌ 错误分析\n")
                    f.write("-" * 30 + "\n")
                    for error_type, count in error_stats.items():
                        f.write(f"{error_type}: {count}次\n")
                    f.write("\n")

                # 详细结果
                f.write("🔍 详细结果\n")
                f.write("-" * 30 + "\n")
                for i, char in enumerate(analysis.characters, 1):
                    status = (
                        "✅正确"
                        if char.is_correct
                        else ("⭕已读" if char.is_read else "❌漏读")
                    )
                    f.write(
                        f"{i:2d}. {char.character} [{char.expected_pinyin}] {status}\n"
                    )
                    if (
                        char.actual_pinyin != char.expected_pinyin
                        and char.actual_pinyin
                    ):
                        f.write(f"    实际读音: {char.actual_pinyin}\n")
                    f.write(
                        f"    时长: {char.duration_ms}ms (语音:{char.actual_speech_duration}ms)\n"
                    )
                    if not char.is_correct and char.is_read:
                        f.write(f"    错误: {char.status_summary}\n")

            logger.info(f"摘要报告已生成: {output_path}")
            return True

        except Exception as e:
            logger.error(f"生成摘要报告失败: {e}")
            return False


def analyze_xml_file_demo(xml_file_path: str):
    """演示分析XML文件"""
    xml_path = Path(xml_file_path)

    if not xml_path.exists():
        print(f"❌ 文件不存在: {xml_path}")
        return

    print(f"🔍 开始分析XML文件: {xml_path.name}")

    try:
        # 分析XML
        analyzer = XfyunXMLAnalyzer()
        analysis = analyzer.analyze_xml_file(xml_path)

        # 显示详细分析
        AnalysisReporter.print_detailed_analysis(analysis)

        # 生成报告
        output_dir = Path("./xml_analysis_results")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # CSV报告
        csv_path = output_dir / f"analysis_{timestamp}.csv"
        AnalysisReporter.export_to_csv(analysis, csv_path)

        # 摘要报告
        summary_path = output_dir / f"summary_{timestamp}.txt"
        AnalysisReporter.generate_summary_report(analysis, summary_path)

        # JSON数据
        json_path = output_dir / f"analysis_{timestamp}.json"
        export_analysis_to_json(analysis, json_path)

        print(f"\n📄 分析报告已生成:")
        print(f"   CSV详情: {csv_path}")
        print(f"   摘要报告: {summary_path}")
        print(f"   JSON数据: {json_path}")

    except Exception as e:
        print(f"❌ 分析失败: {e}")
        logger.exception("分析异常")


def export_analysis_to_json(analysis: EvaluationAnalysis, output_path: Path):
    """导出分析结果为JSON"""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 构建JSON数据
        json_data = {
            "basic_info": {
                "xml_file": analysis.xml_file,
                "analysis_time": analysis.analysis_time.isoformat(),
                "total_duration_ms": analysis.total_duration_ms,
            },
            "scores": {
                "overall_score": analysis.overall_score,
                "phone_score": analysis.phone_score,
                "tone_score": analysis.tone_score,
                "fluency_score": analysis.fluency_score,
                "integrity_score": analysis.integrity_score,
            },
            "statistics": {
                "total_characters": analysis.total_characters,
                "read_characters": analysis.read_characters,
                "correct_characters": analysis.correct_characters,
                "missed_characters": analysis.missed_characters,
                "character_accuracy_rate": analysis.character_accuracy_rate,
                "reading_completion_rate": analysis.reading_completion_rate,
            },
            "characters": [],
        }

        # 字符详情
        for char in analysis.characters:
            char_data = {
                "character": char.character,
                "expected_pinyin": char.expected_pinyin,
                "actual_pinyin": char.actual_pinyin,
                "is_read": char.is_read,
                "is_correct": char.is_correct,
                "duration_ms": char.duration_ms,
                "speech_duration_ms": char.actual_speech_duration,
                "silence_duration_ms": char.total_silence_duration,
                "status": char.status_summary,
                "syllables": [],
            }

            # 音节详情
            for syll in char.syllables:
                syll_data = {
                    "content": syll.content,
                    "symbol": syll.symbol,
                    "type": syll.rec_node_type,
                    "duration_ms": syll.duration_ms,
                    "is_correct": syll.is_correct if syll.is_paper_content else None,
                    "error_summary": syll.error_summary
                    if syll.is_paper_content and not syll.is_correct
                    else None,
                }
                char_data["syllables"].append(syll_data)

            json_data["characters"].append(char_data)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        logger.info(f"JSON数据已导出: {output_path}")

    except Exception as e:
        logger.error(f"导出JSON失败: {e}")


def batch_analyze_xml_files(xml_dir_path: str):
    """批量分析XML文件"""
    xml_dir = Path(xml_dir_path)

    if not xml_dir.exists():
        print(f"❌ 目录不存在: {xml_dir}")
        return

    xml_files = list(xml_dir.glob("*.xml"))
    if not xml_files:
        print(f"❌ 在目录 {xml_dir} 中未找到XML文件")
        return

    print(f"🔍 开始批量分析 {len(xml_files)} 个XML文件")

    analyzer = XfyunXMLAnalyzer()
    results = []

    for xml_file in xml_files:
        try:
            print(f"   正在分析: {xml_file.name}")
            analysis = analyzer.analyze_xml_file(xml_file)
            results.append(analysis)
        except Exception as e:
            print(f"   ❌ 分析失败: {xml_file.name} - {e}")

    if results:
        # 生成批量摘要
        generate_batch_summary(results)
        print(f"\n✅ 批量分析完成，共成功分析 {len(results)} 个文件")
    else:
        print("❌ 没有成功分析任何文件")


def generate_batch_summary(results: List[EvaluationAnalysis]):
    """生成批量分析摘要"""
    output_dir = Path("./batch_xml_analysis")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_path = output_dir / f"batch_summary_{timestamp}.txt"

    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("批量XML分析摘要报告\n")
        f.write("=" * 60 + "\n\n")

        f.write(f"分析文件数: {len(results)}\n")
        f.write(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        if results:
            # 整体统计
            avg_overall = sum(r.overall_score for r in results) / len(results)
            avg_accuracy = sum(r.character_accuracy_rate for r in results) / len(
                results
            )
            avg_completion = sum(r.reading_completion_rate for r in results) / len(
                results
            )

            f.write("📊 整体统计\n")
            f.write("-" * 30 + "\n")
            f.write(f"平均总分: {avg_overall:.2f}\n")
            f.write(f"平均字准确率: {avg_accuracy:.1f}%\n")
            f.write(f"平均完成率: {avg_completion:.1f}%\n\n")

            # 分数分布
            score_ranges = [
                (90, 100, "优秀"),
                (80, 89, "良好"),
                (70, 79, "中等"),
                (60, 69, "及格"),
                (0, 59, "不及格"),
            ]

            f.write("📈 分数分布\n")
            f.write("-" * 30 + "\n")
            for min_score, max_score, level in score_ranges:
                count = len(
                    [r for r in results if min_score <= r.overall_score <= max_score]
                )
                percentage = count / len(results) * 100
                f.write(
                    f"{level}({min_score}-{max_score}): {count}个 ({percentage:.1f}%)\n"
                )
            f.write("\n")

            # 详细列表
            f.write("📋 详细列表\n")
            f.write("-" * 30 + "\n")
            for i, result in enumerate(results, 1):
                f.write(f"{i:2d}. {Path(result.xml_file).stem}\n")
                f.write(
                    f"    总分: {result.overall_score:5.1f} | 准确率: {result.character_accuracy_rate:5.1f}% | 完成率: {result.reading_completion_rate:5.1f}%\n"
                )

    print(f"📄 批量摘要已生成: {summary_path}")


def main():
    """主函数"""
    print("🎙️  科大讯飞XML分析工具")
    print("=" * 60)

    print("请选择操作:")
    print("1. 分析单个XML文件")
    print("2. 批量分析XML文件")
    print("3. 分析当前提供的示例XML")
    print("0. 退出")

    choice = input("\n请选择 (0-3): ").strip()

    if choice == "1":
        xml_file = input("请输入XML文件路径: ").strip()
        analyze_xml_file_demo(xml_file)

    elif choice == "2":
        xml_dir = input("请输入XML文件目录路径: ").strip()
        batch_analyze_xml_files(xml_dir)

    elif choice == "3":
        # 分析当前提供的示例XML
        xml_file = r"ise-demo\ise_python3\results\evaluation_20250615_201641.xml"
        print("🔍 分析示例XML文件" + xml_file)

        # 创建示例XML文件（基于您提供的内容）
        sample_xml_path = Path(xml_file)
        if not sample_xml_path.exists():
            print("❌ 示例XML文件不存在，请先将XML内容保存为文件")
        else:
            analyze_xml_file_demo(str(sample_xml_path))

    elif choice == "0":
        print("👋 再见!")

    else:
        print("❌ 无效选择")


if __name__ == "__main__":
    print("通用XML分析工具")
    main()
