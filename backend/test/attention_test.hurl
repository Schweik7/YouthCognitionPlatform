# 注意力筛查测试 API 测试
# 使用 Hurl (https://hurl.dev/)

# 定义基础URL变量
# hurl --variable base_url=http://localhost:3000
# 或者使用默认值
{{base_url:=http://localhost:3000}}

# 健康检查
GET {{base_url}}/api/health
HTTP 200
[Asserts]
jsonpath "$.status" == "ok"

# 创建用户
POST {{base_url}}/api/users/
{
  "name": "注意力测试用户",
  "school": "测试学校",
  "grade": 3,
  "class_number": 2
}
HTTP 201
[Captures]
user_id: jsonpath "$.id"

# 获取用户信息
GET {{base_url}}/api/users/{{user_id}}
HTTP 200
[Asserts]
jsonpath "$.name" == "注意力测试用户"
jsonpath "$.school" == "测试学校"

# 获取练习序列
GET {{base_url}}/api/attention-test/practice-sequence
HTTP 200
[Asserts]
jsonpath "$" count > 0
jsonpath "$[0].symbol" exists
jsonpath "$[0].is_target" exists

# 获取测试序列
GET {{base_url}}/api/attention-test/test-sequence
HTTP 200
[Asserts]
jsonpath "$" count == 400  # 16行 x 25列
jsonpath "$[0].row_index" exists
jsonpath "$[0].col_index" exists
jsonpath "$[0].symbol" exists
jsonpath "$[0].is_target" exists

# 创建测试会话
POST {{base_url}}/api/attention-test/sessions
{
  "user_id": {{user_id}},
  "target_symbol": "Ψ"
}
HTTP 201
[Captures]
session_id: jsonpath "$.id"
[Asserts]
jsonpath "$.user_id" == {{user_id}}
jsonpath "$.target_symbol" == "Ψ"
jsonpath "$.is_completed" == false

# 获取会话信息
GET {{base_url}}/api/attention-test/sessions/{{session_id}}
HTTP 200
[Asserts]
jsonpath "$.id" == {{session_id}}
jsonpath "$.user_id" == {{user_id}}

# 保存记录 - 目标符号点击
POST {{base_url}}/api/attention-test/records
{
  "user_id": {{user_id}},
  "test_session_id": {{session_id}},
  "row_index": 0,
  "col_index": 0,
  "symbol": "Ψ",
  "is_target": true,
  "is_clicked": true
}
HTTP 201
[Asserts]
jsonpath "$.message" exists
jsonpath "$.id" exists

# 保存记录 - 非目标符号点击
POST {{base_url}}/api/attention-test/records
{
  "user_id": {{user_id}},
  "test_session_id": {{session_id}},
  "row_index": 0,
  "col_index": 1,
  "symbol": "Π",
  "is_target": false,
  "is_clicked": true
}
HTTP 201

# 保存记录 - 目标符号未点击
POST {{base_url}}/api/attention-test/records
{
  "user_id": {{user_id}},
  "test_session_id": {{session_id}},
  "row_index": 0,
  "col_index": 2,
  "symbol": "Ψ",
  "is_target": true,
  "is_clicked": false
}
HTTP 201

# 更新会话
PUT {{base_url}}/api/attention-test/sessions/{{session_id}}
{
  "correct_count": 1,
  "incorrect_count": 1,
  "missed_count": 1
}
HTTP 200
[Asserts]
jsonpath "$.correct_count" == 1
jsonpath "$.incorrect_count" == 1
jsonpath "$.missed_count" == 1

# 完成会话
POST {{base_url}}/api/attention-test/sessions/{{session_id}}/complete
HTTP 200
[Asserts]
jsonpath "$.is_completed" == true
jsonpath "$.end_time" exists

# 获取结果
GET {{base_url}}/api/attention-test/sessions/{{session_id}}/results
HTTP 200
[Asserts]
jsonpath "$.stats" exists
jsonpath "$.stats.correctCount" exists
jsonpath "$.stats.incorrectCount" exists
jsonpath "$.stats.missedCount" exists
jsonpath "$.stats.totalScore" exists