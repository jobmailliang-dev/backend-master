"""JavaScript 脚本包装工具"""

import json
from typing import Optional, Tuple

from sqlalchemy import DateTime


def wrap_javascript_code(code: str, params: dict, metadata: dict = None, inherit_from: Optional[str] = None) -> Tuple[dict, str]:
    """将工具代码包装为可执行的 JavaScript 脚本。

    Args:
        code: 工具的原始 JavaScript 代码
        params: 执行参数，会放入 context.args 中
        metadata: 会话元数据，会放入 context.metadata 中
        inherit_from: 继承自的工具名称

    Returns:
        tuple: (context_dict, wrapped_script)
            - context_dict: 包含 args, metadata, inherit_from 的字典，可作为 JS 绑定参数
            - wrapped_script: 包装后的 JavaScript 脚本（不含 context 声明）
    """
    # 构建 context 字典
    context = {"args": params}

    # 添加 metadata
    if metadata:
        context["metadata"] = metadata

    # 如果存在 inherit_from，添加到 context
    if inherit_from:
        context["inherit_from"] = inherit_from

    # 构建 callSuper 函数（如果存在 inherit_from）
    call_super_func = ""
    if inherit_from:
        call_super_func = '''
function callSuper() {
    return callTool(context.inherit_from, context.args);
}
'''

    # 检查 code 是否包含 function execute
    if "function execute" in code:
        # 包含 execute 函数，包装执行
        wrapped_script = f"""
{call_super_func}
{code}
return execute(context)
"""
    else:
        # 不包含 function execute，直接使用 code 作为脚本
        wrapped_script = f"""
{call_super_func}
{code}
"""

    return context, wrapped_script
