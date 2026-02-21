---
name: workstation
description: 工位基础数据
---

# 工位数据引导参考文件

## Overview

指导文件可以帮助你查询工位相关数据, 请充分阅读后组合脚本代码获取数据


### 基础查询工位数据
```javascript
//分页
callTool("查询工位组工位列表", {})
//指定页码和每页大小
callTool("查询工位组工位列表", {size:10, current:1}
//指定工位名称
callTool("查询工位组工位列表", {keyWord: "工位1"})
//指定工位编号
callTool("查询工位组工位列表", {keyWord: "judy001"})
//状态启用工位
callTool("查询工位组工位列表", {status: 1})
//状态停用工位
callTool("查询工位组工位列表", {status: 0})
//人工工位
callTool("查询工位组工位列表", {type:1})
//机器工位
callTool("查询工位组工位列表", {type:2})
//所有类型
callTool("查询工位组工位列表", {type: ""})
//列出所有工位
callTool("查询工位组工位列表", {size: -1})
```

### 根据工位组名称查询组下工位数据
```javascript
//工位组名称获取工位组
group = callTool("查询工位组", {name: "工位组名称"})
workstaitons =  callTool("查询工位组工位列表", {group_id: group.id })
return workstaitons
```

