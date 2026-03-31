"""
配置和常量
"""
import os

# 路径常量
PLUGIN_DIR = os.path.join('data', 'plugins', 'astrbot_plugin_niuniu')
os.makedirs(PLUGIN_DIR, exist_ok=True)

NIUNIU_LENGTHS_FILE = os.path.join('data', 'niuniu_lengths.yml')
NIUNIU_TEXTS_FILE = os.path.join(PLUGIN_DIR, 'niuniu_game_texts.yml')
LAST_ACTION_FILE = os.path.join(PLUGIN_DIR, 'last_actions.yml')

# 冷却时间常量（秒）
COOLDOWN_10_MIN = 600  # 10分钟
COOLDOWN_30_MIN = 1800  # 30分钟
COMPARE_COOLDOWN = 600  # 比划冷却
INVITE_LIMIT = 3  # 邀请次数限制

# 默认文本配置
DEFAULT_TEXTS = {
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
