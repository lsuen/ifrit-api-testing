# 复杂API接口文档示例

## POST /api/auth/register 用户注册

用户注册接口，创建新用户账户。

### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| username | string | 是 | 用户名，3-20个字符 |
| email | string | 是 | 邮箱地址 |
| password | string | 是 | 密码，至少8位 |
| confirm_password | string | 是 | 确认密码 |
| phone | string | 否 | 手机号码 |
| age | integer | 否 | 年龄 |

### 请求示例

```json
{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
    "confirm_password": "password123",
    "phone": "13800138000",
    "age": 25
}
```

### 响应

- 201: 注册成功
- 400: 参数错误
- 409: 用户已存在

### 响应示例

```json
{
    "code": 201,
    "message": "注册成功",
    "data": {
        "user_id": 12345,
        "username": "testuser",
        "email": "test@example.com",
        "created_at": "2024-01-01T00:00:00Z"
    }
}
```

## GET /api/users/{user_id} 获取用户详情

获取指定用户的详细信息，需要认证。

### 路径参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| user_id | integer | 是 | 用户ID |

### 请求头

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Authorization | string | 是 | Bearer token |

### 查询参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| include_profile | boolean | 否 | 是否包含详细资料 |
| fields | string | 否 | 指定返回字段，逗号分隔 |

### 响应

- 200: 获取成功
- 401: 未认证
- 403: 权限不足
- 404: 用户不存在

## PUT /api/users/{user_id}/profile 更新用户资料

更新用户资料信息，需要认证且只能更新自己的资料。

### 路径参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| user_id | integer | 是 | 用户ID |

### 请求头

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Authorization | string | 是 | Bearer token |
| Content-Type | string | 是 | application/json |

### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| nickname | string | 否 | 昵称 |
| avatar | string | 否 | 头像URL |
| bio | string | 否 | 个人简介 |
| location | string | 否 | 所在地 |

### 响应

- 200: 更新成功
- 400: 参数错误
- 401: 未认证
- 403: 权限不足
- 404: 用户不存在

## DELETE /api/users/{user_id} 删除用户

删除指定用户，需要管理员权限。

### 路径参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| user_id | integer | 是 | 用户ID |

### 请求头

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Authorization | string | 是 | Bearer token (管理员) |

### 响应

- 204: 删除成功
- 401: 未认证
- 403: 权限不足
- 404: 用户不存在

## GET /api/posts 获取文章列表

获取文章列表，支持分页和筛选。

### 查询参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| page | integer | 否 | 页码，默认1 |
| limit | integer | 否 | 每页数量，默认10，最大100 |
| category | string | 否 | 分类筛选 |
| author | string | 否 | 作者筛选 |
| keyword | string | 否 | 关键词搜索 |
| sort | string | 否 | 排序方式：created_at, updated_at, views |
| order | string | 否 | 排序顺序：asc, desc |

### 响应

- 200: 获取成功
- 400: 参数错误

### 响应示例

```json
{
    "code": 200,
    "message": "获取成功",
    "data": {
        "posts": [
            {
                "id": 1,
                "title": "文章标题",
                "content": "文章内容",
                "author": "作者",
                "category": "技术",
                "views": 100,
                "created_at": "2024-01-01T00:00:00Z"
            }
        ],
        "pagination": {
            "page": 1,
            "limit": 10,
            "total": 50,
            "pages": 5
        }
    }
}
```