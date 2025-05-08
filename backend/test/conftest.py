"""
Pytest 配置文件
用于设置测试环境、提供共享 fixtures 等
"""

import os
import pytest
from typing import Dict, Any, Generator
import requests


# 测试配置
API_CONFIGS = {
    "dev": {"base_url": "http://localhost:3000/api", "timeout": 5},
    "test": {"base_url": "http://test-server:3000/api", "timeout": 5},
    "prod": {"base_url": "https://api.example.com/api", "timeout": 10},
}


def pytest_addoption(parser):
    """添加命令行选项"""
    parser.addoption("--env", action="store", default="dev", help="指定测试环境: dev, test, prod")


@pytest.fixture(scope="session")
def api_config(request) -> Dict[str, Any]:
    """根据命令行选项返回 API 配置"""
    env = request.config.getoption("--env")
    return API_CONFIGS.get(env, API_CONFIGS["dev"])


@pytest.fixture(scope="session")
def api_client(api_config: Dict[str, Any]) -> Generator[requests.Session, None, None]:
    """创建一个 API 客户端会话"""
    session = requests.Session()

    # 添加默认请求头
    session.headers.update({"Content-Type": "application/json", "Accept": "application/json"})

    # 如果环境变量中有认证令牌，则添加到请求头
    auth_token = os.environ.get("API_AUTH_TOKEN")
    if auth_token:
        session.headers.update({"Authorization": f"Bearer {auth_token}"})

    # 提供会话给测试用例
    yield session

    # 会话结束后清理
    session.close()


@pytest.fixture(scope="session")
def base_url(api_config: Dict[str, Any]) -> str:
    """返回基础 URL"""
    return api_config["base_url"]


@pytest.fixture(scope="session")
def timeout(api_config: Dict[str, Any]) -> int:
    """返回请求超时时间"""
    return api_config["timeout"]
