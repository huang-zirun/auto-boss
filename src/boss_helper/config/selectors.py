"""
选择器管理模块

提供选择器的加载、缓存和访问功能。
"""
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from ..core.exceptions import SelectorNotFoundError

logger = logging.getLogger(__name__)


class SelectorItem:
    """
    单个选择器项
    
    封装选择器的所有属性。
    """
    
    def __init__(
        self,
        selector: str,
        selector_type: str = "css",
        description: str = ""
    ):
        self.selector = selector
        self.selector_type = selector_type.lower()
        self.description = description
    
    def __repr__(self) -> str:
        return f"SelectorItem({self.selector_type}: {self.selector})"
    
    @property
    def by(self) -> str:
        """返回 Selenium By 类型"""
        from selenium.webdriver.common.by import By
        mapping = {
            "css": By.CSS_SELECTOR,
            "xpath": By.XPATH,
            "id": By.ID,
            "class": By.CLASS_NAME,
            "tag": By.TAG_NAME,
            "name": By.NAME,
        }
        return mapping.get(self.selector_type, By.CSS_SELECTOR)


class SelectorProvider:
    """
    选择器提供者
    
    从 YAML 文件加载选择器配置，提供便捷的访问方法。
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        初始化选择器提供者
        
        Args:
            config_path: 选择器配置文件路径，默认为内置配置
        """
        if config_path is None:
            config_path = Path(__file__).parent / "selectors.yaml"
        self._config_path = config_path
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """加载配置文件"""
        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}
            logger.info(f"选择器配置已加载: {self._config_path}")
        except FileNotFoundError:
            logger.warning(f"选择器配置文件不存在: {self._config_path}")
            self._config = {}
        except yaml.YAMLError as e:
            logger.error(f"选择器配置解析错误: {e}")
            self._config = {}
    
    def reload(self) -> None:
        """重新加载配置"""
        self._load_config()
    
    def get(
        self,
        page: str,
        element: str,
        default: Optional[Union[str, SelectorItem]] = None
    ) -> Union[SelectorItem, List[SelectorItem]]:
        """
        获取选择器
        
        Args:
            page: 页面名称（如 'recommend_page'）
            element: 元素名称（如 'greet_button'）
            default: 默认值
        
        Returns:
            SelectorItem 或 SelectorItem 列表
        
        Raises:
            SelectorNotFoundError: 选择器不存在且无默认值
        """
        page_config = self._config.get(page, {})
        
        keys = element.split(".")
        value = page_config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                value = None
                break
        
        if value is None:
            if default is not None:
                if isinstance(default, str):
                    return SelectorItem(default)
                return default
            raise SelectorNotFoundError(page, element)
        
        return self._parse_selector(value, page, element)
    
    def _parse_selector(
        self,
        value: Any,
        page: str,
        element: str
    ) -> Union[SelectorItem, List[SelectorItem]]:
        """解析选择器配置"""
        if isinstance(value, str):
            return SelectorItem(value)
        
        if isinstance(value, dict):
            selector = value.get("selector", "")
            selector_type = value.get("type", "css")
            description = value.get("description", "")
            return SelectorItem(selector, selector_type, description)
        
        if isinstance(value, list):
            items = []
            for item in value:
                if isinstance(item, str):
                    items.append(SelectorItem(item))
                elif isinstance(item, dict):
                    selector = item.get("selector", "")
                    selector_type = item.get("type", "css")
                    description = item.get("description", "")
                    items.append(SelectorItem(selector, selector_type, description))
            return items
        
        raise SelectorNotFoundError(page, element)
    
    def get_text(self, page: str, key: str) -> Optional[str]:
        """
        获取文本配置
        
        Args:
            page: 页面名称
            key: 配置键名
        
        Returns:
            配置的文本值
        """
        page_config = self._config.get(page, {})
        return page_config.get(key)
    
    def get_texts(self, page: str, key: str) -> List[str]:
        """
        获取文本列表配置
        
        Args:
            page: 页面名称
            key: 配置键名
        
        Returns:
            配置的文本列表
        """
        page_config = self._config.get(page, {})
        value = page_config.get(key, [])
        if isinstance(value, str):
            return [value]
        return list(value)


@lru_cache()
def get_selector_provider() -> SelectorProvider:
    """
    获取选择器提供者实例（单例）
    """
    return SelectorProvider()


def clear_selector_cache() -> None:
    """清除选择器缓存"""
    get_selector_provider.cache_clear()
