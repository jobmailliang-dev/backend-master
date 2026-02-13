"""日期时间工具。

获取当前日期和时间信息。
"""

from datetime import datetime
from typing import Any, Dict

import pytz

from src.tools.base import BaseTool


class DateTimeTool(BaseTool):
    """获取当前日期和时间的工具。"""

    def __init__(self):
        """初始化日期时间工具。"""
        super().__init__(
            name="get_datetime",
            description="Get current date and time information for a specific timezone or local timezone",
        )

    def get_parameters(self) -> Dict[str, Any]:
        """获取参数定义。"""
        return {
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "Timezone name (e.g., 'UTC', 'Asia/Shanghai', 'America/New_York'). Default is local timezone.",
                }
            },
            "required": [],
        }

    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行工具，获取当前日期时间。"""
        timezone_str = kwargs.get('timezone')

        try:
            if timezone_str:
                tz = pytz.timezone(timezone_str)
                now = datetime.now(tz)
                timezone_name = timezone_str
            else:
                now = datetime.now()
                timezone_name = "Local"

            return {
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%H:%M:%S"),
                "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
                "timezone": timezone_name,
                "iso_format": now.isoformat(),
                "weekday": now.strftime("%A"),
                "day_of_year": now.timetuple().tm_yday,
            }

        except pytz.UnknownTimeZoneError as e:
            raise ValueError(f"Unknown timezone: {timezone_str}. Please use IANA timezone names.")
        except Exception as e:
            raise ValueError(f"Failed to get datetime: {str(e)}")

    def __repr__(self) -> str:
        return f"DateTimeTool(name={self.name})"
