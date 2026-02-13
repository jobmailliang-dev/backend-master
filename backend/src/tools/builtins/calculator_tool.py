"""计算器工具。

执行数学计算。
"""

import ast
import operator
from typing import Any, Dict, List, Union

from src.tools.base import BaseTool


class CalculatorTool(BaseTool):
    """数学计算工具。"""

    # 安全操作符
    _ALLOWED_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    # 安全函数
    _ALLOWED_FUNCTIONS = {
        'abs': abs,
        'round': round,
        'min': min,
        'max': max,
        'sum': sum,
        'len': len,
    }

    def __init__(self):
        """初始化计算器工具。"""
        super().__init__(
            name="calculate",
            description="Perform mathematical calculations with basic operations",
        )

    def get_parameters(self) -> Dict[str, Any]:
        """获取参数定义。"""
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate (e.g., '2 + 2', '10 * 5', 'abs(-5)')",
                }
            },
            "required": ["expression"],
        }

    def _safe_eval(self, node: ast.AST) -> Union[int, float]:
        """安全地计算 AST 节点。"""
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.BinOp):
            left = self._safe_eval(node.left)
            right = self._safe_eval(node.right)
            op_type = type(node.op)

            if op_type in self._ALLOWED_OPERATORS:
                return self._ALLOWED_OPERATORS[op_type](left, right)
            raise ValueError(f"Operator {op_type.__name__} is not allowed")
        elif isinstance(node, ast.UnaryOp):
            operand = self._safe_eval(node.operand)
            op_type = type(node.op)

            if op_type in self._ALLOWED_OPERATORS:
                return self._ALLOWED_OPERATORS[op_type](operand)
            raise ValueError(f"Unary operator {op_type.__name__} is not allowed")
        elif isinstance(node, ast.Call):
            func_name = node.func.id
            if func_name in self._ALLOWED_FUNCTIONS:
                args = [self._safe_eval(arg) for arg in node.args]
                return self._ALLOWED_FUNCTIONS[func_name](*args)
            raise ValueError(f"Function {func_name} is not allowed")
        elif isinstance(node, ast.Expression):
            return self._safe_eval(node.body)
        elif isinstance(node, ast.Constant):
            return node.value
        else:
            raise ValueError(f"Expression type {type(node).__name__} is not allowed")

    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行计算。"""
        expression = kwargs.get('expression')

        if not expression:
            raise ValueError("Expression is required")

        try:
            tree = ast.parse(expression, mode='eval')
            result = self._safe_eval(tree)

            return {
                "expression": expression,
                "result": result,
                "result_type": type(result).__name__,
            }

        except SyntaxError as e:
            raise ValueError(f"Invalid expression syntax: {str(e)}")
        except ValueError as e:
            raise ValueError(str(e))
        except Exception as e:
            raise ValueError(f"Calculation failed: {str(e)}")

    def __repr__(self) -> str:
        return f"CalculatorTool(name={self.name})"
