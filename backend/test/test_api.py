"""
认知能力评估平台 API 测试
使用 pytest 自动测试各个 API 端点
"""

import pytest
import requests
import time
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
def test_session(api_client, test_user) -> Dict[str, Any]:
    """创建一个测试会话"""
    session_data = {
        "user_id": test_user["id"],
        "total_questions": 10
    }
    
    response = api_client.post(
        f"{BASE_URL}/reading-fluency/sessions", 
        json=session_data,
        timeout=TIMEOUT
    )
    assert response.status_code in (200, 201), f"创建测试会话失败: {response.text}"
    
    session = response.json()
    assert "id" in session, "会话响应中缺少ID"
    
    return session


# 健康检查测试
def test_health_check(api_client):
    """测试健康检查接口"""
    response = api_client.get(f"{BASE_URL}/health", timeout=TIMEOUT)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# 用户管理 API 测试
class TestUserManagementAPI:
    
    def test_create_user(self, api_client):
        """测试创建用户"""
        user_data = {
            "name": f"新用户_{int(time.time())}",
            "school": "测试学校",
            "grade": 5,
            "class_number": 3
        }
        
        response = api_client.post(f"{BASE_URL}/users/", json=user_data, timeout=TIMEOUT)
        assert response.status_code in (200, 201)
        
        user = response.json()
        assert "id" in user
        assert user["name"] == user_data["name"]
        assert user["school"] == user_data["school"]
        assert user["grade"] == user_data["grade"]
        assert user["class_number"] == user_data["class_number"]
    
    def test_get_user(self, api_client, test_user):
        """测试获取用户信息"""
        user_id = test_user["id"]
        response = api_client.get(f"{BASE_URL}/users/{user_id}", timeout=TIMEOUT)
        assert response.status_code == 200
        
        user = response.json()
        assert user["id"] == user_id
        assert user["name"] == test_user["name"]
    
    def test_get_schools(self, api_client):
        """测试获取学校列表"""
        response = api_client.get(f"{BASE_URL}/users/schools/recent", timeout=TIMEOUT)
        assert response.status_code == 200
        
        data = response.json()
        assert "schools" in data
        assert isinstance(data["schools"], list)


