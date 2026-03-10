"""
页面对象基类

提供页面对象的公共功能。
"""
import logging
from abc import ABC, abstractmethod
from typing import Any, List, Optional, Union

from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ..config.selectors import SelectorItem, SelectorProvider
from ..core.browser import BrowserManager
from ..core.exceptions import ElementNotFoundError
from ..utils.helpers import random_sleep, safe_click, scroll_into_view
from ..utils.wait import SmartWait

logger = logging.getLogger(__name__)


class BasePage(ABC):
    """
    页面对象基类
    
    所有页面对象的抽象基类，提供公共功能。
    """
    
    PAGE_NAME: str = ""
    
    def __init__(
        self,
        browser: BrowserManager,
        selectors: Optional[SelectorProvider] = None
    ):
        """
        初始化页面对象
        
        Args:
            browser: 浏览器管理器
            selectors: 选择器提供者
        """
        self._browser = browser
        self._selectors = selectors or SelectorProvider()
        self._wait = SmartWait()
    
    @property
    def driver(self) -> Any:
        """获取 WebDriver 实例"""
        return self._browser.driver
    
    @property
    def browser(self) -> BrowserManager:
        """获取浏览器管理器"""
        return self._browser
    
    def get_selector(
        self,
        element: str,
        default: Optional[str] = None
    ) -> Union[SelectorItem, List[SelectorItem]]:
        """
        获取选择器
        
        Args:
            element: 元素名称
            default: 默认选择器
        
        Returns:
            选择器项或选择器项列表
        """
        return self._selectors.get(self.PAGE_NAME, element, default)
    
    def find_element(
        self,
        selector_item: SelectorItem
    ) -> Any:
        """
        查找单个元素
        
        Args:
            selector_item: 选择器项
        
        Returns:
            WebElement
        
        Raises:
            ElementNotFoundError: 元素未找到
        """
        try:
            return self.driver.find_element(
                selector_item.by,
                selector_item.selector
            )
        except NoSuchElementException:
            raise ElementNotFoundError(
                selector_item.selector,
                selector_item.selector_type
            )
    
    def find_elements(
        self,
        selector_item: SelectorItem
    ) -> List[Any]:
        """
        查找多个元素
        
        Args:
            selector_item: 选择器项
        
        Returns:
            WebElement 列表
        """
        return self.driver.find_elements(
            selector_item.by,
            selector_item.selector
        )
    
    def try_find_element(
        self,
        selector_item: SelectorItem
    ) -> Optional[Any]:
        """
        尝试查找元素，失败返回 None
        
        Args:
            selector_item: 选择器项
        
        Returns:
            WebElement 或 None
        """
        try:
            return self.find_element(selector_item)
        except ElementNotFoundError:
            return None
    
    def wait_for_element(
        self,
        selector_item: SelectorItem,
        timeout: float = 10.0
    ) -> Any:
        """
        等待元素出现
        
        Args:
            selector_item: 选择器项
            timeout: 超时时间
        
        Returns:
            WebElement
        """
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(
                    (selector_item.by, selector_item.selector)
                )
            )
        except TimeoutException:
            raise ElementNotFoundError(
                selector_item.selector,
                selector_item.selector_type
            )
    
    def wait_for_element_visible(
        self,
        selector_item: SelectorItem,
        timeout: float = 10.0
    ) -> Any:
        """
        等待元素可见
        
        Args:
            selector_item: 选择器项
            timeout: 超时时间
        
        Returns:
            WebElement
        """
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(
                    (selector_item.by, selector_item.selector)
                )
            )
        except TimeoutException:
            raise ElementNotFoundError(
                selector_item.selector,
                selector_item.selector_type
            )
    
    def wait_for_element_clickable(
        self,
        selector_item: SelectorItem,
        timeout: float = 10.0
    ) -> Any:
        """
        等待元素可点击
        
        Args:
            selector_item: 选择器项
            timeout: 超时时间
        
        Returns:
            WebElement
        """
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable(
                    (selector_item.by, selector_item.selector)
                )
            )
        except TimeoutException:
            raise ElementNotFoundError(
                selector_item.selector,
                selector_item.selector_type
            )
    
    def click_element(
        self,
        element: Any,
        scroll_first: bool = True
    ) -> bool:
        """
        点击元素
        
        Args:
            element: 要点击的元素
            scroll_first: 是否先滚动到元素
        
        Returns:
            True 表示成功
        """
        try:
            if scroll_first:
                scroll_into_view(self.driver, element)
                random_sleep(0.1, 0.3)
            return safe_click(self.driver, element)
        except StaleElementReferenceException:
            return False
    
    def try_click_selectors(
        self,
        selectors: Union[SelectorItem, List[SelectorItem]]
    ) -> bool:
        """
        尝试多个选择器点击
        
        Args:
            selectors: 选择器项或选择器项列表
        
        Returns:
            True 表示任一成功
        """
        if isinstance(selectors, SelectorItem):
            selectors = [selectors]
        
        for selector_item in selectors:
            try:
                element = self.wait_for_element_clickable(selector_item, timeout=3)
                if self.click_element(element):
                    return True
            except (ElementNotFoundError, TimeoutException):
                continue
        
        return False
    
    def switch_to_default_content(self) -> None:
        """切换回主文档"""
        self._browser.switch_to_default_content()
    
    def switch_to_frame(self, frame: Any) -> None:
        """切换到 iframe"""
        self._browser.switch_to_frame(frame)
    
    @abstractmethod
    def is_loaded(self) -> bool:
        """
        检查页面是否已加载
        
        Returns:
            True 表示页面已加载
        """
        pass
