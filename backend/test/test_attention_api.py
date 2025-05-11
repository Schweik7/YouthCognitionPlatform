"""
注意力筛查测试 API 测试
"""

import pytest
import requests
import time
import random
from typing import Dict, Any, List, Optional

# 配置
BASE_URL = "http://localhost:3000/api"
TIMEOUT = 5  # 请求超时时间（秒）


# 测试会话固定工具
@pytest.fixture(scope="module")
def api_client():
    """创建一个API客户端会话"""
    session = requests.Session()
    yield session
    session.close()


@pytest.fixture(scope="module")
def test_user(api_client) -> Dict[str, Any]:
    """创建一个测试用户"""
    user_data = {
        "name": f"测试用户_{int(time.time())}",
        "school": "测试学校",
        "grade": 3,
        "class_number": 2
    }
    
    response = api_client.post(f"{BASE_URL}/users/", json=user_data, timeout=TIMEOUT)
    assert response.status_code in (200, 201), f"创建用户失败: {response.text}"
    
    user = response.json()
    assert "id" in user, "用户响应中缺少ID"
    
    return user


@pytest.fixture(scope="module")
def test_attention_session(api_client, test_user) -> Dict[str, Any]:
    """创建一个注意力测试会话"""
    session_data = {
        "user_id": test_user["id"],
        "target_symbol": "Ψ"
    }
    
    response = api_client.post(
        f"{BASE_URL}/attention-test/sessions", 
        json=session_data,
        timeout=TIMEOUT
    )
    assert response.status_code in (200, 201), f"创建测试会话失败: {response.text}"
    
    session = response.json()
    assert "id" in session, "会话响应中缺少ID"
    
    return session


# 获取练习序列测试
def test_get_practice_sequence(api_client):
    """测试获取练习序列接口"""
    response = api_client.get(f"{BASE_URL}/attention-test/practice-sequence", timeout=TIMEOUT)
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    
    # 验证序列格式
    first_item = data[0]
    assert "row_index" in first_item
    assert "col_index" in first_item
    assert "symbol" in first_item
    assert "is_target" in first_item
    assert "is_clicked" in first_item


# 获取测试序列测试
def test_get_test_sequence(api_client):
    """测试获取测试序列接口"""
    response = api_client.get(f"{BASE_URL}/attention-test/test-sequence", timeout=TIMEOUT)
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    
    # 验证序列长度
    assert len(data) == 25 * 16  # 16行，每行25个符号
    
    # 验证序列格式
    first_item = data[0]
    assert "row_index" in first_item
    assert "col_index" in first_item
    assert "symbol" in first_item
    assert "is_target" in first_item
    assert "is_clicked" in first_item


# 测试会话管理测试
class TestAttentionSessionAPI:
    
    def test_create_session(self, api_client, test_user):
        """测试创建测试会话"""
        session_data = {
            "user_id": test_user["id"],
            "target_symbol": "Ψ"
        }
        
        response = api_client.post(
            f"{BASE_URL}/attention-test/sessions", 
            json=session_data,
            timeout=TIMEOUT
        )
        assert response.status_code in (200, 201)
        
        session = response.json()
        assert "id" in session
        assert session["user_id"] == test_user["id"]
        assert session["target_symbol"] == "Ψ"
        assert session["is_completed"] is False
    
    def test_get_session(self, api_client, test_attention_session):
        """测试获取测试会话信息"""
        response = api_client.get(
            f"{BASE_URL}/attention-test/sessions/{test_attention_session['id']}",
            timeout=TIMEOUT
        )
        assert response.status_code == 200
        
        session = response.json()
        assert session["id"] == test_attention_session["id"]
        assert session["user_id"] == test_attention_session["user_id"]
    
    def test_update_session(self, api_client, test_attention_session):
        """测试更新测试会话"""
        update_data = {
            "correct_count": 5,
            "incorrect_count": 2,
            "missed_count": 1
        }
        
        response = api_client.put(
            f"{BASE_URL}/attention-test/sessions/{test_attention_session['id']}",
            json=update_data,
            timeout=TIMEOUT
        )
        assert response.status_code == 200
        
        session = response.json()
        assert session["correct_count"] == 5
        assert session["incorrect_count"] == 2
        assert session["missed_count"] == 1


# 记录管理测试
def test_save_record(api_client, test_user, test_attention_session):
    """测试保存单个注意力测试记录"""
    record_data = {
        "user_id": test_user["id"],
        "test_session_id": test_attention_session["id"],
        "row_index": 0,
        "col_index": 1,
        "symbol": "Ψ",
        "is_target": True,
        "is_clicked": True
    }
    
    response = api_client.post(
        f"{BASE_URL}/attention-test/records",
        json=record_data,
        timeout=TIMEOUT
    )
    assert response.status_code in (200, 201)
    
    data = response.json()
    assert "message" in data
    assert "id" in data


# 完整流程测试
def test_complete_flow(api_client, test_user):
    """测试完整的注意力测试流程"""
    # 1. 创建会话
    session_data = {
        "user_id": test_user["id"],
        "target_symbol": "Ψ"
    }
    
    session_response = api_client.post(
        f"{BASE_URL}/attention-test/sessions", 
        json=session_data,
        timeout=TIMEOUT
    )
    assert session_response.status_code in (200, 201)
    session = session_response.json()
    
    # 2. 获取测试序列
    sequence_response = api_client.get(
        f"{BASE_URL}/attention-test/test-sequence?target_symbol=Ψ",
        timeout=TIMEOUT
    )
    assert sequence_response.status_code == 200
    sequence = sequence_response.json()
    
    # 3. 模拟用户答题 - 找出所有目标符号并点击
    clicked_records = []
    correct_count = 0
    incorrect_count = 0
    
    for symbol in sequence[:50]:  # 只测试前50个符号
        # 90%概率正确判断目标符号
        is_clicked = (symbol["is_target"] and random.random() < 0.9) or (not symbol["is_target"] and random.random() < 0.1)
        
        if is_clicked:
            record_data = {
                "user_id": test_user["id"],
                "test_session_id": session["id"],
                "row_index": symbol["row_index"],
                "col_index": symbol["col_index"],
                "symbol": symbol["symbol"],
                "is_target": symbol["is_target"],
                "is_clicked": True
            }
            
            record_response = api_client.post(
                f"{BASE_URL}/attention-test/records",
                json=record_data,
                timeout=TIMEOUT
            )
            assert record_response.status_code in (200, 201)
            
            clicked_records.append(record_data)
            
            if symbol["is_target"]:
                correct_count += 1
            else:
                incorrect_count += 1
    
    # 4. 完成测试
    complete_response = api_client.post(
        f"{BASE_URL}/attention-test/sessions/{session['id']}/complete",
        timeout=TIMEOUT
    )
    assert complete_response.status_code == 200
    
    # 5. 获取结果
    results_response = api_client.get(
        f"{BASE_URL}/attention-test/sessions/{session['id']}/results",
        timeout=TIMEOUT
    )
    assert results_response.status_code == 200
    
    results = results_response.json()
    assert "stats" in results
    assert "correctCount" in results["stats"]
    assert "incorrectCount" in results["stats"]
    assert "missedCount" in results["stats"]
    assert "totalScore" in results["stats"]


if __name__ == "__main__":
    pytest.main(["-xvs"])