# 阅读流畅性测试 API 测试
class TestReadingFluencyAPI:
    
    def test_get_trials(self, api_client):
        """测试获取试题数据"""
        response = api_client.get(f"{BASE_URL}/reading-fluency/trials", timeout=TIMEOUT)
        assert response.status_code == 200
        
        data = response.json()
        assert "practiceTrials" in data
        assert "formalTrials" in data
        assert isinstance(data["practiceTrials"], list)
        assert isinstance(data["formalTrials"], list)
    
    def test_save_trial(self, api_client, test_user):
        """测试保存试验数据"""
        trial_data = {
            "user_id": test_user["id"],
            "trial_id": 1,
            "user_answer": True,
            "response_time": 1200
        }
        
        response = api_client.post(
            f"{BASE_URL}/reading-fluency/trials", 
            json=trial_data,
            timeout=TIMEOUT
        )
        assert response.status_code in (200, 201)
        
        data = response.json()
        assert "message" in data
        assert "id" in data
    
    def test_get_results(self, api_client, test_user):
        """测试获取用户结果"""
        response = api_client.get(
            f"{BASE_URL}/reading-fluency/results/{test_user['id']}", 
            timeout=TIMEOUT
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "user" in data
        assert "results" in data
        assert "trials" in data
        assert data["user"]["id"] == test_user["id"]


# 测试会话 API 测试
class TestSessionAPI:
    
    def test_create_session(self, api_client, test_user):
        """测试创建测试会话"""
        session_data = {
            "user_id": test_user["id"],
            "total_questions": 20
        }
        
        response = api_client.post(
            f"{BASE_URL}/reading-fluency/sessions", 
            json=session_data,
            timeout=TIMEOUT
        )
        assert response.status_code in (200, 201)
        
        session = response.json()
        assert "id" in session
        assert session["user_id"] == test_user["id"]
        assert session["total_questions"] == 20
        assert session["progress"] == 0
        assert session["is_completed"] is False
    
    def test_get_session(self, api_client, test_session):
        """测试获取测试会话信息"""
        response = api_client.get(
            f"{BASE_URL}/reading-fluency/sessions/{test_session['id']}", 
            timeout=TIMEOUT
        )
        assert response.status_code == 200
        
        session = response.json()
        assert session["id"] == test_session["id"]
        assert session["user_id"] == test_session["user_id"]
    
    def test_update_session(self, api_client, test_session):
        """测试更新测试会话"""
        update_data = {
            "progress": 5,
            "correct_count": 4
        }
        
        response = api_client.put(
            f"{BASE_URL}/reading-fluency/sessions/{test_session['id']}", 
            json=update_data,
            timeout=TIMEOUT
        )
        assert response.status_code == 200
        
        session = response.json()
        assert session["progress"] == 5
        assert session["correct_count"] == 4
    
    def test_save_session_trial(self, api_client, test_user, test_session):
        """测试在测试会话中保存试验记录"""
        trial_data = {
            "user_id": test_user["id"],
            "trial_id": 6,
            "user_answer": True,
            "response_time": 980
        }
        
        response = api_client.post(
            f"{BASE_URL}/reading-fluency/sessions/{test_session['id']}/trials", 
            json=trial_data,
            timeout=TIMEOUT
        )
        assert response.status_code in (200, 201)
        assert "id" in response.json()
    
    def test_get_session_trials(self, api_client, test_session):
        """测试获取测试会话中的所有试验记录"""
        response = api_client.get(
            f"{BASE_URL}/reading-fluency/sessions/{test_session['id']}/trials", 
            timeout=TIMEOUT
        )
        assert response.status_code == 200
        
        trials = response.json()
        assert isinstance(trials, list)
        # 至少应有一个试验记录（从之前的测试中创建）
        assert len(trials) >= 1
    
    def test_complete_session(self, api_client, test_session):
        """测试完成测试会话"""
        response = api_client.post(
            f"{BASE_URL}/reading-fluency/sessions/{test_session['id']}/complete", 
            timeout=TIMEOUT
        )
        assert response.status_code == 200
        
        session = response.json()
        assert session["is_completed"] is True
        assert session["end_time"] is not None
        assert session["total_time_seconds"] is not None
    
    def test_get_session_results(self, api_client, test_session):
        """测试获取测试会话结果"""
        response = api_client.get(
            f"{BASE_URL}/reading-fluency/sessions/{test_session['id']}/results", 
            timeout=TIMEOUT
        )
        assert response.status_code == 200
        
        results = response.json()
        assert "testSession" in results
        assert "user" in results
        assert "trials" in results
        assert "stats" in results
        assert results["testSession"]["id"] == test_session["id"]


# 完整流程测试
def test_complete_flow(api_client):
    """测试完整的用户测试流程"""
    # 1. 创建用户
    user_data = {
        "name": f"流程测试用户_{int(time.time())}",
        "school": "流程测试学校",
        "grade": 4,
        "class_number": 1
    }
    
    user_response = api_client.post(f"{BASE_URL}/users/", json=user_data, timeout=TIMEOUT)
    assert user_response.status_code in (200, 201)
    user = user_response.json()
    
    # 2. 创建测试会话
    session_data = {
        "user_id": user["id"],
        "total_questions": 30
    }
    
    session_response = api_client.post(
        f"{BASE_URL}/reading-fluency/sessions", 
        json=session_data,
        timeout=TIMEOUT
    )
    assert session_response.status_code in (200, 201)
    session = session_response.json()
    
    # 3. 添加多个试验记录
    for i in range(3):
        trial_data = {
            "user_id": user["id"],
            "trial_id": i + 1,
            "user_answer": i % 2 == 0,  # 偶数为True，奇数为False
            "response_time": 1000 + i * 100
        }
        
        trial_response = api_client.post(
            f"{BASE_URL}/reading-fluency/sessions/{session['id']}/trials", 
            json=trial_data,
            timeout=TIMEOUT
        )
        assert trial_response.status_code in (200, 201)
    
    # 4. 更新会话进度
    update_data = {
        "progress": 3,
        "correct_count": 2
    }
    
    update_response = api_client.put(
        f"{BASE_URL}/reading-fluency/sessions/{session['id']}", 
        json=update_data,
        timeout=TIMEOUT
    )
    assert update_response.status_code == 200
    
    # 5. 完成会话
    complete_response = api_client.post(
        f"{BASE_URL}/reading-fluency/sessions/{session['id']}/complete", 
        timeout=TIMEOUT
    )
    assert complete_response.status_code == 200
    
    # 6. 获取结果并检查各项数据
    results_response = api_client.get(
        f"{BASE_URL}/reading-fluency/sessions/{session['id']}/results", 
        timeout=TIMEOUT
    )
    assert results_response.status_code == 200
    
    results = results_response.json()
    assert results["testSession"]["is_completed"] is True
    assert results["testSession"]["progress"] == 3
    assert results["testSession"]["correct_count"] == 2
    assert len(results["trials"]) == 3
    assert results["stats"]["totalTrials"] == 3
    assert results["stats"]["correctTrials"] >= 0
    assert isinstance(results["stats"]["accuracy"], (int, float))
    assert isinstance(results["stats"]["completionRate"], (int, float))


if __name__ == "__main__":
    pytest.main(["-v"])