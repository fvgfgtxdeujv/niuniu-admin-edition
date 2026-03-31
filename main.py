#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
牛牛插件 - 精简版主入口文件
重构后的主入口文件，仅作为调度器使用
"""

import os
import sys
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from data_manager import DataManager
from text_manager import TextManager
from cooldown_manager import CooldownManager
from admin_manager import AdminManager
from utils import Utils

from handlers import (
    register_handler,
    dajiao_handler,
    compare_handler,
    status_handler,
    admin_handler,
    ranking_handler
)

class Plugin:
    """插件主类"""
    
    def __init__(self):
        """初始化插件"""
        self.config = Config()
        self.data_manager = DataManager(self.config)
        self.text_manager = TextManager(self.config)
        self.cooldown_manager = CooldownManager(self.config)
        self.admin_manager = AdminManager(self.config)
        self.utils = Utils(self.config, self.data_manager, self.text_manager, 
                         self.cooldown_manager, self.admin_manager)
        
        # 初始化处理器
        self.handlers = {
            'register': register_handler.RegisterHandler(self),
            'dajiao': dajiao_handler.DajiaoHandler(self),
            'compare': compare_handler.CompareHandler(self),
            'status': status_handler.StatusHandler(self),
            'admin': admin_handler.AdminHandler(self),
            'ranking': ranking_handler.RankingHandler(self)
        }
    
    def handle_command(self, command: str, params: Dict[str, Any]) -> str:
        """处理命令"""
        handler = self.handlers.get(command)
        if handler:
            return handler.handle(params)
        return "未知命令"

def main():
    """主函数"""
    plugin = Plugin()
    
    # 这里可以添加插件启动逻辑
    print("牛牛插件已启动")

if __name__ == "__main__":
    main()