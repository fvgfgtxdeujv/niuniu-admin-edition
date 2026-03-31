"""
注册牛牛处理器
"""
import random
from astrbot.api.all import AstrMessageEvent


class RegisterHandler:
    """注册处理器"""
    
    def __init__(self, plugin):
        self.plugin = plugin
        self.data_manager = plugin.data_manager
        self.text_manager = plugin.text_manager
    
    async def handle(self, event: AstrMessageEvent):
        """处理注册命令"""
        group_id = str(event.message_obj.group_id)
        user_id = str(event.get_sender_id())
        nickname = event.get_sender_name()
        
        group_data = self.data_manager.get_group_data(group_id)
        if not group_data.get('plugin_enabled', False):
            yield event.plain_result("❌ 插件未启用")
            return
        
        if self.data_manager.get_user_data(group_id, user_id):
            text = self.text_manager.get_text('register', 'already_registered').format(nickname=nickname)
            yield event.plain_result(text)
            return
        
        cfg = self.plugin.config.get('niuniu_config', {})
        user_data = {
            'nickname': nickname,
            'length': random.randint(cfg.get('min_length', 3), cfg.get('max_length', 10)),
            'hardness': 1,
            'coins': 0,
            'items': {}
        }
        self.data_manager.update_user_data(group_id, user_id, user_data)
        
        text = self.text_manager.get_text('register', 'success').format(
            nickname=nickname,
            length=user_data['length'],
            hardness=user_data['hardness']
        )
        yield event.plain_result(text)
