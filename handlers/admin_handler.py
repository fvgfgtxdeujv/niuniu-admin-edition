"""
管理员命令处理器
"""
from astrbot.api.all import AstrMessageEvent
from ..utils import format_length


class AdminHandler:
    """管理员处理器"""
    
    def __init__(self, plugin):
        self.plugin = plugin
        self.data_manager = plugin.data_manager
        self.admin_manager = plugin.admin_manager
    
    def parse_target(self, event):
        """解析@目标"""
        from ..utils import parse_at_target
        return parse_at_target(event)
    
    async def add_gold(self, event: AstrMessageEvent, target_id: str, amount: str):
        """添加金币"""
        group_id = str(event.message_obj.group_id)
        
        try:
            amount = int(amount)
            user_data = self.data_manager.get_user_data(group_id, target_id)
            if user_data:
                current_coins = user_data.get('coins', 0)
                self.data_manager.update_user_data(group_id, target_id, {
                    'coins': current_coins + amount
                })
                target_data = self.data_manager.get_user_data(group_id, target_id)
                yield event.plain_result(f"✅ 已为用户添加 {amount} 金币\n当前金币：{target_data['coins']}")
            else:
                yield event.plain_result("❌ 目标用户未注册")
        except ValueError:
            yield event.plain_result("❌ 数量格式错误")
    
    async def add_length(self, event: AstrMessageEvent, target_id: str, amount: str):
        """添加长度"""
        group_id = str(event.message_obj.group_id)
        
        try:
            amount = int(amount)
            user_data = self.data_manager.get_user_data(group_id, target_id)
            if user_data:
                current_length = user_data.get('length', 0)
                new_length = max(1, current_length + amount)
                self.data_manager.update_user_data(group_id, target_id, {
                    'length': new_length
                })
                target_data = self.data_manager.get_user_data(group_id, target_id)
                yield event.plain_result(f"✅ 已为用户修改长度 {amount}cm\n当前长度：{format_length(target_data['length'])}")
            else:
                yield event.plain_result("❌ 目标用户未注册")
        except ValueError:
            yield event.plain_result("❌ 数量格式错误")
    
    async def add_hardness(self, event: AstrMessageEvent, target_id: str, amount: str):
        """添加硬度"""
        group_id = str(event.message_obj.group_id)
        
        try:
            amount = int(amount)
            user_data = self.data_manager.get_user_data(group_id, target_id)
            if user_data:
                current_hardness = user_data.get('hardness', 1)
                new_hardness = max(1, min(10, current_hardness + amount))
                self.data_manager.update_user_data(group_id, target_id, {
                    'hardness': new_hardness
                })
                target_data = self.data_manager.get_user_data(group_id, target_id)
                yield event.plain_result(f"✅ 已为用户修改硬度 {amount}\n当前硬度：{target_data['hardness']}")
            else:
                yield event.plain_result("❌ 目标用户未注册")
        except ValueError:
            yield event.plain_result("❌ 数量格式错误")
    
    async def add_item(self, event: AstrMessageEvent, target_id: str, item_name: str, amount: str):
        """添加道具"""
        group_id = str(event.message_obj.group_id)
        
        try:
            amount = int(amount)
            user_data = self.data_manager.get_user_data(group_id, target_id)
            if user_data:
                items = user_data.get('items', {})
                items[item_name] = items.get(item_name, 0) + amount
                self.data_manager.update_user_data(group_id, target_id, {
                    'items': items
                })
                yield event.plain_result(f"✅ 已为用户添加道具 {item_name} x{amount}")
            else:
                yield event.plain_result("❌ 目标用户未注册")
        except ValueError:
            yield event.plain_result("❌ 数量格式错误")
    
    async def reset_user(self, event: AstrMessageEvent, target_id: str):
        """重置用户"""
        group_id = str(event.message_obj.group_id)
        
        user_data = self.data_manager.get_user_data(group_id, target_id)
        if user_data:
            nickname = user_data.get('nickname', target_id)
            self.data_manager.update_user_data(group_id, target_id, {
                'length': 0,
                'hardness': 1,
                'coins': 0,
                'items': {}
            })
            yield event.plain_result(f"✅ 已重置用户 {nickname}")
        else:
            yield event.plain_result("❌ 目标用户未注册")
    
    async def view_user(self, event: AstrMessageEvent, target_id: str):
        """查看用户"""
        group_id = str(event.message_obj.group_id)
        
        user_data = self.data_manager.get_user_data(group_id, target_id)
        if user_data:
            items_str = ", ".join([f"{k}x{v}" for k, v in user_data.get('items', {}).items()]) if user_data.get('items') else "无"
            info = f"""📊 用户信息：
昵称：{user_data.get('nickname', '未知')}
长度：{format_length(user_data.get('length', 0))}
硬度：{user_data.get('hardness', 1)}
金币：{user_data.get('coins', 0)}
道具：{items_str}"""
            yield event.plain_result(info)
        else:
            yield event.plain_result("❌ 目标用户未注册")
    
    async def show_menu(self, event: AstrMessageEvent):
        """显示管理员菜单"""
        menu = """🔧 管理员菜单：
💰 添加金币 @用户 数量
📏 添加长度 @用户 数量
💪 添加硬度 @用户 数量
📦 添加道具 @用户 道具名 数量
🔄 重置用户 @用户
👁️ 查看用户 @用户"""
        yield event.plain_result(menu)
