"""Token计算器模块：计算文本的token数量并提供AI模型的上下文限制信息。"""
import re
from typing import List, Dict, Any


class TokenCalculator:
    """Token计算器，支持多种AI模型的token限制"""

    # 各AI模型的上下文长度限制（以token为单位）
    MODEL_LIMITS = {
        "gemini": {
            "gemini-pro": 131072,  # 32K
            "gemini-pro-vision": 131072,  # 16K
        },
        "siliconflow": {
            "deepseek-ai/DeepSeek-V2.5": 131072,  # 32K
            "Qwen/Qwen2-7B-Instruct": 131072,  # 32K
            "Qwen/Qwen2-72B-Instruct": 131072,  # 32K
        },
        "deepseek": {
            "deepseek-chat": 131072,  # 32K
        },
        "grok": {
            "grok-beta": 131072,  # 128K
        },
    }

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """改进的token数量估算（基于字符数和语言特征）"""
        if not text:
            return 0
        
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 对于中文内容，更准确的估算
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        numbers_and_symbols = len(text) - chinese_chars - english_chars
        
        # 中文字符：平均每个汉字约2-3个token
        # 英文字符：平均4个字符约1个token
        # 数字和符号：与英文类似
        chinese_tokens = chinese_chars * 2.5  # 中文更保守的估算
        english_tokens = (english_chars + numbers_and_symbols) / 4.0
        
        total_tokens = chinese_tokens + english_tokens
        
        # 确保至少1个token，且向上取整
        return max(1, int(total_tokens + 0.5))

    @classmethod
    def calculate_messages_tokens(cls, messages: List[Dict[str, Any]]) -> int:
        """计算消息列表的总token数"""
        total_tokens = 0
        for msg in messages:
            content = msg.get('content', '')
            total_tokens += cls.estimate_tokens(content)
        return total_tokens

    @classmethod
    def get_model_limit(cls, provider: str, model: str) -> int:
        """获取指定模型的token限制"""
        provider_limits = cls.MODEL_LIMITS.get(provider.lower(), {})
        return provider_limits.get(model, 131072)  # 默认128K

    @classmethod
    def check_token_usage(cls, messages: List[Dict[str, Any]], provider: str, model: str) -> Dict[str, Any]:
        """检查token使用情况"""
        total_tokens = cls.calculate_messages_tokens(messages)
        limit = cls.get_model_limit(provider, model)
        usage_percent = (total_tokens / limit) * 100 if limit > 0 else 0

        return {
            'total_tokens': total_tokens,
            'limit': limit,
            'usage_percent': usage_percent,
            'is_over_limit': total_tokens > limit,
            'warning_level': 'high' if usage_percent > 95 else 'medium' if usage_percent > 80 else 'low'
        }