#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
科大讯飞语音评测SDK封装
基于WebSocket接口实现语音评测功能
"""

import asyncio
import json
import base64
import hashlib
import hmac
import ssl
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Callable
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time

import websockets
from pydantic import BaseModel, Field

# 配置日志
logger = logging.getLogger(__name__)


class XfyunConfig(BaseModel):
    """讯飞配置"""
    app_id: str = Field(..., description="应用ID")
    api_key: str = Field(..., description="API Key")
    api_secret: str = Field(..., description="API Secret")
    host: str = Field(default="ise-api.xfyun.cn", description="API主机")
    ws_url: str = Field(default="ws://ise-api.xfyun.cn/v2/open-ise", description="WebSocket URL")


class EvaluationRequest(BaseModel):
    """评测请求参数"""
    category: str = Field(default="read_syllable", description="评测类型")
    text: str = Field(..., description="待评测文本")
    group: str = Field(default="pupil", description="用户群体")
    language: str = Field(default="cn_vip", description="语言类型")
    audio_format: str = Field(default="raw", description="音频格式")
    sample_rate: int = Field(default=16000, description="采样率")


class EvaluationResponse(BaseModel):
    """评测响应结果"""
    success: bool = Field(default=False, description="是否成功")
    message: str = Field(default="", description="消息")
    total_score: float = Field(default=0.0, description="总分")
    phone_score: float = Field(default=0.0, description="声韵分")
    tone_score: float = Field(default=0.0, description="调型分")
    fluency_score: float = Field(default=0.0, description="流畅度")
    integrity_score: float = Field(default=0.0, description="完整度")
    xml_result: str = Field(default="", description="详细XML结果")
    analysis_time: datetime = Field(default_factory=datetime.now, description="分析时间")


class XfyunSpeechEvaluationSDK:
    """科大讯飞语音评测SDK"""
    
    def __init__(self, config: XfyunConfig):
        self.config = config
        self.websocket = None
        self.evaluation_result = None
        self.is_connected = False
    
    def _generate_auth_url(self) -> str:
        """生成鉴权URL"""
        now_time = datetime.now()
        now_date = format_date_time(time.mktime(now_time.timetuple()))
        
        # 构建签名原始字符串
        signature_origin = f"host: {self.config.host}\n"
        signature_origin += f"date: {now_date}\n"
        signature_origin += "GET /v2/open-ise HTTP/1.1"
        
        # HMAC-SHA256签名
        signature_sha = hmac.new(
            self.config.api_secret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode('utf-8')
        
        # 构建authorization
        authorization_origin = (
            f'api_key="{self.config.api_key}", '
            f'algorithm="hmac-sha256", '
            f'headers="host date request-line", '
            f'signature="{signature_sha_base64}"'
        )
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')
        
        # 构建认证参数
        auth_params = {
            "authorization": authorization,
            "date": now_date,
            "host": self.config.host,
        }
        
        return f"{self.config.ws_url}?{urlencode(auth_params)}"
    
    async def evaluate_audio_file(
        self, 
        audio_file_path: Path, 
        request: EvaluationRequest,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> EvaluationResponse:
        """评测音频文件"""
        try:
            if progress_callback:
                progress_callback("开始连接语音评测服务...")
            
            # 生成认证URL
            auth_url = self._generate_auth_url()
            
            # 建立WebSocket连接
            async with websockets.connect(
                auth_url,
                ssl=ssl.create_default_context() if auth_url.startswith('wss') else None,
                ping_interval=None,
                ping_timeout=None
            ) as websocket:
                self.websocket = websocket
                self.is_connected = True
                self.evaluation_result = None
                
                if progress_callback:
                    progress_callback("连接成功，开始发送参数...")
                
                # 发送评测参数
                await self._send_parameters(request)
                
                if progress_callback:
                    progress_callback("开始上传音频数据...")
                
                # 发送音频数据
                await self._send_audio_file(audio_file_path, progress_callback)
                
                if progress_callback:
                    progress_callback("等待评测结果...")
                
                # 等待结果
                result = await self._wait_for_result()
                
                if progress_callback:
                    progress_callback("评测完成！")
                
                return result
                
        except Exception as e:
            logger.error(f"语音评测失败: {str(e)}")
            return EvaluationResponse(
                success=False,
                message=f"评测失败: {str(e)}"
            )
        finally:
            self.is_connected = False
    
    async def evaluate_audio_blob(
        self, 
        audio_data: bytes, 
        request: EvaluationRequest,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> EvaluationResponse:
        """评测音频数据"""
        try:
            if progress_callback:
                progress_callback("开始连接语音评测服务...")
            
            # 生成认证URL
            auth_url = self._generate_auth_url()
            
            # 建立WebSocket连接
            async with websockets.connect(
                auth_url,
                ssl=ssl.create_default_context() if auth_url.startswith('wss') else None,
                ping_interval=None,
                ping_timeout=None
            ) as websocket:
                self.websocket = websocket
                self.is_connected = True
                self.evaluation_result = None
                
                if progress_callback:
                    progress_callback("连接成功，开始发送参数...")
                
                # 发送评测参数
                await self._send_parameters(request)
                
                if progress_callback:
                    progress_callback("开始上传音频数据...")
                
                # 发送音频数据
                await self._send_audio_data(audio_data, progress_callback)
                
                if progress_callback:
                    progress_callback("等待评测结果...")
                
                # 等待结果
                result = await self._wait_for_result()
                
                if progress_callback:
                    progress_callback("评测完成！")
                
                return result
                
        except Exception as e:
            logger.error(f"语音评测失败: {str(e)}")
            return EvaluationResponse(
                success=False,
                message=f"评测失败: {str(e)}"
            )
        finally:
            self.is_connected = False
    
    async def _send_parameters(self, request: EvaluationRequest):
        """发送评测参数"""
        # 构建参数数据
        param_data = {
            "common": {
                "app_id": self.config.app_id
            },
            "business": {
                "category": request.category,
                "rstcd": "utf8",
                "sub": "ise",
                "group": request.group,
                "ent": request.language,
                "tte": "utf-8",
                "cmd": "ssb",
                "auf": f"audio/L16;rate={request.sample_rate}",
                "aue": request.audio_format,
                "text": "\ufeff" + request.text,
                "extra_ability": "multi_dimension",
                "rst": "entirety",
                "ise_unite": "1"
            },
            "data": {
                "status": 0,
                "data": ""
            }
        }
        
        # 发送参数
        await self.websocket.send(json.dumps(param_data))
        logger.debug("评测参数已发送")
    
    async def _send_audio_file(self, audio_file_path: Path, progress_callback: Optional[Callable]):
        """发送音频文件"""
        frame_size = 1280  # 每帧大小
        
        with open(audio_file_path, 'rb') as audio_file:
            audio_data = audio_file.read()
        
        await self._send_audio_data(audio_data, progress_callback)
    
    async def _send_audio_data(self, audio_data: bytes, progress_callback: Optional[Callable]):
        """发送音频数据"""
        frame_size = 1280  # 每帧大小
        total_size = len(audio_data)
        sent_size = 0
        
        # 分帧发送音频
        for i in range(0, len(audio_data), frame_size):
            chunk = audio_data[i:i + frame_size]
            is_last_frame = (i + frame_size >= len(audio_data))
            
            # 确定音频状态
            if i == 0:
                aus = 1  # 第一帧
            elif is_last_frame:
                aus = 4  # 最后一帧
            else:
                aus = 2  # 中间帧
            
            # 构建音频数据包
            audio_packet = {
                "business": {
                    "cmd": "auw",
                    "aus": aus,
                    "aue": "raw"
                },
                "data": {
                    "status": 2 if is_last_frame else 1,
                    "data": base64.b64encode(chunk).decode('utf-8')
                }
            }
            
            # 发送数据包
            await self.websocket.send(json.dumps(audio_packet))
            
            # 更新进度
            sent_size += len(chunk)
            if progress_callback:
                progress = min(100, int(sent_size / total_size * 100))
                progress_callback(f"上传进度: {progress}%")
            
            # 适当延时，避免发送过快
            await asyncio.sleep(0.04)
        
        logger.debug("音频数据发送完成")
    
    async def _wait_for_result(self, timeout: int = 30) -> EvaluationResponse:
        """等待评测结果"""
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    # 等待消息
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=5.0)
                    result_data = json.loads(message)
                    
                    logger.debug(f"收到消息: {result_data}")
                    
                    # 检查是否是最终结果
                    if result_data.get("data", {}).get("status") == 2:
                        # 解析结果
                        return self._parse_result(result_data)
                    
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"接收消息失败: {str(e)}")
                    continue
            
            # 超时
            return EvaluationResponse(
                success=False,
                message="等待评测结果超时"
            )
            
        except Exception as e:
            logger.error(f"等待结果时发生错误: {str(e)}")
            return EvaluationResponse(
                success=False,
                message=f"等待结果失败: {str(e)}"
            )
    
    def _parse_result(self, result_data: Dict) -> EvaluationResponse:
        """解析评测结果"""
        try:
            # 获取XML结果
            xml_data = result_data.get("data", {}).get("data", "")
            if xml_data:
                xml_result = base64.b64decode(xml_data).decode('utf-8')
            else:
                xml_result = ""
            
            # 基础解析（从XML中提取分数信息）
            total_score = 0.0
            phone_score = 0.0
            tone_score = 0.0
            fluency_score = 0.0
            integrity_score = 0.0
            
            if xml_result:
                # 简单的XML解析来获取分数
                import xml.etree.ElementTree as ET
                try:
                    root = ET.fromstring(xml_result)
                    # 查找评测结果节点
                    read_syllable = root.find(".//rec_paper/read_syllable")
                    if read_syllable is not None:
                        total_score = float(read_syllable.get("total_score", 0))
                        phone_score = float(read_syllable.get("phone_score", 0))
                        tone_score = float(read_syllable.get("tone_score", 0))
                        fluency_score = float(read_syllable.get("fluency_score", 0))
                        integrity_score = float(read_syllable.get("integrity_score", 0))
                except ET.ParseError as e:
                    logger.warning(f"XML解析失败: {e}")
            
            return EvaluationResponse(
                success=True,
                message="评测成功",
                total_score=total_score,
                phone_score=phone_score,
                tone_score=tone_score,
                fluency_score=fluency_score,
                integrity_score=integrity_score,
                xml_result=xml_result
            )
            
        except Exception as e:
            logger.error(f"结果解析失败: {str(e)}")
            return EvaluationResponse(
                success=False,
                message=f"结果解析失败: {str(e)}"
            )


class XfyunSDKFactory:
    """SDK工厂类"""
    
    _instance = None
    _config = None
    
    @classmethod
    def initialize(cls, app_id: str, api_key: str, api_secret: str):
        """初始化SDK配置"""
        cls._config = XfyunConfig(
            app_id=app_id,
            api_key=api_key,
            api_secret=api_secret
        )
        logger.info("讯飞SDK配置已初始化")
    
    @classmethod
    def get_sdk(cls) -> XfyunSpeechEvaluationSDK:
        """获取SDK实例"""
        if cls._config is None:
            raise RuntimeError("SDK未初始化，请先调用initialize方法")
        
        return XfyunSpeechEvaluationSDK(cls._config)
    
    @classmethod
    def create_syllable_request(cls, text: str) -> EvaluationRequest:
        """创建单字朗读请求"""
        return EvaluationRequest(
            category="read_syllable",
            text=text,
            group="pupil",
            language="cn_vip"
        )
    
    @classmethod
    def create_sentence_request(cls, text: str) -> EvaluationRequest:
        """创建句子朗读请求"""
        return EvaluationRequest(
            category="read_sentence",
            text=text,
            group="pupil",
            language="cn_vip"
        )


# 使用示例
async def evaluate_example():
    """使用示例"""
    # 初始化SDK
    XfyunSDKFactory.initialize(
        app_id="your_app_id",
        api_key="your_api_key",
        api_secret="your_api_secret"
    )
    
    # 获取SDK实例
    sdk = XfyunSDKFactory.get_sdk()
    
    # 创建评测请求
    request = XfyunSDKFactory.create_syllable_request("的一了我是")
    
    # 评测音频文件
    audio_file = Path("./test_audio.wav")
    if audio_file.exists():
        result = await sdk.evaluate_audio_file(audio_file, request)
        
        if result.success:
            print(f"评测成功！总分: {result.total_score}")
            print(f"声韵分: {result.phone_score}")
            print(f"调型分: {result.tone_score}")
        else:
            print(f"评测失败: {result.message}")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(evaluate_example())