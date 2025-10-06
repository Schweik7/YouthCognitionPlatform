# 瑞文智力测验 API 测试
# 使用 Hurl (https://hurl.dev/)

# 定义基础URL变量
# hurl --variable base_url=http://localhost:8001 test/raven_test.hurl
# 或者使用默认值
# {{base_url:=http://localhost:8001}}

# 健康检查
GET {{base_url}}/api/health
HTTP 200
[Asserts]
jsonpath "$.status" == "ok"

# 创建用户（包含出生日期）
POST {{base_url}}/api/users/
{
  "name": "瑞文测试用户",
  "school": "测试学校",
  "grade": 3,
  "class_number": 2,
  "birth_date": "2015-06-15"
}
HTTP 201
[Captures]
user_id: jsonpath "$.id"

# 获取用户信息
GET {{base_url}}/api/users/{{user_id}}
HTTP 200
[Asserts]
jsonpath "$.name" == "瑞文测试用户"
jsonpath "$.birth_date" exists

# 创建测试会话
POST {{base_url}}/api/raven-test/sessions
{
  "user_id": {{user_id}}
}
HTTP 201
[Captures]
session_id: jsonpath "$.id"
[Asserts]
jsonpath "$.user_id" == {{user_id}}
jsonpath "$.is_completed" == false
jsonpath "$.current_question" == 0
jsonpath "$.user_age" exists

# 获取会话信息
GET {{base_url}}/api/raven-test/sessions/{{session_id}}
HTTP 200
[Asserts]
jsonpath "$.id" == {{session_id}}
jsonpath "$.user_id" == {{user_id}}

# 获取单个题目信息
GET {{base_url}}/api/raven-test/questions/1
HTTP 200
[Asserts]
jsonpath "$.question_id" == 1
jsonpath "$.group_name" == "A"
jsonpath "$.num_options" == 6
jsonpath "$.main_image_url" exists
jsonpath "$.option_image_urls" count == 6

# 获取所有题目信息
GET {{base_url}}/api/raven-test/questions
HTTP 200
[Asserts]
jsonpath "$" count == 72

# 保存单个答案
POST {{base_url}}/api/raven-test/answers
{
  "user_id": {{user_id}},
  "test_session_id": {{session_id}},
  "question_id": 1,
  "user_answer": 4,
  "response_time": 5000
}
HTTP 201
[Asserts]
jsonpath "$.message" exists

# 保存单个答案（题目2）
POST {{base_url}}/api/raven-test/answers
{
  "user_id": {{user_id}},
  "test_session_id": {{session_id}},
  "question_id": 2,
  "user_answer": 5,
  "response_time": 6000
}
HTTP 201

# 批量保存答案（题目3-10）
POST {{base_url}}/api/raven-test/answers/batch
{
  "user_id": {{user_id}},
  "test_session_id": {{session_id}},
  "answers": [
    {"question_id": 3, "user_answer": 1, "response_time": 4500},
    {"question_id": 4, "user_answer": 2, "response_time": 5500},
    {"question_id": 5, "user_answer": 6, "response_time": 7000},
    {"question_id": 6, "user_answer": 3, "response_time": 4000},
    {"question_id": 7, "user_answer": 6, "response_time": 5000},
    {"question_id": 8, "user_answer": 2, "response_time": 6000},
    {"question_id": 9, "user_answer": 1, "response_time": 4500},
    {"question_id": 10, "user_answer": 3, "response_time": 5000}
  ]
}
HTTP 201
[Asserts]
jsonpath "$.count" == 8

# 获取会话的所有答案
GET {{base_url}}/api/raven-test/sessions/{{session_id}}/answers
HTTP 200
[Asserts]
jsonpath "$" count == 10

# 完成会话
POST {{base_url}}/api/raven-test/sessions/{{session_id}}/complete
HTTP 200
[Asserts]
jsonpath "$.is_completed" == true
jsonpath "$.end_time" exists
jsonpath "$.raw_score" exists
jsonpath "$.iq" exists

# 获取结果
GET {{base_url}}/api/raven-test/sessions/{{session_id}}/results
HTTP 200
[Asserts]
jsonpath "$.stats" exists
jsonpath "$.stats.rawScore" exists
jsonpath "$.stats.iq" exists
jsonpath "$.stats.percentile" exists
jsonpath "$.stats.zScore" exists
jsonpath "$.stats.totalQuestions" == 72
jsonpath "$.stats.answeredQuestions" == 10

# 获取用户的所有会话
GET {{base_url}}/api/raven-test/users/{{user_id}}/sessions
HTTP 200
[Asserts]
jsonpath "$" count >= 1
