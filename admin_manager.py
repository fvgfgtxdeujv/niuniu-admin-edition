"""
管理员管理模块
负责管理员的加载和权限检查
"""
import json
import os
from typing import List


class AdminManager:
    """管理员管理器"""
    
    def __init__(self, logger=None):
        self.logger = logger
        self.admins = self._load_admins()
    
    def _log_error(self, message: str):
        """记录错误日志"""
        if self.logger:
            self.logger.error(message)
    
    def _load_admins(self) -> List[str]:
        """加载管理员列表"""
        try:
            with open(os.path.join('data', 'cmd_config.json'), 'r', encoding='utf-8-sig') as f:
                config = json.load(f)
                return config.get('admins_id', [])
        except Exception as e:
            self._log_error(f"加载管理员列表失败: {str(e)}")
            return []
    
    def is_admin(self, user_id) -> bool:
        """检查用户是否为管理员"""
        return str(user_id) in self.admins
    
    def reload_admins(self):
        """重新加载管理员列表"""
        self.admins = self._load_admins()
