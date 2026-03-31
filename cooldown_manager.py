"""
冷却管理模块
负责冷却时间的检查和管理
"""
import time
from typing import Dict, Any, Tuple
from .data_manager import DataManager
from .config import COOLDOWN_10_MIN, COOLDOWN_30_MIN, COMPARE_COOLDOWN


class CooldownManager:
    """冷却管理器"""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
    
    def check_cooldown(self, last_time: float, cooldown: int) -> Tuple[bool, float]:
        """检查冷却时间"""
        current = time.time()
        elapsed = current - last_time
        remaining = cooldown - elapsed
        return remaining > 0, remaining
    
    def get_last_action_time(self, group_id: str, user_id: str, action: str) -> float:
        """获取上次操作时间"""
        last_actions = self.data_manager.load_last_actions()
        return last_actions.setdefault(group_id, {}).setdefault(user_id, {}).get(action, 0)
    
    def set_last_action_time(self, group_id: str, user_id: str, action: str):
        """设置上次操作时间"""
        last_actions = self.data_manager.load_last_actions()
        last_actions.setdefault(group_id, {}).setdefault(user_id, {})[action] = time.time()
        self.data_manager.update_last_actions(last_actions)
    
    def check_dajiao_cooldown(self, group_id: str, user_id: str) -> Tuple[bool, float]:
        """检查打胶冷却"""
        last_time = self.get_last_action_time(group_id, user_id, 'dajiao')
        return self.check_cooldown(last_time, COOLDOWN_10_MIN)
    
    def check_compare_cooldown(self, group_id: str, user_id: str, target_id: str) -> Tuple[bool, float]:
        """检查比划冷却"""
        last_actions = self.data_manager.load_last_actions()
        compare_records = last_actions.setdefault(group_id, {}).setdefault(user_id, {})
        last_compare = compare_records.get(target_id, 0)
        return self.check_cooldown(last_compare, COMPARE_COOLDOWN)
    
    def get_compare_count(self, group_id: str, user_id: str) -> int:
        """获取10分钟内比划次数"""
        last_actions = self.data_manager.load_last_actions()
        compare_records = last_actions.setdefault(group_id, {}).setdefault(user_id, {})
        return compare_records.get('count', 0)
    
    def increment_compare_count(self, group_id: str, user_id: str):
        """增加比划次数"""
        last_actions = self.data_manager.load_last_actions()
        compare_records = last_actions.setdefault(group_id, {}).setdefault(user_id, {})
        compare_records['count'] = compare_records.get('count', 0) + 1
        compare_records['last_time'] = time.time()
        self.data_manager.update_last_actions(last_actions)
    
    def should_reset_compare_count(self, group_id: str, user_id: str) -> bool:
        """检查是否需要重置比划计数"""
        last_actions = self.data_manager.load_last_actions()
        compare_records = last_actions.setdefault(group_id, {}).setdefault(user_id, {})
        last_compare_time = compare_records.get('last_time', 0)
        if time.time() - last_compare_time > 600:  # 10分钟
            compare_records['count'] = 0
            compare_records['last_time'] = time.time()
            self.data_manager.update_last_actions(last_actions)
            return True
        return False
