# Apifox 导出示例：添加地址

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: Apifox Sample
  version: 1.0.0
paths:
  /api/address/add:
    post:
      summary: 添加地址
      description: 添加用户收货地址
      tags:
        - 地址管理
      parameters:
        - name: Authorization
          in: header
          description: Bearer token
          required: true
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required:
                - name
                - phone
                - province
                - city
                - district
                - detail
              properties:
                name:
                  type: string
                phone:
                  type: string
                province:
                  type: string
                city:
                  type: string
                district:
                  type: string
                detail:
                  type: string
                is_default:
                  type: integer
      responses:
        '201':
          description: 地址添加成功
        '400':
          description: 缺少必要参数
components:
  securitySchemes:
    Bearer:
      type: apikey
      name: Authorization
      in: header
```
