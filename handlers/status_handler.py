"""
状态查看和排行榜处理器
"""
import random
from astrbot.api.all import AstrMessageEvent
from ..utils import format_length


class StatusHandler:
    """状态和排行榜处理器"""
    
    def __init__(self, plugin):
        self.plugin = plugin
        self.data_manager = plugin.data_manager
        self.text_manager = plugin.text_manager
    
    async def handle_status(self, event: AstrMessageEvent):
        """处理我的牛牛命令"""
        group_id = str(event.message_obj.group_id)
        user_id = str(event.get_sender_id())
        nickname = event.get_sender_name()
        
        group_data = self.data_manager.get_group_data(group_id)
        if not group_data.get('plugin_enabled', False):
            yield event.plain_result("❌ 插件未启用")
            return
        
        user_data = self.data_manager.get_user_data(group_id, user_id)
        if not user_data:
            text = self.text_manager.get_text('my_niuniu', 'not_registered').format(nickname=nickname)
            yield event.plain_result(text)
            return
        
        # 获取评价
        length = user_data['length']
        if length < 10:
            evaluation = random.choice(self.text_manager.get_text('my_niuniu', 'evaluation', 'short'))
        elif length < 20:
            evaluation = random.choice(self.text_manager.get_text('my_niuniu', 'evaluation', 'medium'))
        elif length < 30:
            evaluation = random.choice(self.text_manager.get_text('my_niuniu', 'evaluation', 'long'))
        elif length < 50:
            evaluation = random.choice(self.text_manager.get_text('my_niuniu', 'evaluation', 'very_long'))
        elif length < 100:
            evaluation = random.choice(self.text_manager.get_text('my_niuniu', 'evaluation', 'super_long'))
        else:
            evaluation = random.choice(self.text_manager.get_text('my_niuniu', 'evaluation', 'ultra_long'))
        
        text = self.text_manager.get_text('my_niuniu', 'info').format(
            nickname=nickname,
            length=format_length(user_data['length']),
            hardness=user_data['hardness'],
            evaluation=evaluation
        )
        yield event.plain_result(text)
    
    async def handle_ranking(self, event: AstrMessageEvent):
        """处理牛牛排行命令"""
        group_id = str(event.message_obj.group_id)
        
        group_data = self.data_manager.get_group_data(group_id)
        if not group_data.get('plugin_enabled', False):
            yield event.plain_result("❌ 插件未启用")
            return
        
        # 收集所有用户数据
        users = []
        for user_id, user_data in group_data.items():
            if isinstance(user_data, dict) and 'length' in user_data:
                users.append({
                    'name': user_data.get('nickname', user_id),
                    'length': user_data['length']
                })
        
        if not users:
            yield event.plain_result(self.text_manager.get_text('ranking', 'no_data'))
            return
        
        # 按长度排序，取前10
        users.sort(key=lambda x: x['length'], reverse=True)
        top10 = users[:10]
        
        # 生成排行榜
        lines = [self.text_manager.get_text('ranking', 'header')]
        for rank, user in enumerate(top10, 1):
            lines.append(self.text_manager.get_text('ranking', 'item').format(
                rank=rank,
                name=user['name'],
                length=format_length(user['length'])
            ))
        
        yield event.plain_result("\n".join(lines))
    
    async def handle_menu(self, event: AstrMessageEvent):
        """处理牛牛菜单命令"""
        text = self.text_manager.get_text('menu', 'default')
        yield event.plain_result(text)
    
    async def handle_toggle(self, event: AstrMessageEvent, enable: bool):
        """处理开关插件命令"""
        group_id = str(event.message_obj.group_id)
        user_id = str(event.get_sender_id())
        
        if not self.plugin.admin_manager.is_admin(user_id):
            yield event.plain_result("❌ 只有管理员才能使用此指令")
            return
        
        self.data_manager.update_group_data(group_id, {'plugin_enabled': enable})
        text_key = 'enable' if enable else 'disable'
        yield event.plain_result(self.text_manager.get_text('system', text_key))
