"""修复数据库中 Tool 参数的中文编码问题

将 Unicode 编码的中文（如 \u4e2d\u6587）转换为可读的中文字符
"""
import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "app.db")


def fix_encoding():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 获取所有工具
    cursor.execute("SELECT id, name, parameters FROM tools WHERE parameters IS NOT NULL")
    rows = cursor.fetchall()

    fixed_count = 0
    for tool_id, name, params_str in rows:
        if not params_str:
            continue

        # 尝试解析 JSON
        try:
            # 检查是否包含 Unicode 编码的中文
            if "\\u" in params_str:
                # 使用 Python 的 json.loads 自动处理 Unicode 转义
                params_list = json.loads(params_str)
                # 重新序列化为带中文的格式
                new_params_str = json.dumps(params_list, ensure_ascii=False)

                # 更新数据库
                cursor.execute(
                    "UPDATE tools SET parameters = ? WHERE id = ?",
                    (new_params_str, tool_id)
                )
                fixed_count += 1
                print(f"Fixed tool: {name} (id={tool_id})")
                print(f"  Old: {params_str[:100]}...")
                print(f"  New: {new_params_str[:100]}...")
        except json.JSONDecodeError as e:
            print(f"JSON decode error for tool {name}: {e}")
        except Exception as e:
            print(f"Error processing tool {name}: {e}")

    conn.commit()
    conn.close()

    print(f"\nTotal fixed: {fixed_count} tools")


if __name__ == "__main__":
    fix_encoding()
