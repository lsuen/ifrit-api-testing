# API接口文档

## POST /api/user/login 用户登录

用户登录接口，验证用户名和密码。

### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |

### 请求示例

```json
{
    "username": "admin",
    "password": "123456"
}
```

### 响应

- 200: 登录成功
- 400: 参数错误
- 401: 认证失败

### 响应示例

```json
{
    "code": 200,
    "message": "登录成功",
    "data": {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "user_id": 1
    }
}
```

## GET /api/user/profile 获取用户信息

获取当前登录用户的详细信息，需要认证。

### 请求头

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Authorization | string | 是 | Bearer token |

### 响应

- 200: 获取成功
- 401: 未认证
- 403: 权限不足
