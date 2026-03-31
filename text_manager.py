"""
文本管理模块
负责游戏文本的加载、合并和访问
"""
import yaml
import os
from typing import Dict, Any

from .config import NIUNIU_TEXTS_FILE, DEFAULT_TEXTS


class TextManager:
    """文本管理器"""
    
    def __init__(self, logger=None):
        self.logger = logger
        self.texts = self._load_texts()
    
    def _log_error(self, message: str):
        """记录错误日志"""
        if self.logger:
            self.logger.error(message)
    
    def _deep_merge(self, base: Dict, update: Dict) -> Dict:
        """深度合并字典"""
        for key, value in update.items():
            if isinstance(value, dict):
                base[key] = self._deep_merge(base.get(key, {}), value)
            else:
                base[key] = value
        return base
    
    def _load_texts(self) -> Dict[str, Any]:
        """加载游戏文本"""
        try:
            if os.path.exists(NIUNIU_TEXTS_FILE):
                with open(NIUNIU_TEXTS_FILE, 'r', encoding='utf-8') as f:
                    custom_texts = yaml.safe_load(f) or {}
                    return self._deep_merge(DEFAULT_TEXTS.copy(), custom_texts)
        except Exception as e:
            self._log_error(f"加载文本失败: {str(e)}")
        return DEFAULT_TEXTS.copy()
    
    def get_text(self, *keys) -> Any:
        """获取文本"""
        result = self.texts
        for key in keys:
            if isinstance(result, dict):
                result = result.get(key)
            else:
                return None
        return result
    
    def get_random_text(self, *keys) -> str:
        """获取随机文本（从列表中）"""
        import random
        text = self.get_text(*keys)
        if isinstance(text, list):
            return random.choice(text)
        return text or ""
