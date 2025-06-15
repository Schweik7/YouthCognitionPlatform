# This is a sample Python script.
# 变量

from builtins import Exception, str, bytes

import websocket
import datetime
import hashlib
import base64
import hmac
import json
from urllib.parse import urlencode
import time
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import os
os.chdir(os.path.dirname(__file__))

host_url = "ws://ise-api.xfyun.cn/v2/open-ise"
appid = "e96b71cc"  # 控制台获取
api_secret = "YTM0YzkxYTk1MWQzOTdkZDg3Zjg0MTQx"
api_key = "c596bae72326e35a645eca27bf9d235a"

websocket_url = ""
audio_file = "./前四排好好读.mp3"


def product_url(api_secret, api_key):
    now_time = datetime.now()
    now_date = format_date_time(mktime(now_time.timetuple()))
    # print(now_date)
    # 拼接鉴权原始餐宿
    # now_date = "Fri, 18 Oct 2024 07:39:19 GMT"
    origin_base = "host: " + "ise-api.xfyun.cn" + "\n"
    origin_base += "date: " + now_date + "\n"
    origin_base += "GET " + "/v2/open-ise " + "HTTP/1.1"
    # print(origin_base)
    # sha256加密
    signature_sha = hmac.new(
        api_secret.encode("utf-8"),
        origin_base.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    signature_sha = base64.b64encode(signature_sha).decode(encoding="utf-8")
    print(signature_sha)
    authorization_origin = (
        'api_key="%s", algorithm="%s", headers="%s", signature="%s"'
        % (api_key, "hmac-sha256", "host date request-line", signature_sha)
    )
    authorization = base64.b64encode(authorization_origin.encode("utf-8")).decode(
        encoding="utf-8"
    )
    print(authorization)
    # 将请求的鉴权参数组合为字典
    dict_data = {
        "authorization": authorization,
        "date": now_date,
        "host": "ise-api.xfyun.cn",
    }
    ws_url = host_url + "?" + urlencode(dict_data)
    # print(ws_url)
    return ws_url


def on_message(ws, message):
    print(f"Received message: {message}")
    status = json.loads(message)["data"]["status"]
    # print(status)
    if status == 2:
        xml = base64.b64decode(json.loads(message)["data"]["data"])
        print(xml.decode("utf-8"))
        ws.close()


def on_error(ws, error):
    print(f"Error: {error},{ws}")


def on_close(ws, reason, res):
    print(f"WebSocket connection closed,{ws}")


def on_open(ws):
    print(f"WebSocket connection opened,{ws},ws连接建立成功...")
    # 这里可以发送初始消息给服务器，如果需要的话
    send_dict = {
        "common": {"app_id": appid},
        "business": {
            "category": "read_sentence",
            "rstcd": "utf8",
            "sub": "ise",
            "group": "pupil",
            "ent": "en_vip",
            "tte": "utf-8",
            "cmd": "ssb",
            "auf": "audio/L16;rate=16000",
            "aue": "lame",
            "text": "\ufeff" + "[content]\nnice to meet you.",
        },
        "data": {"status": 0, "data": ""},
    }
    ws.send(json.dumps(send_dict))  # 发送第一帧
    with open(audio_file, "rb") as file_flag:
        while True:
            buffer = file_flag.read(1280)
            if not buffer:
                my_dict = {
                    "business": {"cmd": "auw", "aus": 4, "aue": "lame"},
                    "data": {
                        "status": 2,
                        "data": str(base64.b64encode(buffer).decode()),
                    },
                }
                ws.send(json.dumps(my_dict))
                print("发送最后一帧")
                time.sleep(1)
                break  # 退出循环
            send_dict = {
                "business": {"cmd": "auw", "aus": 1, "aue": "lame"},
                "data": {
                    "status": 1,
                    "data": str(base64.b64encode(buffer).decode()),
                    "data_type": 1,
                    "encoding": "raw",
                },
            }
            ws.send(json.dumps(send_dict))  # 模拟发送一次中间音频帧
            # print("发送评测中间帧...")
            time.sleep(0.04)


def close_connection(ws):
    print("Closing WebSocket connection...")
    ws.close()


# 主函数入口
if __name__ == "__main__":
    start_time = datetime.now()
    websocket.enableTrace(False)
    ws_url = product_url(api_secret, api_key)
    ws_entity = websocket.WebSocketApp(
        ws_url,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open,
    )
    ws_entity.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
    end_time = datetime.now()
    print(f"评测耗时： {end_time - start_time}")
