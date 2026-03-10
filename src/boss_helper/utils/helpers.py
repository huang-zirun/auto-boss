"""
辅助工具函数

提供常用的辅助功能。
"""
import logging
import random
import time
from typing import Any, Optional, Tuple, Union

logger = logging.getLogger(__name__)


def random_sleep(
    min_seconds: float,
    max_seconds: Optional[float] = None
) -> float:
    """
    随机等待
    
    Args:
        min_seconds: 最小等待时间
        max_seconds: 最大等待时间，为 None 则等于 min_seconds
    
    Returns:
        实际等待时间
    """
    if max_seconds is None:
        max_seconds = min_seconds
    
    if max_seconds < min_seconds:
        max_seconds = min_seconds
    
    actual = random.uniform(min_seconds, max_seconds)
    time.sleep(actual)
    return actual


def safe_click(
    driver: Any,
    element: Any,
    use_js_fallback: bool = True
) -> bool:
    """
    安全点击元素
    
    尝试多种方式点击元素，提高成功率。
    
    Args:
        driver: WebDriver 实例
        element: 要点击的元素
        use_js_fallback: 是否使用 JavaScript 回退
    
    Returns:
        True 表示点击成功
    """
    try:
        if element.is_displayed() and element.is_enabled():
            element.click()
            return True
    except Exception as e:
        logger.debug(f"常规点击失败: {e}")
        
        if use_js_fallback:
            try:
                driver.execute_script("arguments[0].click();", element)
                return True
            except Exception as js_e:
                logger.debug(f"JavaScript 点击失败: {js_e}")
    
    return False


def safe_send_keys(
    element: Any,
    text: str,
    clear_first: bool = True
) -> bool:
    """
    安全输入文本
    
    Args:
        element: 输入元素
        text: 要输入的文本
        clear_first: 是否先清空
    
    Returns:
        True 表示输入成功
    """
    try:
        if clear_first:
            element.clear()
        element.send_keys(text)
        return True
    except Exception as e:
        logger.debug(f"输入文本失败: {e}")
        return False


def scroll_into_view(
    driver: Any,
    element: Any,
    block: str = "center",
    behavior: str = "smooth"
) -> bool:
    """
    滚动到元素可见
    
    Args:
        driver: WebDriver 实例
        element: 目标元素
        block: 垂直对齐方式
        behavior: 滚动行为
    
    Returns:
        True 表示成功
    """
    try:
        driver.execute_script(
            f"arguments[0].scrollIntoView({{block: '{block}', behavior: '{behavior}'}});",
            element
        )
        return True
    except Exception as e:
        logger.debug(f"滚动到元素失败: {e}")
        return False


def get_element_text_safe(element: Any) -> str:
    """
    安全获取元素文本
    
    Args:
        element: 元素
    
    Returns:
        元素文本，失败返回空字符串
    """
    try:
        return (element.text or "").strip()
    except Exception:
        return ""


def is_element_displayed(element: Any) -> bool:
    """
    检查元素是否可见
    
    Args:
        element: 元素
    
    Returns:
        True 表示可见
    """
    try:
        return element.is_displayed()
    except Exception:
        return False


def is_element_enabled(element: Any) -> bool:
    """
    检查元素是否可用
    
    Args:
        element: 元素
    
    Returns:
        True 表示可用
    """
    try:
        return element.is_enabled()
    except Exception:
        return False


def format_duration(seconds: float) -> str:
    """
    格式化时长
    
    Args:
        seconds: 秒数
    
    Returns:
        格式化的时长字符串
    """
    if seconds < 60:
        return f"{seconds:.1f}秒"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}分{secs}秒"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}小时{minutes}分"


def truncate_text(text: str, max_length: int = 50) -> str:
    """
    截断文本
    
    Args:
        text: 原文本
        max_length: 最大长度
    
    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."
