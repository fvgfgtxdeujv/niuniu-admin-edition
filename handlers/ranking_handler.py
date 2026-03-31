class RankingHandler:
    """排行榜处理器"""

    def __init__(self, plugin):
        self.plugin = plugin

    async def handle(self, event):
        """处理排行榜命令"""
        group_id = str(event.message_obj.group_id)

        group_data = self.plugin.data_manager.get_group_data(group_id)
        if not group_data.get('plugin_enabled', False):
            yield event.plain_result("❌ 插件未启用")
            return

        # 收集所有用户数据
        user_list = []
        for user_id, user_data in group_data.items():
            if isinstance(user_data, dict) and 'length' in user_data:
                user_list.append(user_data)

        # 如果没有数据
        if not user_list:
            yield event.plain_result(self.plugin.text_manager.get_text('ranking', 'no_data'))
            return

        # 按长度降序排序
        user_list.sort(key=lambda x: x['length'], reverse=True)

        # 取前10名
        top10 = user_list[:10]

        # 生成排行榜文本
        header = self.plugin.text_manager.get_text('ranking', 'header')
        item_template = self.plugin.text_manager.get_text('ranking', 'item')

        result_lines = [header]
        for rank, user_data in enumerate(top10, start=1):
            length_str = self.plugin.utils.format_length(user_data['length'])
            result_lines.append(item_template.format(
                rank=rank,
                name=user_data.get('nickname', '未知'),
                length=length_str
            ))

        yield event.plain_result("\n".join(result_lines))
