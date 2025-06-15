#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
科大讯飞语音评测增强版客户端
新增功能：
1. 独立的XML结果分析器
2. 修复XML解析逻辑
3. 详细的错误信息解析
4. 可视化分析报告
"""

import asyncio
import json
import base64
import hashlib
import hmac
import logging
import xml.etree.ElementTree as ET
import csv
from datetime import datetime
from email.utils import formatdate
from pathlib import Path
from time import mktime
from typing import Dict, List, Optional, Callable, Any, Union, Tuple
from urllib.parse import urlencode
from dataclasses import dataclass, field
from enum import Enum

import httpx
import websockets
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv
import os

os.chdir(os.path.dirname(__file__))
# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("xfyun_evaluation.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """错误类型枚举"""

    CORRECT = 0  # 正确
    MISSED = 16  # 漏读
    ADDED = 32  # 增读
    REPEATED = 64  # 回读
    REPLACED = 128  # 替换


class PhoneErrorType(Enum):
    """音素错误类型枚举"""

    CORRECT = 0  # 正确
    CONSONANT_ERROR = 1  # 声母错误
    VOWEL_ERROR = 1  # 韵母错误（当is_yun=1时）
    TONE_ERROR = 2  # 调型错误（当is_yun=1时）
    VOWEL_TONE_ERROR = 3  # 韵母和调型都错误（当is_yun=1时）


class NodeType(Enum):
    """节点类型枚举"""

    PAPER = "paper"  # 试卷内容
    SIL = "sil"  # 非试卷内容（静音）
    FIL = "fil"  # 噪音


@dataclass
class XfyunConfig:
    """科大讯飞配置类"""

    app_id: str = field(default_factory=lambda: os.getenv("XFYUN_APP_ID", "e96b71cc"))
    api_secret: str = field(
        default_factory=lambda: os.getenv(
            "XFYUN_API_SECRET", "YTM0YzkxYTk1MWQzOTdkZDg3Zjg0MTQx"
        )
    )
    api_key: str = field(
        default_factory=lambda: os.getenv(
            "XFYUN_API_KEY", "c596bae72326e35a645eca27bf9d235a"
        )
    )
    host: str = "ise-api.xfyun.cn"
    path: str = "/v2/open-ise"

    def __post_init__(self):
        if not all([self.app_id, self.api_secret, self.api_key]):
            raise ValueError("请设置科大讯飞的APP_ID、API_SECRET和API_KEY")

    @property
    def websocket_url(self) -> str:
        return f"wss://{self.host}{self.path}"


class EvaluationParams(BaseModel):
    """语音评测参数模型"""

    category: str = Field(default="read_syllable", description="评测类型")
    group: str = Field(default="pupil", description="评测群体")
    ent: str = Field(default="cn_vip", description="中文评测引擎")
    sub: str = Field(default="ise", description="服务类型")
    tte: str = Field(default="utf-8", description="文本编码")
    ttp_skip: bool = Field(default=True, description="跳过ttp阶段")
    aue: str = Field(default="lame", description="音频格式")
    auf: str = Field(default="audio/L16;rate=16000", description="音频采样率")
    rstcd: str = Field(default="utf8", description="返回结果编码")
    check_type: str = Field(default="common", description="评测松严门限")
    grade: str = Field(default="middle", description="学段参数")
    rst: str = Field(default="entirety", description="评测返回结果控制")
    ise_unite: str = Field(default="1", description="返回结果控制")
    extra_ability: str = Field(
        default="multi_dimension;syll_phone_err_msg", description="拓展能力"
    )


class PhoneResult(BaseModel):
    """音素评测结果模型"""

    content: str = ""  # 音素内容
    beg_pos: int = 0  # 开始位置（帧）
    end_pos: int = 0  # 结束位置（帧）
    time_len: int = 0  # 时长（帧，每帧10ms）
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
    def phone_error_type(self) -> PhoneErrorType:
        """音素错误类型"""
        return PhoneErrorType(self.perr_msg)

    @property
    def node_type(self) -> NodeType:
        """节点类型"""
        try:
            return NodeType(self.rec_node_type)
        except ValueError:
            return NodeType.PAPER

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
    def is_correct(self) -> bool:
        """是否正确"""
        return (
            self.dp_message == 0
            and self.perr_msg == 0
            and self.rec_node_type == "paper"
        )

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


class SyllableResult(BaseModel):
    """音节评测结果模型"""

    content: str = ""  # 音节内容
    symbol: str = ""  # 拼音（带声调）
    beg_pos: int = 0  # 开始位置（帧）
    end_pos: int = 0  # 结束位置（帧）
    time_len: int = 0  # 时长（帧）
    dp_message: int = 0  # 增漏信息
    rec_node_type: str = ""  # 节点类型
    phones: List[PhoneResult] = Field(default_factory=list)

    @property
    def duration_ms(self) -> int:
        """持续时间（毫秒）"""
        return self.time_len * 10

    @property
    def error_type(self) -> ErrorType:
        """错误类型"""
        return ErrorType(self.dp_message)

    @property
    def node_type(self) -> NodeType:
        """节点类型"""
        try:
            return NodeType(self.rec_node_type)
        except ValueError:
            return NodeType.PAPER

    @property
    def is_correct(self) -> bool:
        """音节是否正确"""
        return (
            self.dp_message == 0
            and self.rec_node_type == "paper"
            and all(phone.is_correct for phone in self.phones)
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
            if not phone.is_correct:
                errors.append(f"{phone.content}({phone.error_description})")

        return "; ".join(errors) if errors else "未知错误"


class WordResult(BaseModel):
    """词语评测结果模型"""

    content: str = ""  # 词语内容
    symbol: str = ""  # 拼音
    beg_pos: int = 0  # 开始位置（帧）
    end_pos: int = 0  # 结束位置（帧）
    time_len: int = 0  # 时长（帧）
    syllables: List[SyllableResult] = Field(default_factory=list)

    @property
    def duration_ms(self) -> int:
        """持续时间（毫秒）"""
        return self.time_len * 10

    @property
    def is_correct(self) -> bool:
        """词语是否正确"""
        return all(syll.is_correct for syll in self.syllables)

    @property
    def error_count(self) -> int:
        """错误数量"""
        return len([syll for syll in self.syllables if not syll.is_correct])

    @property
    def accuracy_rate(self) -> float:
        """准确率"""
        if not self.syllables:
            return 0.0
        correct_count = len([syll for syll in self.syllables if syll.is_correct])
        return correct_count / len(self.syllables) * 100


class DetailedEvaluationResult(BaseModel):
    """详细评测结果模型"""

    # 基本信息
    session_id: str = ""
    audio_file: str = ""
    original_text: str = ""
    evaluation_time: datetime = Field(default_factory=datetime.now)

    # 整体分数
    overall_score: float = 0.0
    phone_score: float = 0.0
    tone_score: float = 0.0
    fluency_score: float = 0.0
    accuracy_score: float = 0.0
    integrity_score: float = 0.0
    emotion_score: float = 0.0

    # 状态信息
    is_rejected: bool = False
    except_info: Optional[str] = None
    total_time: int = 0  # 总时长（帧）

    # 详细结果
    words: List[WordResult] = Field(default_factory=list)

    # 原始数据
    raw_xml: str = ""

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    @property
    def total_duration_ms(self) -> int:
        """总时长（毫秒）"""
        return self.total_time * 10

    @property
    def total_syllables(self) -> int:
        """总音节数"""
        return sum(len(word.syllables) for word in self.words)

    @property
    def correct_syllables(self) -> int:
        """正确音节数"""
        return sum(
            len([syll for syll in word.syllables if syll.is_correct])
            for word in self.words
        )

    @property
    def syllable_accuracy_rate(self) -> float:
        """音节准确率"""
        if self.total_syllables == 0:
            return 0.0
        return self.correct_syllables / self.total_syllables * 100

    @property
    def total_phones(self) -> int:
        """总音素数"""
        return sum(len(syll.phones) for word in self.words for syll in word.syllables)

    @property
    def correct_phones(self) -> int:
        """正确音素数"""
        return sum(
            len([phone for phone in syll.phones if phone.is_correct])
            for word in self.words
            for syll in word.syllables
        )

    @property
    def phone_accuracy_rate(self) -> float:
        """音素准确率"""
        if self.total_phones == 0:
            return 0.0
        return self.correct_phones / self.total_phones * 100


class XfyunResultAnalyzer:
    """科大讯飞结果分析器"""

    @staticmethod
    def analyze_xml_file(xml_file_path: Path) -> DetailedEvaluationResult:
        """分析XML文件"""
        try:
            with open(xml_file_path, "r", encoding="utf-8") as f:
                xml_content = f.read()

            return XfyunResultAnalyzer.analyze_xml_content(xml_content)

        except Exception as e:
            logger.error(f"分析XML文件失败: {e}")
            raise

    @staticmethod
    def analyze_xml_content(xml_content: str) -> DetailedEvaluationResult:
        """分析XML内容"""
        result = DetailedEvaluationResult()
        result.raw_xml = xml_content

        try:
            root = ET.fromstring(xml_content)

            # 查找评测结果节点
            eval_node = (
                root.find(".//read_syllable")
                or root.find(".//read_word")
                or root.find(".//read_sentence")
                or root.find(".//read_chapter")
            )

            if eval_node is not None:
                # 解析整体分数
                result.overall_score = float(eval_node.get("total_score", 0))
                result.phone_score = float(eval_node.get("phone_score", 0))
                result.tone_score = float(eval_node.get("tone_score", 0))
                result.fluency_score = float(eval_node.get("fluency_score", 0))
                result.accuracy_score = float(eval_node.get("accuracy_score", 0))
                result.integrity_score = float(eval_node.get("integrity_score", 0))
                result.emotion_score = float(eval_node.get("emotion_score", 0))

                # 解析状态信息
                result.is_rejected = (
                    eval_node.get("is_rejected", "false").lower() == "true"
                )
                result.except_info = eval_node.get("except_info")
                result.total_time = int(eval_node.get("time_len", 0))

                # 解析词语详情
                result.words = XfyunResultAnalyzer._parse_words(eval_node)

            logger.info(f"XML解析完成，总分: {result.overall_score}")

        except ET.ParseError as e:
            logger.error(f"XML解析失败: {e}")
            raise
        except Exception as e:
            logger.error(f"结果解析过程中发生错误: {e}")
            raise

        return result

    @staticmethod
    def _parse_words(eval_node) -> List[WordResult]:
        """解析词语节点"""
        words = []

        for word_node in eval_node.findall(".//word"):
            word = WordResult(
                content=word_node.get("content", ""),
                symbol=word_node.get("symbol", ""),
                beg_pos=int(word_node.get("beg_pos", 0)),
                end_pos=int(word_node.get("end_pos", 0)),
                time_len=int(word_node.get("time_len", 0)),
            )

            # 解析音节
            word.syllables = XfyunResultAnalyzer._parse_syllables(word_node)
            words.append(word)

        return words

    @staticmethod
    def _parse_syllables(word_node) -> List[SyllableResult]:
        """解析音节节点"""
        syllables = []

        for syll_node in word_node.findall(".//syll"):
            syllable = SyllableResult(
                content=syll_node.get("content", ""),
                symbol=syll_node.get("symbol", ""),
                beg_pos=int(syll_node.get("beg_pos", 0)),
                end_pos=int(syll_node.get("end_pos", 0)),
                time_len=int(syll_node.get("time_len", 0)),
                dp_message=int(syll_node.get("dp_message", 0)),
                rec_node_type=syll_node.get("rec_node_type", ""),
            )

            # 解析音素
            syllable.phones = XfyunResultAnalyzer._parse_phones(syll_node)
            syllables.append(syllable)

        return syllables

    @staticmethod
    def _parse_phones(syll_node) -> List[PhoneResult]:
        """解析音素节点"""
        phones = []

        for phone_node in syll_node.findall(".//phone"):
            phone = PhoneResult(
                content=phone_node.get("content", ""),
                beg_pos=int(phone_node.get("beg_pos", 0)),
                end_pos=int(phone_node.get("end_pos", 0)),
                time_len=int(phone_node.get("time_len", 0)),
                dp_message=int(phone_node.get("dp_message", 0)),
                perr_msg=int(phone_node.get("perr_msg", 0)),
                perr_level_msg=int(phone_node.get("perr_level_msg", 0)),
                is_yun=int(phone_node.get("is_yun", 0)),
                rec_node_type=phone_node.get("rec_node_type", ""),
                mono_tone=phone_node.get("mono_tone"),
            )
            phones.append(phone)

        return phones


class EvaluationAnalytics:
    """评测分析工具"""

    @staticmethod
    def generate_detailed_report(
        result: DetailedEvaluationResult, output_path: Path
    ) -> bool:
        """生成详细分析报告"""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write("科大讯飞语音评测详细分析报告\n")
                f.write("=" * 60 + "\n\n")

                # 基本信息
                f.write("📋 基本信息\n")
                f.write("-" * 30 + "\n")
                f.write(f"音频文件: {result.audio_file}\n")
                f.write(f"原始文本: {result.original_text}\n")
                f.write(
                    f"评测时间: {result.evaluation_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                f.write(f"会话ID: {result.session_id}\n")
                f.write(f"总时长: {result.total_duration_ms}ms\n")

                if result.is_rejected:
                    f.write(f"⚠️  评测状态: 被拒绝\n")
                if result.except_info:
                    f.write(f"异常信息: {result.except_info}\n")
                f.write("\n")

                # 整体分数
                f.write("📊 整体分数\n")
                f.write("-" * 30 + "\n")
                f.write(f"总分: {result.overall_score:.2f}\n")
                f.write(f"声韵分: {result.phone_score:.2f}\n")
                f.write(f"调型分: {result.tone_score:.2f}\n")
                f.write(f"流畅度分: {result.fluency_score:.2f}\n")
                f.write(f"准确度分: {result.accuracy_score:.2f}\n")
                f.write(f"完整度分: {result.integrity_score:.2f}\n")
                f.write(f"情感分: {result.emotion_score:.2f}\n")
                f.write("\n")

                # 统计信息
                f.write("📈 统计信息\n")
                f.write("-" * 30 + "\n")
                f.write(f"词语总数: {len(result.words)}\n")
                f.write(f"音节总数: {result.total_syllables}\n")
                f.write(f"正确音节数: {result.correct_syllables}\n")
                f.write(f"音节准确率: {result.syllable_accuracy_rate:.1f}%\n")
                f.write(f"音素总数: {result.total_phones}\n")
                f.write(f"正确音素数: {result.correct_phones}\n")
                f.write(f"音素准确率: {result.phone_accuracy_rate:.1f}%\n")
                f.write("\n")

                # 详细分析
                f.write("🔍 详细分析\n")
                f.write("-" * 30 + "\n")

                for i, word in enumerate(result.words, 1):
                    f.write(f"\n{i}. 词语: {word.content}\n")
                    f.write(f"   拼音: {word.symbol}\n")
                    f.write(f"   时长: {word.duration_ms}ms\n")
                    f.write(f"   状态: {'✅ 正确' if word.is_correct else '❌ 错误'}\n")
                    f.write(f"   准确率: {word.accuracy_rate:.1f}%\n")

                    for j, syll in enumerate(word.syllables, 1):
                        f.write(f"   {i}.{j} 音节: {syll.content} [{syll.symbol}]\n")
                        f.write(f"        时长: {syll.duration_ms}ms\n")
                        f.write(
                            f"        状态: {'✅ 正确' if syll.is_correct else '❌ 错误'}\n"
                        )
                        if not syll.is_correct:
                            f.write(f"        错误: {syll.error_summary}\n")

                        # 音素详情
                        for k, phone in enumerate(syll.phones, 1):
                            status = "✅" if phone.is_correct else "❌"
                            phone_type = "韵母" if phone.is_yun else "声母"
                            f.write(
                                f"        {i}.{j}.{k} {phone_type}: {phone.content} {status}\n"
                            )

                            if not phone.is_correct:
                                f.write(
                                    f"             错误: {phone.error_description}\n"
                                )
                                f.write(
                                    f"             置信度: {phone.confidence_level}\n"
                                )

                # 错误统计
                error_stats = EvaluationAnalytics._calculate_error_stats(result)
                if error_stats:
                    f.write("\n📉 错误统计\n")
                    f.write("-" * 30 + "\n")
                    for error_type, count in error_stats.items():
                        f.write(f"{error_type}: {count}次\n")

                # 时间分析
                f.write("\n⏱️  时间分析\n")
                f.write("-" * 30 + "\n")
                if result.words:
                    avg_word_time = sum(w.duration_ms for w in result.words) / len(
                        result.words
                    )
                    f.write(f"平均词语时长: {avg_word_time:.0f}ms\n")

                if result.total_syllables > 0:
                    avg_syll_time = result.total_duration_ms / result.total_syllables
                    f.write(f"平均音节时长: {avg_syll_time:.0f}ms\n")

            logger.info(f"详细分析报告已生成: {output_path}")
            return True

        except Exception as e:
            logger.error(f"生成详细报告失败: {e}")
            return False

    @staticmethod
    def _calculate_error_stats(result: DetailedEvaluationResult) -> Dict[str, int]:
        """计算错误统计"""
        error_stats = {}

        for word in result.words:
            for syll in word.syllables:
                for phone in syll.phones:
                    if not phone.is_correct:
                        error_desc = phone.error_description
                        error_stats[error_desc] = error_stats.get(error_desc, 0) + 1

        # 按错误次数排序
        return dict(sorted(error_stats.items(), key=lambda x: x[1], reverse=True))

    @staticmethod
    def export_detailed_csv(
        result: DetailedEvaluationResult, output_path: Path
    ) -> bool:
        """导出详细CSV格式"""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)

                # 写入表头
                headers = [
                    "词语序号",
                    "词语内容",
                    "词语拼音",
                    "词语时长(ms)",
                    "词语状态",
                    "音节序号",
                    "音节内容",
                    "音节拼音",
                    "音节时长(ms)",
                    "音节状态",
                    "音节错误",
                    "音素序号",
                    "音素内容",
                    "音素类型",
                    "音素时长(ms)",
                    "音素状态",
                    "音素错误",
                    "置信度",
                    "开始位置(帧)",
                    "结束位置(帧)",
                ]
                writer.writerow(headers)

                # 写入数据
                for word_idx, word in enumerate(result.words, 1):
                    for syll_idx, syll in enumerate(word.syllables, 1):
                        for phone_idx, phone in enumerate(syll.phones, 1):
                            row = [
                                word_idx,
                                word.content,
                                word.symbol,
                                word.duration_ms,
                                "正确" if word.is_correct else "错误",
                                syll_idx,
                                syll.content,
                                syll.symbol,
                                syll.duration_ms,
                                "正确" if syll.is_correct else "错误",
                                syll.error_summary if not syll.is_correct else "",
                                phone_idx,
                                phone.content,
                                "韵母" if phone.is_yun else "声母",
                                phone.duration_ms,
                                "正确" if phone.is_correct else "错误",
                                phone.error_description if not phone.is_correct else "",
                                phone.confidence_level,
                                phone.beg_pos,
                                phone.end_pos,
                            ]
                            writer.writerow(row)

            logger.info(f"详细CSV已导出: {output_path}")
            return True

        except Exception as e:
            logger.error(f"导出详细CSV失败: {e}")
            return False

    @staticmethod
    def generate_visualization_data(result: DetailedEvaluationResult) -> Dict[str, Any]:
        """生成可视化数据"""
        viz_data = {
            "timeline": [],
            "error_distribution": {},
            "accuracy_by_position": [],
            "phone_analysis": {"consonants": {}, "vowels": {}},
            "tone_analysis": {},
        }

        # 时间轴数据
        for word_idx, word in enumerate(result.words):
            for syll_idx, syll in enumerate(word.syllables):
                for phone_idx, phone in enumerate(syll.phones):
                    viz_data["timeline"].append(
                        {
                            "start_ms": phone.beg_pos * 10,
                            "end_ms": phone.end_pos * 10,
                            "content": phone.content,
                            "type": "韵母" if phone.is_yun else "声母",
                            "is_correct": phone.is_correct,
                            "error": phone.error_description
                            if not phone.is_correct
                            else None,
                            "word_index": word_idx,
                            "syllable_index": syll_idx,
                            "phone_index": phone_idx,
                        }
                    )

        # 错误分布
        for word in result.words:
            for syll in word.syllables:
                for phone in syll.phones:
                    if not phone.is_correct:
                        error_type = phone.error_description
                        viz_data["error_distribution"][error_type] = (
                            viz_data["error_distribution"].get(error_type, 0) + 1
                        )

        # 位置准确率
        for i, word in enumerate(result.words):
            accuracy = word.accuracy_rate
            viz_data["accuracy_by_position"].append(
                {"position": i + 1, "word": word.content, "accuracy": accuracy}
            )

        # 音素分析
        for word in result.words:
            for syll in word.syllables:
                for phone in syll.phones:
                    phone_type = "vowels" if phone.is_yun else "consonants"
                    phone_content = phone.content

                    if phone_content not in viz_data["phone_analysis"][phone_type]:
                        viz_data["phone_analysis"][phone_type][phone_content] = {
                            "total": 0,
                            "correct": 0,
                            "errors": [],
                        }

                    viz_data["phone_analysis"][phone_type][phone_content]["total"] += 1
                    if phone.is_correct:
                        viz_data["phone_analysis"][phone_type][phone_content][
                            "correct"
                        ] += 1
                    else:
                        viz_data["phone_analysis"][phone_type][phone_content][
                            "errors"
                        ].append(phone.error_description)

        # 声调分析
        for word in result.words:
            for syll in word.syllables:
                if syll.tone is not None:
                    tone = syll.tone
                    if tone not in viz_data["tone_analysis"]:
                        viz_data["tone_analysis"][tone] = {"total": 0, "correct": 0}

                    viz_data["tone_analysis"][tone]["total"] += 1
                    if syll.is_correct:
                        viz_data["tone_analysis"][tone]["correct"] += 1

        return viz_data


class EnhancedXfyunEvaluator:
    """增强版科大讯飞评测器 - 集成了分析功能"""

    def __init__(self, config: XfyunConfig):
        self.config = config
        self.analyzer = XfyunResultAnalyzer()
        self.analytics = EvaluationAnalytics()

    def analyze_existing_xml(
        self, xml_path: Path, output_dir: Path = None
    ) -> DetailedEvaluationResult:
        """分析现有的XML文件"""
        if output_dir is None:
            output_dir = Path("./analysis_results")

        logger.info(f"开始分析XML文件: {xml_path}")

        # 解析XML
        result = self.analyzer.analyze_xml_file(xml_path)
        result.audio_file = xml_path.stem  # 使用文件名作为音频文件标识

        # 生成分析报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 详细报告
        report_path = output_dir / f"analysis_report_{timestamp}.txt"
        self.analytics.generate_detailed_report(result, report_path)

        # 详细CSV
        csv_path = output_dir / f"analysis_details_{timestamp}.csv"
        self.analytics.export_detailed_csv(result, csv_path)

        # 可视化数据
        viz_data = self.analytics.generate_visualization_data(result)
        viz_path = output_dir / f"visualization_data_{timestamp}.json"
        with open(viz_path, "w", encoding="utf-8") as f:
            json.dump(viz_data, f, ensure_ascii=False, indent=2)

        logger.info(f"分析完成，结果保存到: {output_dir}")
        return result

    def batch_analyze_xmls(
        self, xml_dir: Path, output_dir: Path = None
    ) -> List[DetailedEvaluationResult]:
        """批量分析XML文件"""
        if output_dir is None:
            output_dir = Path("./batch_analysis_results")

        xml_files = list(xml_dir.glob("*.xml"))
        if not xml_files:
            logger.warning(f"在目录 {xml_dir} 中未找到XML文件")
            return []

        logger.info(f"开始批量分析 {len(xml_files)} 个XML文件")

        results = []
        for xml_file in xml_files:
            try:
                result = self.analyzer.analyze_xml_file(xml_file)
                result.audio_file = xml_file.stem
                results.append(result)
                logger.info(f"已分析: {xml_file.name}")
            except Exception as e:
                logger.error(f"分析文件 {xml_file.name} 失败: {e}")

        if results:
            # 生成批量分析报告
            self._generate_batch_report(results, output_dir)

        logger.info(f"批量分析完成，共分析 {len(results)} 个文件")
        return results

    def _generate_batch_report(
        self, results: List[DetailedEvaluationResult], output_dir: Path
    ):
        """生成批量分析报告"""
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 汇总统计报告
        summary_path = output_dir / f"batch_summary_{timestamp}.txt"
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write("批量XML分析汇总报告\n")
            f.write("=" * 50 + "\n\n")

            f.write(f"分析文件总数: {len(results)}\n")
            f.write(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # 整体统计
            if results:
                avg_overall = sum(r.overall_score for r in results) / len(results)
                avg_phone = sum(r.phone_score for r in results) / len(results)
                avg_tone = sum(r.tone_score for r in results) / len(results)
                avg_syllable_acc = sum(r.syllable_accuracy_rate for r in results) / len(
                    results
                )
                avg_phone_acc = sum(r.phone_accuracy_rate for r in results) / len(
                    results
                )

                f.write("📊 整体统计\n")
                f.write("-" * 30 + "\n")
                f.write(f"平均总分: {avg_overall:.2f}\n")
                f.write(f"平均声韵分: {avg_phone:.2f}\n")
                f.write(f"平均调型分: {avg_tone:.2f}\n")
                f.write(f"平均音节准确率: {avg_syllable_acc:.1f}%\n")
                f.write(f"平均音素准确率: {avg_phone_acc:.1f}%\n\n")

                # 分数分布
                score_ranges = {
                    "90-100": 0,
                    "80-89": 0,
                    "70-79": 0,
                    "60-69": 0,
                    "<60": 0,
                }
                for result in results:
                    score = result.overall_score
                    if score >= 90:
                        score_ranges["90-100"] += 1
                    elif score >= 80:
                        score_ranges["80-89"] += 1
                    elif score >= 70:
                        score_ranges["70-79"] += 1
                    elif score >= 60:
                        score_ranges["60-69"] += 1
                    else:
                        score_ranges["<60"] += 1

                f.write("📈 分数分布\n")
                f.write("-" * 30 + "\n")
                for range_name, count in score_ranges.items():
                    percentage = count / len(results) * 100
                    f.write(f"{range_name}分: {count}个 ({percentage:.1f}%)\n")
                f.write("\n")

                # 常见错误
                all_errors = {}
                for result in results:
                    error_stats = self.analytics._calculate_error_stats(result)
                    for error_type, count in error_stats.items():
                        all_errors[error_type] = all_errors.get(error_type, 0) + count

                if all_errors:
                    f.write("❌ 常见错误排行\n")
                    f.write("-" * 30 + "\n")
                    sorted_errors = sorted(
                        all_errors.items(), key=lambda x: x[1], reverse=True
                    )
                    for i, (error_type, count) in enumerate(sorted_errors[:10], 1):
                        f.write(f"{i:2d}. {error_type}: {count}次\n")
                    f.write("\n")

            # 个别结果
            f.write("📋 个别结果\n")
            f.write("-" * 30 + "\n")
            for i, result in enumerate(results, 1):
                f.write(f"{i:3d}. {result.audio_file}\n")
                f.write(
                    f"     总分: {result.overall_score:5.1f} | 音节准确率: {result.syllable_accuracy_rate:5.1f}%\n"
                )
                if result.is_rejected:
                    f.write(f"     状态: 被拒绝\n")
                if result.except_info:
                    f.write(f"     异常: {result.except_info}\n")

        # 批量详细CSV
        batch_csv_path = output_dir / f"batch_details_{timestamp}.csv"
        with open(batch_csv_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)

            # 表头
            headers = [
                "文件名",
                "总分",
                "声韵分",
                "调型分",
                "流畅度分",
                "准确度分",
                "完整度分",
                "词语总数",
                "音节总数",
                "正确音节数",
                "音节准确率",
                "音素总数",
                "正确音素数",
                "音素准确率",
                "总时长(ms)",
                "是否被拒",
                "异常信息",
            ]
            writer.writerow(headers)

            # 数据
            for result in results:
                row = [
                    result.audio_file,
                    result.overall_score,
                    result.phone_score,
                    result.tone_score,
                    result.fluency_score,
                    result.accuracy_score,
                    result.integrity_score,
                    len(result.words),
                    result.total_syllables,
                    result.correct_syllables,
                    result.syllable_accuracy_rate,
                    result.total_phones,
                    result.correct_phones,
                    result.phone_accuracy_rate,
                    result.total_duration_ms,
                    "是" if result.is_rejected else "否",
                    result.except_info or "",
                ]
                writer.writerow(row)

        logger.info(f"批量分析报告已生成: {output_dir}")


def print_detailed_result(result: DetailedEvaluationResult):
    """打印详细评测结果"""
    print("\n" + "=" * 70)
    print("📊 科大讯飞语音评测详细分析结果")
    print("=" * 70)

    # 基本信息
    print(f"🎵 音频文件: {result.audio_file}")
    print(f"📝 原始文本: {result.original_text}")
    print(f"🕐 评测时间: {result.evaluation_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️  总时长: {result.total_duration_ms}ms")

    if result.is_rejected:
        print("⚠️  评测状态: 被拒绝")
    if result.except_info:
        print(f"❗ 异常信息: {result.except_info}")

    # 整体分数
    print(f"\n📈 整体分数")
    print("-" * 40)
    print(f"总分: {result.overall_score:6.2f} | 声韵分: {result.phone_score:6.2f}")
    print(f"调型分: {result.tone_score:6.2f} | 流畅度: {result.fluency_score:6.2f}")
    print(
        f"准确度: {result.accuracy_score:6.2f} | 完整度: {result.integrity_score:6.2f}"
    )

    # 统计信息
    print(f"\n📊 统计信息")
    print("-" * 40)
    print(
        f"词语数: {len(result.words):3d} | 音节数: {result.total_syllables:3d} | 音素数: {result.total_phones:3d}"
    )
    print(
        f"音节准确率: {result.syllable_accuracy_rate:5.1f}% | 音素准确率: {result.phone_accuracy_rate:5.1f}%"
    )

    # 详细分析
    print(f"\n🔍 详细分析")
    print("-" * 70)

    for word_idx, word in enumerate(result.words, 1):
        word_status = "✅" if word.is_correct else "❌"
        print(
            f"\n{word_idx:2d}. 词语: {word.content:4s} [{word.symbol:8s}] {word_status}"
        )
        print(f"    时长: {word.duration_ms:4d}ms | 准确率: {word.accuracy_rate:5.1f}%")

        for syll_idx, syll in enumerate(word.syllables, 1):
            syll_status = "✅" if syll.is_correct else "❌"
            tone_str = f"声调{syll.tone}" if syll.tone is not None else "无调"
            print(
                f"    {word_idx}.{syll_idx} 音节: {syll.content:3s} [{syll.pinyin_without_tone}{tone_str}] {syll_status}"
            )

            if not syll.is_correct:
                print(f"        ❌ 错误: {syll.error_summary}")

            # 音素详情
            phone_line = "        音素: "
            for phone_idx, phone in enumerate(syll.phones):
                phone_status = "✅" if phone.is_correct else "❌"
                phone_type = "韵" if phone.is_yun else "声"
                phone_line += f"{phone.content}({phone_type}){phone_status} "
            print(phone_line)

            # 显示错误的音素详情
            for phone in syll.phones:
                if not phone.is_correct:
                    print(
                        f"          ❌ {phone.content}: {phone.error_description} (置信度:{phone.confidence_level})"
                    )


async def demo_xml_analysis():
    """演示XML分析功能"""
    print("🔬 XML分析演示")
    print("=" * 50)

    # 创建分析器
    config = XfyunConfig()
    evaluator = EnhancedXfyunEvaluator(config)

    # 查找XML文件
    xml_files = list(Path(".").glob("*.xml"))

    if not xml_files:
        print("❌ 当前目录中未找到XML文件")
        print("请将XML文件放在当前目录中再运行分析")
        return

    print(f"✅ 找到 {len(xml_files)} 个XML文件:")
    for i, xml_file in enumerate(xml_files, 1):
        print(f"   {i}. {xml_file.name}")

    # 选择分析模式
    print("\n请选择分析模式:")
    print("1. 分析单个XML文件")
    print("2. 批量分析所有XML文件")

    choice = input("请选择 (1-2): ").strip()

    if choice == "1":
        # 单文件分析
        if len(xml_files) == 1:
            selected_file = xml_files[0]
        else:
            file_index = int(input(f"请选择文件编号 (1-{len(xml_files)}): ")) - 1
            selected_file = xml_files[file_index]

        print(f"\n🔍 正在分析: {selected_file.name}")

        result = evaluator.analyze_existing_xml(selected_file)

        # 显示详细结果
        print_detailed_result(result)

        print(f"\n📄 分析报告已生成在: ./analysis_results/")

    elif choice == "2":
        # 批量分析
        print(f"\n🔍 正在批量分析 {len(xml_files)} 个文件...")

        results = evaluator.batch_analyze_xmls(Path("."))

        if results:
            print(f"\n✅ 批量分析完成！")
            print(f"总文件数: {len(results)}")
            print(
                f"平均总分: {sum(r.overall_score for r in results) / len(results):.2f}"
            )
            print(
                f"平均音节准确率: {sum(r.syllable_accuracy_rate for r in results) / len(results):.1f}%"
            )
            print(f"\n📄 批量分析报告已生成在: ./batch_analysis_results/")
        else:
            print("❌ 批量分析失败")

    else:
        print("❌ 无效选择")


def main():
    """主函数"""
    print("🎙️  科大讯飞语音评测增强版客户端")
    print("支持XML分析和详细解析")
    print("=" * 60)

    print("1. XML结果分析演示")
    print("2. 在线评测演示")
    print("0. 退出")

    choice = input("\n请选择功能 (0-2): ").strip()

    if choice == "1":
        asyncio.run(demo_xml_analysis())
    elif choice == "2":
        print("在线评测功能请参考之前的示例代码")
    elif choice == "0":
        print("👋 再见!")
    else:
        print("❌ 无效选择")


def analyze_single_xml(xml_file="results/evaluation_20250615_201641.xml"):
    """示例1: 分析单个XML文件"""
    print("📋 分析单个XML文件")
    print("-" * 40)

    # 方法1: 直接使用分析器
    analyzer = XfyunResultAnalyzer()

    xml_file = Path(xml_file)  # 替换为实际的XML文件路径

    if xml_file.exists():
        # 分析XML文件
        result = analyzer.analyze_xml_file(xml_file)

        # 打印基本信息
        print(f"文件: {xml_file.name}")
        print(f"总分: {result.overall_score:.2f}")
        print(f"音节准确率: {result.syllable_accuracy_rate:.1f}%")
        print(f"音素准确率: {result.phone_accuracy_rate:.1f}%")

        # 显示词语详情
        for i, word in enumerate(result.words, 1):
            print(f"\n{i}. {word.content} [{word.symbol}]")
            print(f"   准确率: {word.accuracy_rate:.1f}%")
            print(f"   时长: {word.duration_ms}ms")

            for j, syll in enumerate(word.syllables, 1):
                status = "✅" if syll.is_correct else "❌"
                print(f"   {i}.{j} {syll.content} [{syll.symbol}] {status}")

                if not syll.is_correct:
                    print(f"       错误: {syll.error_summary}")
    else:
        print(f"❌ 文件不存在: {xml_file}")


if __name__ == "__main__":
    try:
        # main()
        analyze_single_xml()
    except KeyboardInterrupt:
        print("\n👋 程序被用户中断")
    except Exception as e:
        print(f"❌ 程序运行出错: {e}")
        logger.exception("程序异常")
