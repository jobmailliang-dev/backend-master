---
name: workstation
description: 工位基础数据
---

# 工位数据引导参考文件

## Overview

指导文件可以帮助你查询工位相关数据, 请充分阅读后组合脚本代码使用工具`QuickJSTool` 获取数据


### 基础查询工位数据
```javascript
//分页
callTool("查询工位组工位列表", {data: {} })
//指定页码和每页大小
callTool("查询工位组工位列表", {data: {size:10, current:1} })
//指定工位名称
callTool("查询工位组工位列表", {data: {keyWord: "工位1"} })
//指定工位编号
callTool("查询工位组工位列表", {data: {keyWord: "judy001"} })
//状态启用工位
callTool("查询工位组工位列表", {data: {status: 1} })
//状态停用工位
callTool("查询工位组工位列表", {data: {status: 0} })
//人工工位
callTool("查询工位组工位列表", {data: {type:1} })
//机器工位
callTool("查询工位组工位列表", {data: {type:2} })
//所有类型
callTool("查询工位组工位列表", {data: {type: ""} })
//列出所有工位
callTool("查询工位组工位列表", {data: {size: -1} })
```

### 根据工位组名称查询组下工位数据
```javascript
//工位组名称获取工位组
group = callTool("查询工位组", {params: {name: "工位组名称"}})
workstaitons =  callTool("查询工位组工位列表", {data: {group_id: group.id }})
return workstaitons
```

### 统计工位组下工位数量
```javascript
// 1. 获取所有工位组列表 (Array)
var group_list = callTool("查询工位组", {data: {}});
var result = [];

// 2. 遍历工位组，组装数据
for (var i = 0; i < group_list.length; i++) {
    // 浅拷贝原始工位组对象，避免直接修改原数据
    var group = { ...group_list[i] };


    // 3. 获取该组下的工位列表
    var workstationsResult = callTool("查询工位组工位列表", {
        data: {
            group_id: group.id
        }
    } );
    

    // 4. 动态增加“工位数量”字段
    // 假设 workstationsResult 返回的是对象 { list: [], length: 0 }
    group.workstation_count = workstationsResult.list.length || 0;

    // 5. 将增强后的对象推入结果数组
    result.push(group);
}

// 返回数组：[{id: "001", name: "组A", workstation_count: 5}, ...]
return result;
```



