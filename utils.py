"""
工具函数模块
"""
from astrbot.api.all import At
import re


def format_length(length: float) -> str:
    """格式化长度显示"""
    if length >= 100:
        return f"{length/100:.2f}m"
    return f"{length}cm"


def parse_at_target(event) -> str:
    """解析@目标"""
    for comp in event.message_obj.message:
        if isinstance(comp, At):
            return str(comp.qq)
    return None


def parse_target(event, data_manager=None):
    """解析@目标或用户名"""
    # 先尝试@解析
    at_result = parse_at_target(event)
    if at_result:
        return at_result
    
    # 再尝试用户名匹配
    msg = event.message_str.strip()
    if msg.startswith("比划比划") and data_manager:
        target_name = msg[len("比划比划"):].strip()
        if target_name:
            group_id = str(event.message_obj.group_id)
            group_data = data_manager.get_group_data(group_id)
            for user_id, user_data in group_data.items():
                if isinstance(user_data, dict):
                    nickname = user_data.get('nickname', '')
                    if re.search(re.escape(target_name), nickname, re.IGNORECASE):
                        return user_id
    return None
