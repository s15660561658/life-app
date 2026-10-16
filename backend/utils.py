"""通用小工具。"""
from datetime import datetime


def now_str() -> str:
    """当前时间，格式 YYYY-MM-DD HH:MM。"""
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def today_str() -> str:
    """今天日期，格式 YYYY-MM-DD。"""
    return datetime.now().strftime("%Y-%m-%d")
