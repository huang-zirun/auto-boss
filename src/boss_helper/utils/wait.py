"""
智能等待策略模块

提供条件等待、智能重试等功能，替代硬编码的 time.sleep()。
"""
import logging
import time
from functools import wraps
from typing import Any, Callable, Optional, Tuple, Type, TypeVar, Union

logger = logging.getLogger(__name__)

T = TypeVar('T')


class SmartWait:
    """
    智能等待工具类
    
    提供多种等待策略，减少不必要的等待时间。
    """
    
    def __init__(
        self,
        timeout: float = 10.0,
        poll_interval: float = 0.5,
        ignored_exceptions: Tuple[Type[Exception], ...] = (Exception,)
    ):
        """
        初始化智能等待
        
        Args:
            timeout: 超时时间（秒）
            poll_interval: 轮询间隔（秒）
            ignored_exceptions: 忽略的异常类型
        """
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.ignored_exceptions = ignored_exceptions
    
    def until(
        self,
        condition: Callable[[], T],
        message: str = ""
    ) -> T:
        """
        等待条件满足
        
        Args:
            condition: 条件函数，返回非 None 或 True 表示满足
            message: 超时错误消息
        
        Returns:
            条件函数的返回值
        
        Raises:
            TimeoutError: 超时
        """
        deadline = time.time() + self.timeout
        last_exception: Optional[Exception] = None
        
        while time.time() < deadline:
            try:
                result = condition()
                if result is not None and result is not False:
                    return result
            except self.ignored_exceptions as e:
                last_exception = e
                logger.debug(f"等待条件异常: {e}")
            
            time.sleep(self.poll_interval)
        
        msg = message or f"等待超时 ({self.timeout}秒)"
        if last_exception:
            raise TimeoutError(f"{msg}: {last_exception}") from last_exception
        raise TimeoutError(msg)
    
    def until_not(
        self,
        condition: Callable[[], Any],
        message: str = ""
    ) -> bool:
        """
        等待条件不满足
        
        Args:
            condition: 条件函数
            message: 超时错误消息
        
        Returns:
            True 表示条件不再满足
        
        Raises:
            TimeoutError: 超时
        """
        deadline = time.time() + self.timeout
        
        while time.time() < deadline:
            try:
                result = condition()
                if not result:
                    return True
            except self.ignored_exceptions:
                return True
            
            time.sleep(self.poll_interval)
        
        msg = message or f"等待条件失效超时 ({self.timeout}秒)"
        raise TimeoutError(msg)
    
    def with_retry(
        self,
        func: Callable[[], T],
        max_attempts: int = 3,
        retry_interval: float = 1.0
    ) -> T:
        """
        带重试的执行
        
        Args:
            func: 要执行的函数
            max_attempts: 最大尝试次数
            retry_interval: 重试间隔
        
        Returns:
            函数返回值
        
        Raises:
            最后一次尝试的异常
        """
        last_exception: Optional[Exception] = None
        
        for attempt in range(1, max_attempts + 1):
            try:
                return func()
            except Exception as e:
                last_exception = e
                logger.warning(f"执行失败 (尝试 {attempt}/{max_attempts}): {e}")
                if attempt < max_attempts:
                    time.sleep(retry_interval)
        
        if last_exception:
            raise last_exception
        raise RuntimeError("未知错误")


def wait_for_condition(
    condition: Callable[[], T],
    timeout: float = 10.0,
    poll_interval: float = 0.5,
    message: str = ""
) -> T:
    """
    等待条件满足的便捷函数
    
    Args:
        condition: 条件函数
        timeout: 超时时间
        poll_interval: 轮询间隔
        message: 超时消息
    
    Returns:
        条件函数的返回值
    """
    return SmartWait(timeout, poll_interval).until(condition, message)


def wait_for_element_visible(
    driver: Any,
    selector: str,
    selector_type: str = "css",
    timeout: float = 10.0
) -> Any:
    """
    等待元素可见
    
    Args:
        driver: WebDriver 实例
        selector: 选择器
        selector_type: 选择器类型
        timeout: 超时时间
    
    Returns:
        WebElement
    """
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
    
    by = By.CSS_SELECTOR if selector_type.lower() == "css" else By.XPATH
    return WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located((by, selector))
    )


def wait_for_element_clickable(
    driver: Any,
    selector: str,
    selector_type: str = "css",
    timeout: float = 10.0
) -> Any:
    """
    等待元素可点击
    
    Args:
        driver: WebDriver 实例
        selector: 选择器
        selector_type: 选择器类型
        timeout: 超时时间
    
    Returns:
        WebElement
    """
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
    
    by = By.CSS_SELECTOR if selector_type.lower() == "css" else By.XPATH
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((by, selector))
    )


def wait_for_page_load(
    driver: Any,
    timeout: float = 30.0
) -> bool:
    """
    等待页面加载完成
    
    Args:
        driver: WebDriver 实例
        timeout: 超时时间
    
    Returns:
        True 表示加载完成
    """
    from selenium.webdriver.support.ui import WebDriverWait
    
    def page_loaded(d):
        return d.execute_script("return document.readyState") == "complete"
    
    return WebDriverWait(driver, timeout).until(page_loaded)
