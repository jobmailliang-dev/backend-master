---
name: machine
description: 机器台账管理 - 提供机器设备的增删改查接口，用于管理生产设备信息
---

# 机器台账技能

本技能提供机器台账的 API 接口调用规范，基于 CPS 系统的机器管理模块。

## 基础信息

- **Base URL**: `http://192.168.3.100`
- **认证**: OAuth2 password 模式获取 token
- **Content-Type**: application/json

## 认证流程

```bash
# 获取访问令牌
curl -X POST "http://192.168.3.100/api/blade-auth/oauth/token?tenantId=000000&username=admin&password=123456&grant_type=password&scope=all"
```

## 机器台账接口

### 1. 获取机器列表（分页查询）

```bash
curl -X POST "http://192.168.3.100/api/blade-cps/machine/page?current=1&orderField=&size=15" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "machineName": "",
    "machineGroupId": "",
    "typeId": "",
    "status": ""
  }'
```

**请求参数 (query)**:
| 参数 | 类型 | 说明 |
|------|------|------|
| current | int | 当前页码 |
| size | int | 每页数量 |
| orderField | string | 排序字段（可选） |

**请求体 (JSON)**:
| 字段 | 类型 | 说明 |
|------|------|------|
| machineName | string | 机器名称（模糊查询） |
| machineGroupId | string | 机器组ID |
| typeId | string | 机器类型ID |
| status | string | 状态（启用/禁用） |

**响应示例**:
```json
{
  "code": 200,
  "data": {
    "records": [
      {
        "id": "2018938830382112770",
        "machineCode": "CCC",
        "machineName": "CCC",
        "machineGroupId": "xxx",
        "machineGroupName": "默认组",
        "typeId": "",
        "serialNumber": "",
        "shortCode": "",
        "specification": "",
        "status": "1"
      }
    ],
    "total": 78,
    "size": 15,
    "current": 1
  },
  "msg": "success"
}
```

### 2. 获取机器详情

```bash
curl -X GET "http://192.168.3.100/api/blade-cps/machine/detail/{id}" \
  -H "Authorization: Bearer {access_token}"
```

**路径参数**:
| 参数 | 说明 |
|------|------|
| id | 机器ID |

### 3. 创建机器

```bash
curl -X POST "http://192.168.3.100/api/blade-cps/machine" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "machineName": "测试机器",
    "shortCode": "",
    "pinCode": "",
    "typeId": "",
    "serialNumber": "",
    "machineGroupId": "",
    "dmpId": "",
    "detail": {
      "originCountry": "",
      "specification": "",
      "lifeState": "",
      "systemName": "",
      "machineBrand": "",
      "machineNameplate": "",
      "netWeight": 0,
      "voltage": 0,
      "dimensionCm": 0,
      "powerKw": 0,
      "softwareVersion": ""
    },
    "asset": {
      "invoiceAmount": 0,
      "assetOriginalValue": 0,
      "assetNetValue": 0,
      "depreciationYears": 0,
      "assetCode": "",
      "manufacturer": "",
      "productionDate": "",
      "deliveryDate": ""
    },
    "storage": {
      "factoryArchive": "",
      "factoryCode": "",
      "installPosition": "",
      "manageLevel": "",
      "productionLine": "",
      "fixedDate": "",
      "useState": "",
      "useDeptId": "",
      "dutyUserId": "",
      "isSpecialEquipment": "0",
      "remark": ""
    }
  }'
```

**主要字段说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| machineName | string | 是 | 机器名称 |
| dmpId | string | 是 | DMP ID |
| machineGroupId | string | 是 | 所属机器组ID |
| typeId | string | 否 | 机器类型ID |

### 4. 更新机器

```bash
curl -X PUT "http://192.168.3.100/api/blade-cps/machine" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "2018938830382112770",
    "machineName": "更新后的名称",
    "shortCode": "SHORT01",
    "machineGroupId": "xxx",
    "dmpId": "xxx",
    ...其他字段
  }'
```

### 5. 删除机器

```bash
curl -X DELETE "http://192.168.3.100/api/blade-cps/machine?type=0" \
  -H "Authorization: Bearer {access_token}"
```

**Query 参数**:
| 参数 | 说明 |
|------|------|
| type | 0=删除, 1=停用 |

## 辅助接口

### 获取机器组树

```bash
curl -X GET "http://192.168.3.100/api/blade-cps/group/tree?groupCategory=1&groupType=group_machine" \
  -H "Authorization: Bearer {access_token}"
```

### 获取机器类型列表

```bash
curl -X GET "http://192.168.3.100/api/blade-cps/device-types/page?keyWord=&current=1&size=-1" \
  -H "Authorization: Bearer {access_token}"
```

### 获取字典数据

```bash
# 生命状态
curl -X GET "http://192.168.3.100/api/blade-system/dict/dictionary?code=machine_life_state" \
  -H "Authorization: Bearer {access_token}"

# 使用状态
curl -X GET "http://192.168.3.100/api/blade-system/dict/dictionary?code=machine_use_state" \
  -H "Authorization: Bearer {access_token}"
```

## 常用操作示例

### 查询默认组下的所有机器

```bash
# 1. 获取机器组ID
curl -X GET "http://192.168.3.100/api/blade-cps/group/tree?groupCategory=1&groupType=group_machine" \
  -H "Authorization: Bearer {access_token}" | jq '.data[] | select(.name == "默认组")'

# 2. 根据机器组ID查询机器列表
curl -X POST "http://192.168.3.100/api/blade-cps/machine/page?current=1&size=100" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{"machineGroupId": "默认组ID"}'
```

### 批量停用机器

```bash
curl -X DELETE "http://192.168.3.100/api/blade-cps/machine?type=1&ids=id1,id2" \
  -H "Authorization: Bearer {access_token}"
```
