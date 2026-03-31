"""
数据管理模块
负责所有数据的加载、保存和访问
"""
import yaml
import os
from typing import Dict, Any, Optional

from .config import NIUNIU_LENGTHS_FILE, NIUNIU_TEXTS_FILE, LAST_ACTION_FILE


class DataManager:
    """数据管理器"""
    
    def __init__(self, logger=None):
        self.logger = logger
    
    def _log_error(self, message: str):
        """记录错误日志"""
        if self.logger:
            self.logger.error(message)
    
    # ==================== 牛牛数据管理 ====================
    def _create_niuniu_lengths_file(self):
        """创建数据文件"""
        try:
            with open(NIUNIU_LENGTHS_FILE, 'w', encoding='utf-8') as f:
                yaml.dump({}, f)
        except Exception as e:
            self._log_error(f"创建文件失败: {str(e)}")
    
    def load_niuniu_lengths(self) -> Dict[str, Any]:
        """从文件加载牛牛数据"""
        if not os.path.exists(NIUNIU_LENGTHS_FILE):
            self._create_niuniu_lengths_file()
        
        try:
            with open(NIUNIU_LENGTHS_FILE, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
                
                # 数据结构验证
                for group_id in list(data.keys()):
                    group_data = data[group_id]
                    if not isinstance(group_data, dict):
                        data[group_id] = {'plugin_enabled': False}
                    elif 'plugin_enabled' not in group_data:
                        group_data['plugin_enabled'] = False
                    for user_id in list(group_data.keys()):
                        user_data = group_data[user_id]
                        if isinstance(user_data, dict):
                            user_data.setdefault('coins', 0)
                            user_data.setdefault('items', {})
                return data
        except Exception as e:
            self._log_error(f"加载数据失败: {str(e)}")
            return {}
    
    def save_niuniu_lengths(self, data: Dict[str, Any]):
        """保存数据到文件"""
        try:
            with open(NIUNIU_LENGTHS_FILE, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True)
        except Exception as e:
            self._log_error(f"保存失败: {str(e)}")
    
    # ==================== 冷却数据管理 ====================
    def load_last_actions(self) -> Dict[str, Any]:
        """加载冷却数据"""
        try:
            with open(LAST_ACTION_FILE, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except:
            return {}
    
    def save_last_actions(self, data: Dict[str, Any]):
        """保存冷却数据到文件"""
        try:
            with open(LAST_ACTION_FILE, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True)
        except Exception as e:
            self._log_error(f"保存冷却数据失败: {str(e)}")
    
    # ==================== 数据访问接口 ====================
    def get_group_data(self, group_id) -> Dict[str, Any]:
        """从文件获取群组数据"""
        group_id = str(group_id)
        data = self.load_niuniu_lengths()
        if group_id not in data:
            data[group_id] = {'plugin_enabled': False}
            self.save_niuniu_lengths(data)
        return data[group_id]
    
    def get_user_data(self, group_id, user_id) -> Optional[Dict[str, Any]]:
        """从文件获取用户数据"""
        group_id = str(group_id)
        user_id = str(user_id)
        data = self.load_niuniu_lengths()
        group_data = data.get(group_id, {'plugin_enabled': False})
        return group_data.get(user_id)
    
    def update_user_data(self, group_id, user_id, updates: Dict[str, Any]) -> Dict[str, Any]:
        """更新用户数据并保存到文件"""
        group_id = str(group_id)
        user_id = str(user_id)
        data = self.load_niuniu_lengths()
        group_data = data.setdefault(group_id, {'plugin_enabled': False})
        user_data = group_data.setdefault(user_id, {
            'nickname': '',
            'length': 0,
            'hardness': 1,
            'coins': 0,
            'items': {}
        })
        user_data.update(updates)
        self.save_niuniu_lengths(data)
        return user_data
    
    def update_group_data(self, group_id, updates: Dict[str, Any]) -> Dict[str, Any]:
        """更新群组数据并保存到文件"""
        group_id = str(group_id)
        data = self.load_niuniu_lengths()
        group_data = data.setdefault(group_id, {'plugin_enabled': False})
        group_data.update(updates)
        self.save_niuniu_lengths(data)
        return group_data
    
    def update_last_actions(self, data: Dict[str, Any]):
        """更新冷却数据并保存到文件"""
        self.save_last_actions(data)
