from niuniu_games import NiuniuGames
from niuniu_shop import NiuniuShop
import random
import yaml
import os
import re
import time
import json
import sys

from astrbot.api.all import *
from astrbot.core.event import AstrMessageEvent
from astrbot.core.pipeline.context import Context

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 常量定义
PLUGIN_DIR = os.path.join('data', 'plugins', 'astrbot_plugin_niuniu')
os.makedirs(PLUGIN_DIR, exist_ok=True)
NIUNIU_LENGTHS_FILE = os.path.join('data', 'niuniu_lengths.yml')
NIUNIU_TEXTS_FILE = os.path.join(PLUGIN_DIR, 'niuniu_game_texts.yml')
LAST_ACTION_FILE = os.path.join(PLUGIN_DIR, 'last_actions.yml')
ADMIN_LIST_FILE = os.path.join(PLUGIN_DIR, 'admin_list.yml')


@register("niuniu_plugin", "长安某", "牛牛插件，包含注册牛牛、打胶、我的牛牛、比划比划、牛牛排行等功能", "4.7.2")
class NiuniuPlugin(Star):
    # 冷却时间常量（秒）
    COOLDOWN_10_MIN = 600  # 10分钟
    COOLDOWN_30_MIN = 1800  # 30分钟
    COMPARE_COOLDOWN = 600  # 比划冷却
    INVITE_LIMIT = 3  # 邀请次数限制

    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        self.config = config or {}
        self.niuniu_texts = self._load_niuniu_texts()
        self.last_actions = self._load_last_actions()
        self.admins = self._load_admins()  # 加载管理员列表
        self.shop = NiuniuShop(self)  # 实例化商城模块
        self.games = NiuniuGames(self)  # 实例化游戏模块
        
    def _load_admin_list(self):
        """加载群级管理员"""
        try:
            with open(ADMIN_LIST_FILE, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def _save_admin_list(self, data):
        """保存群级管理员"""
        try:
            with open(ADMIN_LIST_FILE, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True)
        except Exception as e:
            self.context.logger.error(f"保存管理员列表失败: {e}")

    def _create_niuniu_lengths_file(self):
        """创建数据文件"""
        try:
            with open(NIUNIU_LENGTHS_FILE, 'w', encoding='utf-8') as f:
                yaml.dump({}, f)
        except Exception as e:
            self.context.logger.error(f"创建文件失败: {e}")

    def _load_niuniu_lengths(self):
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
                    if user_id == 'plugin_enabled':
                        continue
                    user_data = group_data[user_id]
                    if isinstance(user_data, dict):
                        user_data.setdefault('coins', 0)
                        user_data.setdefault('items', {})
            return data
        except Exception as e:
            self.context.logger.error(f"加载数据失败: {e}")
            return {}

    def _save_niuniu_lengths(self, data):
        """保存数据到文件"""
        try:
            with open(NIUNIU_LENGTHS_FILE, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True)
        except Exception as e:
            self.context.logger.error(f"保存失败: {e}")

    def _load_niuniu_texts(self):
        """加载游戏文本"""
        default_texts = {
            'register': {
                'success': "🧧 {nickname} 成功注册牛牛！\n📏 初始长度：{length}cm\n💪 硬度等级：{hardness}",
                'already_registered': "⚠️ {nickname} 你已经注册过牛牛啦！",
            },
            'dajiao': {
                'cooldown': [
                    "⏳ {nickname} 牛牛需要休息，{remaining}分钟后可再打胶",
                    "🛑 冷却中，{nickname} 请耐心等待 (＞﹏＜)"
                ],
                'increase': [
                    "🚀 {nickname} 打胶成功！长度增加 {change}cm！",
                    "🎉 {nickname} 的牛牛茁壮成长！+{change}cm"
                ],
                'decrease': [
                    "😱 {nickname} 用力过猛！长度减少 {change}cm！",
                    "⚠️ {nickname} 操作失误！-{change}cm"
                ],
                'decrease_30min': [
                    "😱 {nickname} 用力过猛！长度减少 {change}cm！",
                    "⚠️ {nickname} 操作失误！-{change}cm"
                ],
                'no_effect': [
                    "🌀 {nickname} 的牛牛毫无变化...",
                    "🔄 {nickname} 这次打胶没有效果"
                ],
                'not_registered': "❌ {nickname} 请先注册牛牛"
            },
            'my_niuniu': {
                'info': "📊 {nickname} 的牛牛状态\n📏 长度：{length}\n💪 硬度：{hardness}\n📝 评价：{evaluation}",
                'evaluation': {
                    'short': ["小巧玲珑", "精致可爱"],
                    'medium': ["中规中矩", "潜力无限"],
                    'long': ["威风凛凛", "傲视群雄"],
                    'very_long': ["擎天巨柱", "突破天际"],
                    'super_long': ["超级长", "无与伦比"],
                    'ultra_long': ["超越极限", "无人能敌"]
                },
                'not_registered': "❌ {nickname} 请先注册牛牛"
            },
            'compare': {
                'no_target': "❌ {nickname} 请指定比划对象",
                'target_not_registered': "❌ 对方尚未注册牛牛",
                'cooldown': "⏳ {nickname} 请等待{remaining}分钟后再比划",
                'self_compare': "❌ 不能和自己比划",
                'win': [
                    "🎉 {winner} 战胜了 {loser}！\n📈 增加 {gain}cm",
                    "🏆 {winner} 的牛牛更胜一筹！+{gain}cm"
                ],
                'lose': [
                    "😭 {loser} 败给 {winner}\n📉 减少 {loss}cm",
                    "💔 {loser} 的牛牛不敌对方！-{loss}cm"
                ],
                'draw': "🤝 双方势均力敌！",
                'double_loss': "😱 {nickname1} 和 {nickname2} 的牛牛因过于柔软发生缠绕，长度减半！",
                'hardness_win': "🎉 {nickname} 因硬度优势获胜！",
                'hardness_lose': "💔 {nickname} 因硬度劣势败北！",
                'user_no_increase': "😅 {nickname} 的牛牛没有任何增长。"
            },
            'ranking': {
                'header': "🏅 牛牛排行榜 TOP10：\n",
                'no_data': "📭 本群暂无牛牛数据",
                'item': "{rank}. {name} ➜ {length}"
            },
            'menu': {
                'default': """📜 牛牛菜单：
🔹 注册牛牛 - 初始化你的牛牛
🔹 打胶 - 提升牛牛长度
🔹 我的牛牛 - 查看当前状态
🔹 比划比划 @目标 - 发起对决
🔹 牛牛排行 - 查看群排行榜
🔹 牛牛开/关 - 管理插件"""
            },
            'system': {
                'enable': "✅ 牛牛插件已启用",
                'disable': "❌ 牛牛插件已禁用"
            }
        }

        try:
            if os.path.exists(NIUNIU_TEXTS_FILE):
                with open(NIUNIU_TEXTS_FILE, 'r', encoding='utf-8') as f:
                    custom_texts = yaml.safe_load(f) or {}
                return self._deep_merge(default_texts, custom_texts)
            return default_texts
        except Exception as e:
            self.context.logger.error(f"加载文本失败: {e}")
            return default_texts

    def _deep_merge(self, base, update):
        """深度合并字典"""
        for key, value in update.items():
            if isinstance(value, dict):
                base[key] = self._deep_merge(base.get(key, {}), value)
            else:
                base[key] = value
        return base

    def _load_last_actions(self):
        """加载冷却数据"""
        try:
            with open(LAST_ACTION_FILE, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def _save_last_actions(self, data):
        """保存冷却数据到文件"""
        try:
            with open(LAST_ACTION_FILE, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True)
        except Exception as e:
            self.context.logger.error(f"保存冷却数据失败: {e}")

    def _load_admins(self):
        """加载管理员列表"""
        try:
            with open(os.path.join('data', 'cmd_config.json'), 'r', encoding='utf-8-sig') as f:
                config = json.load(f)
            return config.get('admins_id', [])
        except Exception as e:
            self.context.logger.error(f"加载管理员列表失败: {e}")
            return []
    # endregion

    # region 数据访问接口
    def get_group_data(self, group_id):
        """从文件获取群组数据"""
        group_id = str(group_id)
        data = self._load_niuniu_lengths()
        if group_id not in data:
            data[group_id] = {'plugin_enabled': False}
            self._save_niuniu_lengths(data)
        return data[group_id]

    def get_user_data(self, group_id, user_id):
        """从文件获取用户数据"""
        group_id = str(group_id)
        user_id = str(user_id)
        data = self._load_niuniu_lengths()
        group_data = data.get(group_id, {'plugin_enabled': False})
        return group_data.get(user_id)

    def update_user_data(self, group_id, user_id, updates):
        """更新用户数据并保存到文件"""
        group_id = str(group_id)
        user_id = str(user_id)
        data = self._load_niuniu_lengths()
        group_data = data.setdefault(group_id, {'plugin_enabled': False})
        user_data = group_data.setdefault(user_id, {
            'nickname': '',
            'length': 0,
            'hardness': 1,
            'coins': 0,
            'items': {}
        })
        user_data.update(updates)
        self._save_niuniu_lengths(data)
        return user_data

    def update_group_data(self, group_id, updates):
        """更新群组数据并保存到文件"""
        group_id = str(group_id)
        data = self._load_niuniu_lengths()
        group_data = data.setdefault(group_id, {'plugin_enabled': False})
        group_data.update(updates)
        self._save_niuniu_lengths(data)
        return group_data

    def update_last_actions(self, data):
        """更新冷却数据并保存到文件"""
        self._save_last_actions(data)
    # endregion

    # region 工具方法
    def format_length(self, length):
        """格式化长度显示"""
        if length >= 100:
            return f"{length/100:.2f}m"
        return f"{length}cm"

    def check_cooldown(self, last_time, cooldown):
        current = time.time()
        elapsed = current - last_time
        if elapsed >= cooldown:
            return False, 0
        remaining = cooldown - elapsed
        return True, remaining

    def parse_at_target(self, event):
        """解析@目标"""
        for comp in event.message_obj.message:
            if isinstance(comp, At):
                return str(comp.qq)
        return None

    def parse_target(self, event):
        """只提取@或命令后第一个连续数字串（QQ号）"""
        # 1. 先尝试解析@
        at_target = self.parse_at_target(event)
        if at_target:
            return at_target

        # 2. 去掉命令头，用正则拿第一串数字
        msg = event.message_str.strip()
        for cmd in ["添加金币", "添加长度", "添加硬度", "添加道具","重置用户", "查看用户", "比划比划"]:
            if msg.startswith(cmd):
                arg = msg[len(cmd):].strip()
                m = re.search(r'\d+', arg)
                return m.group(0) if m else None
        return None

    def is_admin(self, user_id, group_id=None):
        """根管理员 或 本群管理员 都算"""
        user_id = str(user_id)
        # 根管理员（config.json 里的 admins_id）
        if user_id in self.admins:
            return True
        if group_id:
            group_id = str(group_id)
            admin_data = self._load_admin_list()
            return user_id in admin_data.get(group_id, [])
        return False


    # region 事件处理
    niuniu_commands = ["牛牛菜单","牛牛开","牛牛关","注册牛牛","打胶","我的牛牛","比划比划","牛牛排行","管理员菜单", "添加管理员","删除管理员","管理员列表"]

    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def on_group_message(self, event: AstrMessageEvent, context: Context):
        """群聊消息处理器"""
        group_id = str(event.message_obj.group_id)
        group_data = self.get_group_data(group_id)
        msg = event.message_str.strip()

        # 处理开关命令（不需要插件启用）
        if msg.startswith("牛牛开"):
            async for result in self._toggle_plugin(event, True):
                yield result
            return
        elif msg.startswith("牛牛关"):
            async for result in self._toggle_plugin(event, False):
                yield result
            return
        elif msg.startswith("牛牛菜单"):
            async for result in self._show_menu(event):
                yield result
            return
        elif msg.startswith("管理员菜单"):
            async for result in self._show_admin_menu(event):
                yield result
            return
        elif msg.startswith("添加管理员"):
            target = self.parse_target(event)
            if target:
                async for r in self._add_admin(event, target):
                    yield r
            else:
                yield event.plain_result("❌ 请 @ 要添加的管理员 或 直接给 QQ 号")
                return
        elif msg.startswith("删除管理员"):
            target = self.parse_target(event)
            if target:
                async for r in self._del_admin(event, target):
                yield r
            else:
                yield event.plain_result("❌ 请 @ 要删除的管理员 或 直接给 QQ 号")
            return
        elif msg.startswith("管理员列表"):
            async for r in self._list_admin(event):
                yield r
            return

        # 管理员命令处理（不需要插件启用）
        if msg.startswith("添加金币"):
            parts = msg.split()
            if len(parts) >= 3:
                target_id = self.parse_target(event)
                if target_id:
                    amount = parts[2]
                    async for result in self._admin_add_gold(event, target_id, amount):
                        yield result
                    return
        elif msg.startswith("添加长度"):
            print("已进入添加长度的功能")
            parts = msg.split()
            if len(parts) >= 3:
                target_id = self.parse_target(event)
                print(target_id)
                if target_id:
                    amount = parts[2]
                    async for result in self._admin_add_length(event, target_id, amount):
                        yield result
                    return
        elif msg.startswith("添加硬度"):
            parts = msg.split()
            if len(parts) >= 3:
                target_id = self.parse_target(event)
                if target_id:
                    amount = parts[2]
                    async for result in self._admin_add_hardness(event, target_id, amount):
                        yield result
                    return
        elif msg.startswith("添加道具"):
            parts = msg.split()
            if len(parts) >= 4:
                target_id = self.parse_target(event)
                if target_id:
                    item_name = parts[2]
                    amount = parts[3]
                    async for result in self._admin_add_item(event, target_id, item_name, amount):
                        yield result
                    return
        elif msg.startswith("重置用户"):
            parts = msg.split()
            if len(parts) >= 2:
                target_id = self.parse_target(event)
                if target_id:
                    async for result in self._admin_reset_user(event, target_id):
                        yield result
                    return
        elif msg.startswith("查看用户"):
            parts = msg.split()
            if len(parts) >= 2:
                target_id = self.parse_target(event)
                if target_id:
                    async for result in self._admin_view_user(event, target_id):
                        yield result
                    return

        # 如果插件未启用，忽略其他所有消息
        if not group_data.get('plugin_enabled', False):
            return

        # 统一检查是否在开冲
        user_id = str(event.get_sender_id())
        user_data = self.get_user_data(group_id, user_id)
        is_rushing = user_data.get('is_rushing', False) if user_data else False

        # 处理其他命令
        if msg.startswith("开冲"):
            if is_rushing:
                yield event.plain_result("❌ 你已经在开冲了，无需重复操作")
                return
            async for result in self.games.start_rush(event):
                yield result
        elif msg.startswith("停止开冲"):
            if not is_rushing:
                yield event.plain_result("❌ 你当前并未在开冲，无需停止")
                return
            async for result in self.games.stop_rush(event):
                yield result
        elif msg.startswith("飞飞机"):
            if is_rushing:
                yield event.plain_result("❌ 牛牛快冲晕了，还做不了其他事情，要不先停止开冲？")
                return
            async for result in self.games.fly_plane(event):
                yield result
        else:
            # 处理其他命令
            handler_map = {"注册牛牛": self._register,"打胶": self._dajiao,"我的牛牛": self._show_status,"比划比划": self._compare,"牛牛排行": self._show_ranking,"牛牛商城": self.shop.show_shop,"牛牛购买": self.shop.handle_buy,"牛牛背包": self.shop.show_items}

            for cmd, handler in handler_map.items():
                if msg.startswith(cmd):
                    if is_rushing:
                        yield event.plain_result("❌ 牛牛快冲晕了，还做不了其他事情，要不先停止开冲？")
                        return
                    async for result in handler(event):
                        yield result
                    return

    @event_message_type(EventMessageType.PRIVATE_MESSAGE)
    async def on_private_message(self, event: AstrMessageEvent):
        """私聊消息处理器"""
        msg = event.message_str.strip()
        niuniu_commands = ["牛牛菜单", "牛牛开", "牛牛关", "注册牛牛", "打胶", "我的牛牛", "比划比划","牛牛排行", "牛牛商城", "牛牛购买", "牛牛背包", "开冲", "停止开冲", "飞飞机"]

        if any(msg.startswith(cmd) for cmd in niuniu_commands):
            yield event.plain_result("不许一个人偷偷玩牛牛")
    # endregion

    # region 命令处理函数
    async def _toggle_plugin(self, event, enable):
        """开关插件"""
        group_id = str(event.message_obj.group_id)
        user_id = str(event.get_sender_id())

        # 检查是否为管理员
        if not self.is_admin(user_id):
            yield event.plain_result("❌ 只有管理员才能使用此指令")
            return

        self.update_group_data(group_id, {'plugin_enabled': enable})
        text_key = 'enable' if enable else 'disable'
        yield event.plain_result(self.niuniu_texts['system'][text_key])

    async def _register(self, event):
        """注册牛牛"""
        group_id = str(event.message_obj.group_id)
        user_id = str(event.get_sender_id())
        nickname = event.get_sender_name()
        group_data = self.get_group_data(group_id)

        if not group_data.get('plugin_enabled', False):
            yield event.plain_result("❌ 插件未启用")
            return

        if self.get_user_data(group_id, user_id):
            text = self.niuniu_texts['register']['already_registered'].format(
                nickname=nickname)
            yield event.plain_result(text)
            return

        cfg = self.config.get('niuniu_config', {})
        user_data = {'nickname': nickname,'length': random.randint(cfg.get('min_length',3),cfg.get('max_length',10)),'hardness': 1,'coins': 0,'items': {}}

        self.update_user_data(group_id, user_id, user_data)
        text = self.niuniu_texts['register']['success'].format(
            nickname=nickname,
            length=user_data['length'],
            hardness=user_data['hardness']
        )
        yield event.plain_result(text)

    async def _dajiao(self, event: AstrMessageEvent):
        """打胶功能"""
        group_id = str(event.message_obj.group_id)
        user_id = str(event.get_sender_id())
        nickname = event.get_sender_name()
        group_data = self.get_group_data(group_id)

        if not group_data.get('plugin_enabled', False):
            yield event.plain_result("❌ 插件未启用")
            return

        user_data = self.get_user_data(group_id, user_id)
        if not user_data:
            text = self.niuniu_texts['dajiao']['not_registered'].format(
                nickname=nickname)
            yield event.plain_result(text)
            return

        user_items = self.shop.get_user_items(group_id, user_id)
        has_zhiming_rhythm = user_items.get("致命节奏", 0) > 0
        last_actions = self._load_last_actions()
        last_time = last_actions.setdefault(
            group_id, {}).get(
            user_id, {}).get(
            'dajiao', 0)

        # 初始化消息容器
        result_msg = []

        # 检查是否处于冷却期
        on_cooldown, remaining = self.check_cooldown(last_time, self.COOLDOWN_10_MIN)

        # 只有在冷却期内且持有道具时才触发效果
        if on_cooldown and has_zhiming_rhythm:
            # 消耗道具并跳过冷却
            self.shop.consume_item(group_id, user_id, "致命节奏")
            result_msg.append(f"⚡ 触发致命节奏！ {nickname} 无视冷却强行打胶！")
            elapsed = self.COOLDOWN_30_MIN + 1  # 强制进入增益逻辑
        else:
            # 原有冷却处理
            if on_cooldown and not has_zhiming_rhythm:
                mins = int(remaining // 60) + 1
                text = random.choice(self.niuniu_texts['dajiao']['cooldown']).format(
                    nickname=nickname, remaining=mins
                )
                yield event.plain_result(text)
                return
            elapsed = time.time() - last_time

        # 计算变化
        change = 0
        current_time = time.time()
        template = ""

        if elapsed < self.COOLDOWN_30_MIN:  # 10-30分钟
            rand = random.random()
            if rand < 0.4:  # 40% 增加
                change = random.randint(2, 5)
                template = random.choice(self.niuniu_texts['dajiao']['increase'])
            elif rand < 0.7:  # 30% 减少
                change = -random.randint(1, 3)
                template = random.choice(self.niuniu_texts['dajiao']['decrease'])
            # 30% 无效果
        else:  # 30分钟后
            rand = random.random()
            if rand < 0.7:  # 70% 增加
                change = random.randint(3, 6)
                template = random.choice(self.niuniu_texts['dajiao']['increase'])
                user_data['hardness'] = min(user_data['hardness'] + 1, 10)
            elif rand < 0.9:  # 20% 减少
                change = -random.randint(1, 2)
                template = random.choice(self.niuniu_texts['dajiao']['decrease_30min'])
            # 10% 无效果

        # 应用变化并保存到文件
        updated_data = {'length': max(1, user_data['length'] + change)}
        if user_data.get('hardness'):
            updated_data['hardness'] = user_data['hardness']

        self.update_user_data(group_id, user_id, updated_data)

        # 更新冷却时间
        last_actions = self._load_last_actions()
        last_actions.setdefault(
            group_id, {}).setdefault(
            user_id, {})['dajiao'] = current_time
        self.update_last_actions(last_actions)

        # 生成消息
        if change == 0:
            template = random.choice(self.niuniu_texts['dajiao']['no_effect'])
            text = template.format(nickname=nickname)
        else:
            text = template.format(nickname=nickname, change=abs(change))

        # 合并提示消息
        if result_msg:
            final_text = "\n".join(result_msg + [text])
        else:
            final_text = text

        # 重新获取最新数据以显示
        user_data = self.get_user_data(group_id, user_id)
        yield event.plain_result(f"{final_text}\n当前长度：{self.format_length(user_data['length'])}")

    async def _compare(self, event):
        """比划功能——管理员终极豁免版"""
        group_id = str(event.message_obj.group_id)
        user_id  = str(event.get_sender_id())
        nickname = event.get_sender_name()

        # 1. 基础校验
        group_data = self.get_group_data(group_id)
        if not group_data.get('plugin_enabled', False):
            yield event.plain_result("❌ 插件未启用")
            return

        user_data = self.get_user_data(group_id, user_id)
        if not user_data:
            yield event.plain_result(self.niuniu_texts['dajiao']['not_registered'].format(nickname=nickname))
            return

        target_id = self.parse_target(event)
        if not target_id or target_id == user_id:
            yield event.plain_result(self.niuniu_texts['compare']['self_compare'])
            return

        target_data = self.get_user_data(group_id, target_id)
        if not target_data:
            yield event.plain_result(self.  niuniu_texts['compare']['target_not_registered'])
            return

        # 2. 冷却 & 10 分钟 3 次限制
        last_actions = self._load_last_actions()
        compare_records = last_actions.setdefault(group_id, {}).setdefault(user_id, {})
        last_compare = compare_records.get(target_id, 0)
        on_cooldown, remaining = self.check_cooldown(last_compare, self.COMPARE_COOLDOWN)
        if on_cooldown:
            mins = int(remaining // 60) + 1
            yield event.plain_result(self.niuniu_texts['compare']['cooldown'].format(nickname=nickname, remaining=mins))
            return

        current_time = time.time()
        if current_time - compare_records.get('last_time', 0) > 600:
            compare_records['count'] = 0
            compare_records['last_time'] = current_time
        if compare_records.get('count', 0) >= 3:
            yield event.plain_result("❌ 10 分钟内只能比划三次")
            return

        # 3. 更新冷却 & 计数
        compare_records[target_id] = current_time
        compare_records['count']  = compare_records.get('count', 0) + 1
        self.update_last_actions(last_actions)

        # 4. 管理员最高优先级——永不缩短
        is_admin_user = self.is_admin(user_id)
        if is_admin_user:
            gain = random.randint(1, 3)
            user_data['length'] += gain
            t_gain = random.randint(0, 2)
            target_data['length'] += t_gain
            self.update_user_data(group_id, user_id,   user_data)
            self.update_user_data(group_id, target_id, target_data)
            yield event.plain_result(f"⚔️ 【牛牛对决结果】 ⚔️\n"f"👑 管理员 {nickname} 获胜！长度 +{gain} cm（管理员永不减少）\n"f"🛡️ {target_data['nickname']} 陪练奖励 +{t_gain} cm")
            return

        # 5. 夺心魔——对管理员已提前过滤，这里只剩普通人
        user_items = self.shop.get_user_items(group_id, user_id)
        if user_items.get("夺心魔蝌蚪罐头", 0) > 0:
            r = random.random()
            self.shop.consume_item(group_id, user_id, "夺心魔蝌蚪罐头")
            if r < 0.5:
                stolen = target_data['length']
                user_data['length'] += stolen
                target_data['length'] = 1
                self.update_user_data(group_id, user_id,   user_data)
                self.update_user_data(group_id, target_id, target_data)
                yield event.plain_result(f"⚔️ 【牛牛对决结果】 ⚔️\n"f"🎉 {nickname} 夺取了 {target_data['nickname']} 的全部长度！\n"f"🗡️ {nickname}: {self.format_length(user_data['length']-stolen)} → {self.format_length(user_data['length'])}\n"f"🛡️ {target_data['nickname']}: {self.format_length(stolen)} → 1 cm")
                return
            elif r < 0.6:
                user_data['length'] = 1
                self.update_user_data(group_id, user_id, user_data)
                yield event.plain_result(f"⚔️ 【牛牛对决结果】 ⚔️\n"f"💔 {nickname} 使用夺心魔蝌蚪罐头，牛牛变成了夺心魔！！！\n"f"🗡️ {nickname}: {self.format_length(user_data['length'])} → 1 cm")
                return
            else:
                yield event.plain_result(f"⚔️ 【牛牛对决结果】 ⚔️\n"f"⚠️ {nickname} 使用夺心魔蝌蚪罐头，但是罐头好像坏掉了...")
                return

        # 6. 普通比拼
        old_u, old_t = user_data['length'], target_data['length']
        u_len, t_len = old_u, old_t
        u_hard, t_hard = user_data['hardness'], target_data['hardness']

        base_win = 0.5
        max_len  = max(u_len, t_len, 1)
        length_factor = (u_len - t_len) / max_len * 0.2
        hardness_factor = (u_hard - t_hard) * 0.05
        win_prob = min(max(base_win + length_factor + hardness_factor, 0.2), 0.8)

        if random.random() < win_prob:
            gain = random.randint(0, 3)
            user_data['length'] += gain
            loss = random.randint(1, 2)
            target_data['length'] = max(1, target_data['length'] - loss)
            msg = [f"🎉 {nickname} 获胜！+{gain} cm，{target_data['nickname']} -{loss} cm"]
            # 淬火爪刀
            if user_items.get("淬火爪刀", 0) > 0 and abs(u_len - t_len) > 10 and u_len < t_len:
                extra = int(target_data['length'] * 0.1)
                user_data['length'] += extra
                msg.append(f"🔥 淬火爪刀触发！额外掠夺 {extra} cm")
                self.shop.consume_item(group_id, user_id, "淬火爪刀")
        else:
            gain = random.randint(0, 3)
            target_data['length'] += gain
            loss = random.randint(1, 2)
            # 余震仅对普通用户生效，且放在管理员判断之后
            if user_items.get("余震", 0) > 0:
                self.shop.consume_item(group_id, user_id, "余震")
                msg = [f"🛡️ 【余震生效】 {nickname} 未减少长度！"]
            else:
                user_data['length'] = max(1, user_data['length'] - loss)
                msg = [f"💔 {nickname} 失败！-{loss} cm"]
            msg.append(f"🎉 {target_data['nickname']} 获胜！+{gain} cm")

        # 7. 统一写档 & 回显
        self.update_user_data(group_id, user_id,   user_data)
        self.update_user_data(group_id, target_id, target_data)
        yield event.plain_result(f"⚔️ 【牛牛对决结果】 ⚔️\n"f"🗡️ {nickname}: {self.format_length(old_u)} → {self.format_length(user_data['length'])}\n"f"🛡️ {target_data['nickname']}: {self.format_length(old_t)} → {self.format_length(target_data['length'])}\n"+ "\n".join(msg))

    async def _show_status(self, event):
        """查看牛牛状态"""
        group_id = str(event.message_obj.group_id)
        user_id = str(event.get_sender_id())
        nickname = event.get_sender_name()
        group_data = self.get_group_data(group_id)

        if not group_data.get('plugin_enabled', False):
            yield event.plain_result("❌ 插件未启用")
            return

        user_data = self.get_user_data(group_id, user_id)
        if not user_data:
            yield event.plain_result(self.niuniu_texts['my_niuniu']['not_registered'].format(nickname=nickname))
            return

        # 评价系统
        length = user_data['length']
        length_str = self.format_length(length)

        if length < 12:
            evaluation = random.choice(
                self.niuniu_texts['my_niuniu']['evaluation']['short'])
        elif length < 25:
            evaluation = random.choice(
                self.niuniu_texts['my_niuniu']['evaluation']['medium'])
        elif length < 50:
            evaluation = random.choice(
                self.niuniu_texts['my_niuniu']['evaluation']['long'])
        elif length < 100:
            evaluation = random.choice(
                self.niuniu_texts['my_niuniu']['evaluation']['very_long'])
        elif length < 200:
            evaluation = random.choice(
                self.niuniu_texts['my_niuniu']['evaluation']['super_long'])
        else:
            evaluation = random.choice(
                self.niuniu_texts['my_niuniu']['evaluation']['ultra_long'])

        text = self.niuniu_texts['my_niuniu']['info'].format(
            nickname=nickname,
            length=length_str,
            hardness=user_data.get('hardness', 1),
            evaluation=evaluation
        )
        yield event.plain_result(text)

    async def _show_ranking(self, event):
        """显示排行榜（从文件读取数据）"""
        group_id = str(event.message_obj.group_id)
        group_data = self.get_group_data(group_id)

        if not group_data.get('plugin_enabled', False):
            yield event.plain_result("❌ 插件未启用")
            return

        # 过滤有效用户数据
        data = self._load_niuniu_lengths()
        group_data = data.get(group_id, {'plugin_enabled': False})
        valid_users = [
            (uid, data) for uid, data in group_data.items()
            if isinstance(data, dict) and 'length' in data
        ]

        if not valid_users:
            yield event.plain_result(self.niuniu_texts['ranking']['no_data'])
            return

        # 排序并取前10
        sorted_users = sorted(valid_users,key=lambda x: x[1]['length'],reverse=True)[:10]

        # 构建排行榜
        ranking = [self.niuniu_texts['ranking']['header']]
        for idx, (uid, data) in enumerate(sorted_users, 1):
            ranking.append(
                self.niuniu_texts['ranking']['item'].format(rank=idx,name=data['nickname'],length=self.format_length(data['length']))
            )

        yield event.plain_result("\n".join(ranking))

    async def _show_menu(self, event):
        """显示菜单"""
        user_id = str(event.get_sender_id())

        # 如果是管理员，显示管理员菜单
        if self.is_admin(user_id):
            yield event.plain_result(self.niuniu_texts['menu']['default'] + "\n\n👑 管理员专属：\n🔹 管理员菜单 - 显示管理员功能菜单")
        else:
            yield event.plain_result(self.niuniu_texts['menu']['default'])

    async def _show_admin_menu(self, event):
        """显示管理员菜单"""
        user_id = str(event.get_sender_id())

        # 检查是否为管理员
        if not self.is_admin(user_id):
            yield event.plain_result("❌ 只有管理员才能使用此指令")
            return

        admin_menu = """👑 管理员功能菜单：
🔹 添加金币 @用户/QQ 数量
🔹 添加长度 @用户/QQ 数量
🔹 添加硬度 @用户/QQ 数量
🔹 添加道具 @用户/QQ 道具名 数量
🔹 重置用户 @用户/QQ
🔹 查看用户 @用户/QQ
🔹 添加管理员 @用户/QQ   ← 根管理员可用
🔹 删除管理员 @用户/QQ   ← 根管理员可用
🔹 管理员列表            ← 任何人可查看
使用示例：
添加金币 2997036064 10
添加管理员 2149969203"""

        yield event.plain_result(admin_menu)
    
    async def _add_admin(self, event, target_id):
        """根管理员才能加群管"""
        user_id = str(event.get_sender_id())
        group_id = str(event.message_obj.group_id)
        if not self.is_admin(user_id):
            yield event.plain_result("❌ 只有根管理员才能添加群管理员")
            return
        data = self._load_admin_list()
        grp = data.setdefault(group_id, [])
        if target_id in grp:
            yield event.plain_result("⚠️ 该用户已是本群管理员")
            return
        grp.append(target_id)
        self._save_admin_list(data)
        yield event.plain_result(f"✅ 已添加 {target_id} 为本群牛牛管理员")

    async def _del_admin(self, event, target_id):
        """根管理员才能删群管"""
        user_id = str(event.get_sender_id())
        group_id = str(event.message_obj.group_id)
        if not self.is_admin(user_id):
            yield event.plain_result("❌ 只有根管理员才能删除群管理员")
            return
        data = self._load_admin_list()
        grp = data.get(group_id, [])
        if target_id not in grp:
            yield event.plain_result("⚠️ 该用户不是本群管理员")
            return
        grp.remove(target_id)
        self._save_admin_list(data)
        yield event.plain_result(f"✅ 已删除 {target_id} 的本群牛牛管理员权限")

    async def _list_admin(self, event):
        """列出本群所有管理员"""
        group_id = str(event.message_obj.group_id)
        root_admins = [q for q in self.admins]          # 全局
        local_admins  = self._load_admin_list().get(group_id, [])
        msg = ["👑 牛牛管理员列表："]
        if root_admins:
            msg.append("【根管理员】")
            msg.extend(f"  - {q}" for q in root_admins)
        if local_admins:
            msg.append("【本群管理员】")
            msg.extend(f"  - {q}" for q in local_admins)
        if not root_admins and not local_admins:
            msg.append("  暂无管理员")
        yield event.plain_result("\n".join(msg))

    async def _admin_add_gold(self, event, target_id, amount):
        """管理员添加金币"""
        group_id = str(event.message_obj.group_id)
        user_id = str(event.get_sender_id())

        # 检查是否为管理员
        if not self.is_admin(user_id):
            yield event.plain_result("❌ 只有管理员才能使用此功能")
            return

        # 获取目标用户数据
        target_data = self.get_user_data(group_id, target_id)
        if not target_data:
            yield event.plain_result(f"❌ 用户 {target_id} 未注册牛牛")
            return

        # 添加金币
        current_coins = target_data.get('coins', 0)
        updated_data = {'coins': current_coins + int(amount)}
        self.update_user_data(group_id, target_id, updated_data)

        yield event.plain_result(f"✅ 成功给用户 {target_data['nickname']} 添加 {amount} 金币\n当前金币：{current_coins + int(amount)}")

    async def _admin_add_length(self, event, target_id, amount):
        print("已经进入_admin_add_length方法")
        """管理员添加长度"""
        group_id = str(event.message_obj.group_id)
        user_id = str(event.get_sender_id())

        # 检查是否为管理员
        if not self.is_admin(user_id):
            yield event.plain_result("❌ 只有管理员才能使用此功能")
            return

        # 获取目标用户数据
        target_data = self.get_user_data(group_id, target_id)
        if not target_data:
            yield event.plain_result(f"❌ 用户 {target_id} 未注册牛牛")
            return

        # 添加长度
        current_length = target_data.get('length', 0)
        updated_data = {'length': current_length + int(amount)}
        self.update_user_data(group_id, target_id, updated_data)

        yield event.plain_result(f"✅ 成功给用户 {target_data['nickname']} 添加 {amount}cm 长度\n当前长度：{self.format_length(current_length + int(amount))}")

    async def _admin_add_hardness(self, event, target_id, amount):
        """管理员添加硬度"""
        group_id = str(event.message_obj.group_id)
        user_id = str(event.get_sender_id())

        # 检查是否为管理员
        if not self.is_admin(user_id):
            yield event.plain_result("❌ 只有管理员才能使用此功能")
            return

        # 获取目标用户数据
        target_data = self.get_user_data(group_id, target_id)
        if not target_data:
            yield event.plain_result(f"❌ 用户 {target_id} 未注册牛牛")
            return

        # 添加硬度
        current_hardness = target_data.get('hardness', 0)
        updated_data = {'hardness': current_hardness + int(amount)}
        self.update_user_data(group_id, target_id, updated_data)

        yield event.plain_result(f"✅ 成功给用户 {target_data['nickname']} 添加 {amount} 点硬度\n当前硬度：{current_hardness + int(amount)}")

    async def _admin_add_item(self, event, target_id, item_name, amount):
        """管理员添加道具"""
        group_id = str(event.message_obj.group_id)
        user_id = str(event.get_sender_id())

        # 检查是否为管理员
        if not self.is_admin(user_id):
            yield event.plain_result("❌ 只有管理员才能使用此功能")
            return

        # 获取目标用户数据
        target_data = self.get_user_data(group_id, target_id)
        if not target_data:
            yield event.plain_result(f"❌ 用户 {target_id} 未注册牛牛")
            return

        # 添加道具
        current_items = self.shop.get_user_items(group_id, target_id)
        current_amount = current_items.get(item_name, 0)
        self.shop.add_item(group_id, target_id, item_name, int(amount))

        yield event.plain_result(f"✅ 成功给用户 {target_data['nickname']} 添加 {amount} 个 {item_name}\n当前数量：{current_amount + int(amount)}")

    async def _admin_reset_user(self, event, target_id):
        """管理员重置用户数据"""
        group_id = str(event.message_obj.group_id)
        user_id = str(event.get_sender_id())

        # 检查是否为管理员
        if not self.is_admin(user_id):
            yield event.plain_result("❌ 只有管理员才能使用此功能")
            return

        # 获取目标用户数据
        target_data = self.get_user_data(group_id, target_id)
        if not target_data:
            yield event.plain_result(f"❌ 用户 {target_id} 未注册牛牛")
            return

        # 重置用户数据
        reset_data = {'length': 10,'hardness': 10,'coins': 0,'nickname': target_data['nickname']}
        self.update_user_data(group_id, target_id, reset_data)

        # 清空道具
        self.shop.clear_user_items(group_id, target_id)

        yield event.plain_result(f"✅ 成功重置用户 {target_data['nickname']} 的数据")

    async def _admin_view_user(self, event, target_id):
        """管理员查看用户数据"""
        group_id = str(event.message_obj.group_id)
        user_id = str(event.get_sender_id())

        # 检查是否为管理员
        if not self.is_admin(user_id):
            yield event.plain_result("❌ 只有管理员才能使用此功能")
            return

        # 获取目标用户数据
        target_data = self.get_user_data(group_id, target_id)
        if not target_data:
            yield event.plain_result(f"❌ 用户 {target_id} 未注册牛牛")
            return

        # 获取用户道具
        user_items = self.shop.get_user_items(group_id, target_id)
        items_str = "\n".join(
            [f"  - {item}: {count}" for item, count in user_items.items() if count > 0])
        if not items_str:
            items_str = "  无道具"

        user_info = f"""👑 用户详细信息：👤 昵称：{target_data['nickname']} 📏 长度：{self.format_length(target_data['length'])} 💪 硬度：{target_data.get('hardness', 1)} 💰 金币：{target_data.get('coins', 0)} 📦 道具：{items_str}"""

        yield event.plain_result(user_info)
