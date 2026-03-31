import random
import time
from astrbot.api.all import At


class CompareHandler:
    """比划比划处理器"""

    def __init__(self, plugin):
        self.plugin = plugin

    async def handle(self, event):
        """处理比划命令"""
        group_id = str(event.message_obj.group_id)
        user_id = str(event.get_sender_id())
        nickname = event.get_sender_name()

        group_data = self.plugin.data_manager.get_group_data(group_id)
        if not group_data.get('plugin_enabled', False):
            yield event.plain_result("❌ 插件未启用")
            return

        # 获取自身数据
        user_data = self.plugin.data_manager.get_user_data(group_id, user_id)
        if not user_data:
            yield event.plain_result(self.plugin.text_manager.get_text('dajiao', 'not_registered').format(nickname=nickname))
            return

        # 解析目标
        target_id = self._parse_target(event)
        if not target_id:
            yield event.plain_result(self.plugin.text_manager.get_text('compare', 'no_target').format(nickname=nickname))
            return

        if target_id == user_id:
            yield event.plain_result(self.plugin.text_manager.get_text('compare', 'self_compare'))
            return

        # 获取目标数据
        target_data = self.plugin.data_manager.get_user_data(group_id, target_id)
        if not target_data:
            yield event.plain_result(self.plugin.text_manager.get_text('compare', 'target_not_registered'))
            return

        # 冷却检查
        last_actions = self.plugin.cooldown_manager.load_last_actions()
        compare_records = last_actions.setdefault(group_id, {}).setdefault(user_id, {})
        last_compare = compare_records.get(target_id, 0)
        on_cooldown, remaining = self.plugin.utils.check_cooldown(last_compare, self.plugin.config.COMPARE_COOLDOWN)
        if on_cooldown:
            mins = int(remaining // 60) + 1
            text = self.plugin.text_manager.get_text('compare', 'cooldown').format(
                nickname=nickname,
                remaining=mins
            )
            yield event.plain_result(text)
            return

        # 检查10分钟内比划次数
        last_compare_time = compare_records.get('last_time', 0)
        current_time = time.time()

        # 如果超过10分钟，重置计数
        if current_time - last_compare_time > 600:
            compare_records['count'] = 0
            compare_records['last_time'] = current_time
            self.plugin.cooldown_manager.update_last_actions(last_actions)

        compare_count = compare_records.get('count', 0)

        if compare_count >= 3:
            yield event.plain_result("❌ 10分钟内只能比划三次")
            return

        # 更新冷却时间和比划次数
        compare_records[target_id] = current_time
        compare_records['count'] = compare_count + 1
        self.plugin.cooldown_manager.update_last_actions(last_actions)

        # 检查是否持有夺心魔蝌蚪罐头
        user_items = self.plugin.shop.get_user_items(group_id, user_id)
        if user_items.get("夺心魔蝌蚪罐头", 0) > 0:
            async for result in self._handle_mind_flayer(event, group_id, user_id, target_id, user_data, target_data, nickname):
                yield result
            return

        # 正常比划逻辑
        async for result in self._normal_compare(event, group_id, user_id, target_id, user_data, target_data, nickname):
            yield result

    def _parse_target(self, event):
        """解析@目标或用户名"""
        for comp in event.message_obj.message:
            if isinstance(comp, At):
                return str(comp.qq)
        msg = event.message_str.strip()
        if msg.startswith("比划比划"):
            target_name = msg[len("比划比划"):].strip()
            if target_name:
                group_id = str(event.message_obj.group_id)
                group_data = self.plugin.data_manager.get_group_data(group_id)
                import re
                for user_id, user_data in group_data.items():
                    if isinstance(user_data, dict):
                        nickname = user_data.get('nickname', '')
                        if re.search(re.escape(target_name), nickname, re.IGNORECASE):
                            return user_id
        return None

    async def _handle_mind_flayer(self, event, group_id, user_id, target_id, user_data, target_data, nickname):
        """处理夺心魔蝌蚪罐头效果"""
        effect_chance = random.random()
        is_admin_user = self.plugin.admin_manager.is_admin(user_id)

        if is_admin_user:
            # 管理员逻辑：50%夺取对方长度，50%无效
            if effect_chance < 0.5:
                original_target_length = target_data['length']
                self.plugin.data_manager.update_user_data(group_id, user_id, {'length': user_data['length'] + original_target_length})
                self.plugin.data_manager.update_user_data(group_id, target_id, {'length': 1})
                result_msg = [
                    "⚔️ 【牛牛对决结果】 ⚔️",
                    f"🎉 {nickname} 获得了夺心魔技能，夺取了 {target_data['nickname']} 的全部长度！",
                    f"🗡️ {nickname}: {self.plugin.utils.format_length(user_data['length'] - original_target_length)} → {self.plugin.utils.format_length(user_data['length'] + original_target_length)}",
                    f"🛡️ {target_data['nickname']}: {self.plugin.utils.format_length(original_target_length)} → 1cm"
                ]
                self.plugin.shop.consume_item(group_id, user_id, "夺心魔蝌蚪罐头")
            else:
                result_msg = [
                    "⚔️ 【牛牛对决结果】 ⚔️",
                    f"⚠️ {nickname} 使用夺心魔蝌蚪罐头，但是罐头好像坏掉了...",
                    f"🗡️ {nickname}: {self.plugin.utils.format_length(user_data['length'])}",
                    f"🛡️ {target_data['nickname']}: {self.plugin.utils.format_length(target_data['length'])}"
                ]
                self.plugin.shop.consume_item(group_id, user_id, "夺心魔蝌蚪罐头")
        else:
            # 普通用户逻辑：50%夺取，10%清空自己，40%无效
            if effect_chance < 0.5:
                original_target_length = target_data['length']
                self.plugin.data_manager.update_user_data(group_id, user_id, {'length': user_data['length'] + original_target_length})
                self.plugin.data_manager.update_user_data(group_id, target_id, {'length': 1})
                result_msg = [
                    "⚔️ 【牛牛对决结果】 ⚔️",
                    f"🎉 {nickname} 获得了夺心魔技能，夺取了 {target_data['nickname']} 的全部长度！",
                    f"🗡️ {nickname}: {self.plugin.utils.format_length(user_data['length'] - original_target_length)} → {self.plugin.utils.format_length(user_data['length'] + original_target_length)}",
                    f"🛡️ {target_data['nickname']}: {self.plugin.utils.format_length(original_target_length)} → 1cm"
                ]
                self.plugin.shop.consume_item(group_id, user_id, "夺心魔蝌蚪罐头")
            elif effect_chance < 0.6:
                self.plugin.data_manager.update_user_data(group_id, user_id, {'length': 1})
                result_msg = [
                    "⚔️ 【牛牛对决结果】 ⚔️",
                    f"💔 {nickname} 使用夺心魔蝌蚪罐头，牛牛变成了夺心魔！！！",
                    f"🗡️ {nickname}: {self.plugin.utils.format_length(user_data['length'])} → 1cm",
                    f"🛡️ {target_data['nickname']}: {self.plugin.utils.format_length(target_data['length'])}"
                ]
                self.plugin.shop.consume_item(group_id, user_id, "夺心魔蝌蚪罐头")
            else:
                result_msg = [
                    "⚔️ 【牛牛对决结果】 ⚔️",
                    f"⚠️ {nickname} 使用夺心魔蝌蚪罐头，但是罐头好像坏掉了...",
                    f"🗡️ {nickname}: {self.plugin.utils.format_length(user_data['length'])}",
                    f"🛡️ {target_data['nickname']}: {self.plugin.utils.format_length(target_data['length'])}"
                ]
                self.plugin.shop.consume_item(group_id, user_id, "夺心魔蝌蚪罐头")

        yield event.plain_result("\n".join(result_msg))

    async def _normal_compare(self, event, group_id, user_id, target_id, user_data, target_data, nickname):
        """正常比划逻辑"""
        u_len = user_data['length']
        t_len = target_data['length']
        u_hardness = user_data['hardness']
        t_hardness = target_data['hardness']

        # 基础胜率
        base_win = 0.5

        # 长度影响（最多影响20%的胜率）
        length_factor = (u_len - t_len) / max(u_len, t_len) * 0.2

        # 硬度影响（最多影响10%的胜率）
        hardness_factor = (u_hardness - t_hardness) * 0.05

        # 最终胜率（限制在20%-80%之间）
        win_prob = min(max(base_win + length_factor + hardness_factor, 0.2), 0.8)

        # 记录比划前的长度
        old_u_len = u_len
        old_t_len = t_len

        # 执行判定
        if random.random() < win_prob:
            # 用户获胜
            gain = random.randint(0, 3)
            loss = random.randint(1, 2)
            total_gain = gain
            updated_user = {'length': user_data['length'] + gain}
            updated_target = {'length': max(1, target_data['length'] - loss)}

            text = random.choice(self.plugin.text_manager.get_text('compare', 'win')).format(
                nickname=nickname,
                target_nickname=target_data['nickname'],
                gain=gain
            )

            # 检查淬火爪刀
            user_items = self.plugin.shop.get_user_items(group_id, user_id)
            if user_items.get("淬火爪刀", 0) > 0 and abs(u_len - t_len) > 10 and u_len < t_len:
                extra_loot = int(target_data['length'] * 0.1)
                updated_user['length'] += extra_loot
                total_gain += extra_loot
                text += f"\n🔥 淬火爪刀触发！额外掠夺 {extra_loot}cm！"
                self.plugin.shop.consume_item(group_id, user_id, "淬火爪刀")

            # 极大劣势获胜
            if abs(u_len - t_len) >= 20 and user_data['hardness'] < target_data['hardness']:
                extra_gain = random.randint(0, 5)
                updated_user['length'] += extra_gain
                total_gain += extra_gain
                text += f"\n🎁 由于极大劣势获胜，额外增加 {extra_gain}cm！"

            # 掠夺机制
            if abs(u_len - t_len) > 10 and u_len < t_len:
                stolen_length = int(target_data['length'] * 0.2)
                updated_user['length'] += stolen_length
                updated_target['length'] = max(1, target_data['length'] - loss - stolen_length)
                total_gain += stolen_length
                text += f"\n🎉 {nickname} 掠夺了 {stolen_length}cm！"

            # 硬度优势
            if abs(u_len - t_len) <= 5 and user_data['hardness'] > target_data['hardness']:
                text += f"\n🎉 {nickname} 因硬度优势获胜！"

            if total_gain == 0:
                text += f"\n{self.plugin.text_manager.get_text('compare', 'user_no_increase').format(nickname=nickname)}"

            self.plugin.data_manager.update_user_data(group_id, user_id, updated_user)
            self.plugin.data_manager.update_user_data(group_id, target_id, updated_target)
        else:
            # 用户失败
            loss = random.randint(1, 2)
            gain = random.randint(0, 3)
            updated_user = {'length': max(1, user_data['length'] - loss)}
            updated_target = {'length': target_data['length'] + gain}

            text = random.choice(self.plugin.text_manager.get_text('compare', 'lose')).format(
                nickname=nickname,
                target_nickname=target_data['nickname'],
                loss=loss
            )

            self.plugin.data_manager.update_user_data(group_id, user_id, updated_user)
            self.plugin.data_manager.update_user_data(group_id, target_id, updated_target)

        # 双方缠绕判定
        if u_hardness < 3 and t_hardness < 3:
            if random.random() < 0.3:
                self.plugin.data_manager.update_user_data(group_id, user_id, {'length': max(1, old_u_len // 2)})
                self.plugin.data_manager.update_user_data(group_id, target_id, {'length': max(1, old_t_len // 2)})
                text = self.plugin.text_manager.get_text('compare', 'double_loss').format(
                    nickname1=nickname,
                    nickname2=target_data['nickname']
                )

        # 重新获取最新数据
        user_data = self.plugin.data_manager.get_user_data(group_id, user_id)
        target_data = self.plugin.data_manager.get_user_data(group_id, target_id)

        result_msg = [
            "⚔️ 【牛牛对决结果】 ⚔️",
            f"🗡️ {nickname}: {self.plugin.utils.format_length(old_u_len)} → {self.plugin.utils.format_length(user_data['length'])}",
            f"🛡️ {target_data['nickname']}: {self.plugin.utils.format_length(old_t_len)} → {self.plugin.utils.format_length(target_data['length'])}",
            text
        ]

        yield event.plain_result("\n".join(result_msg))
