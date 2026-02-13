---
name: workstation
description: 获取工位基础数据
argument-hint: time=查询时间(非必填) workstationName=工位名称(非必填)
when_to_use:  machine
---

# Workstation Processing Guide

## Overview

指导文件可以帮助你查询时间{time}内工位{workstationName}数据


### 工位查询分页
- current: 当前页码(默认1)
- size: 分页大小(默认15)
```bash
curl ^"{cps_base_url}/blade-cps/workstation/pc-page?current=1^&size=20^&groupId=1^" ^
  -H ^"Accept: application/json, text/plain, */*^" ^
  -H ^"Accept-Language: zh-CN^" ^
  -H ^"Authorization: {cps_authorization}^" ^
  -H ^"Blade-Auth: {cps_access_token}^" ^
  -H ^"Connection: keep-alive^" ^
  -H ^"Content-Type: application/json^" ^
  -H ^"Tenant-Id: 000000^" ^
  -H ^"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0^" ^
  --data-raw ^"^{^\^"type^\^":^\^"^\^",^\^"status^\^":1^}^" ^
  --insecure

```

