"""
打胶处理器
"""
import random
import time
from astrbot.api.all import AstrMessageEvent
from ..utils import format_length


class DajiaoHandler:
    """打胶处理器"""
    
    def __init__(self, plugin):
        self.plugin = plugin
        self.data_manager = plugin.data_manager
        self.text_manager = plugin.text_manager
        self.cooldown_manager = plugin.cooldown_manager
    
    async def handle(self, event: AstrMessageEvent):
        """处理打胶命令"""
        group_id = str(event.message_obj.group_id)
        user_id = str(event.get_sender_id())
        nickname = event.get_sender_name()
        
        group_data = self.data_manager.get_group_data(group_id)
        if not group_data.get('plugin_enabled', False):
            yield event.plain_result("❌ 插件未启用")
            return
        
        user_data = self.data_manager.get_user_data(group_id, user_id)
        if not user_data:
            text = self.text_manager.get_text('dajiao', 'not_registered').format(nickname=nickname)
            yield event.plain_result(text)
            return
        
        user_items = self.plugin.shop.get_user_items(group_id, user_id)
        has_zhiming_rhythm = user_items.get("致命节奏", 0) > 0
        
        # 检查是否处于冷却期
        on_cooldown, remaining = self.cooldown_manager.check_dajiao_cooldown(group_id, user_id)
        
        # 初始化消息容器
        result_msg = []
        
        # 只有在冷却期内且持有道具时才触发效果
        if on_cooldown and has_zhiming_rhythm:
            # 消耗道具并跳过冷却
            self.plugin.shop.consume_item(group_id, user_id, "致命节奏")
            result_msg.append(f"⚡ 触发致命节奏！{nickname} 无视冷却强行打胶！")
            elapsed = self.plugin.COOLDOWN_30_MIN + 1  # 强制进入增益逻辑
        else:
            # 原有冷却处理
            if on_cooldown and not has_zhiming_rhythm:
                mins = int(remaining // 60) + 1
                text = self.text_manager.get_random_text('dajiao', 'cooldown').format(
                    nickname=nickname, remaining=mins
                )
                yield event.plain_result(text)
                return
            last_time = self.cooldown_manager.get_last_action_time(group_id, user_id, 'dajiao')
            elapsed = time.time() - last_time
        
        # 计算变化
        change = 0
        current_time = time.time()
        
        if elapsed < self.plugin.COOLDOWN_30_MIN:  # 10-30分钟
            rand = random.random()
            if rand < 0.4:  # 40% 增加
                change = random.randint(2, 5)
            elif rand < 0.7:  # 30% 减少
                change = -random.randint(1, 3)
        else:  # 30分钟后
            rand = random.random()
            if rand < 0.7:  # 70% 增加
                change = random.randint(3, 6)
                user_data['hardness'] = min(user_data['hardness'] + 1, 10)
            elif rand < 0.9:  # 20% 减少
                change = -random.randint(1, 2)
        
        # 应用变化并保存到文件
        updated_data = {
            'length': max(1, user_data['length'] + change)
        }
        if 'hardness' in locals():
            updated_data['hardness'] = user_data['hardness']
        self.data_manager.update_user_data(group_id, user_id, updated_data)
        
        # 更新冷却时间
        self.cooldown_manager.set_last_action_time(group_id, user_id, 'dajiao')
        
        # 生成消息
        if change > 0:
            template = self.text_manager.get_random_text('dajiao', 'increase')
        elif change < 0:
            if elapsed < self.plugin.COOLDOWN_30_MIN:
                template = self.text_manager.get_random_text('dajiao', 'decrease')
            else:
                template = self.text_manager.get_random_text('dajiao', 'decrease_30min')
        else:
            template = self.text_manager.get_random_text('dajiao', 'no_effect')
        
        text = template.format(nickname=nickname, change=abs(change))
        
        # 合并提示消息
        if result_msg:
            final_text = "\n".join(result_msg + [text])
        else:
            final_text = text
        
        # 重新获取最新数据以显示
        user_data = self.data_manager.get_user_data(group_id, user_id)
        yield event.plain_result(f"{final_text}\n当前长度：{format_length(user_data['length'])}")
