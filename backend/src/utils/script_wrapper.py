"""JavaScript 脚本包装工具"""

import json
from typing import Optional


def wrap_javascript_code(code: str, params: dict, metadata: dict = None, inherit_from: Optional[str] = None) -> str:
    """将工具代码包装为可执行的 JavaScript 脚本。

    Args:
        code: 工具的原始 JavaScript 代码
        params: 执行参数，会放入 context.args 中
        metadata: 会话元数据，会放入 context.metadata 中
        inherit_from: 继承自的工具名称

    Returns:
        包装后的可执行 JavaScript 脚本
    """
    # 构建 context 对象
    context_parts = [f"args: {json.dumps(params, ensure_ascii=False)}"]

    # 添加 metadata
    if metadata:
        metadata_json = json.dumps(metadata, ensure_ascii=False)
        context_parts.append(f"metadata: {metadata_json}")

    # 如果存在 inherit_from，获取继承工具信息并生成 callTool 脚本
    data_script = ""
    if inherit_from:
        # 生成调用继承工具的脚本，直接使用 params 的值
        params_json = json.dumps(params, ensure_ascii=False)
        data_script = f'const data = callTool("{inherit_from}", {params_json});'

    if data_script:
        context_parts.append(f"data: (() => {{ {data_script} return data; }})()")

    context_str = "const context = {\n  " + ",\n  ".join(context_parts) + "\n};"

    # 检查 code 是否包含 function execute
    if "function execute" in code:
        # 包含 execute 函数，包装执行
        return f"""
{context_str}
{code}
return execute(context);
"""
    else:
        # 不包含 function execute，直接使用 code 作为脚本
        return f"""
{context_str}
{code}
"""
