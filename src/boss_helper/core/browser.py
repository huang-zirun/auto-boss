"""
浏览器管理模块

提供浏览器实例的创建、连接和管理功能。
"""
import logging
import socket
from typing import Any, List, Optional

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ..config.settings import BrowserSettings
from ..core.exceptions import (
    BrowserError,
    ElementNotFoundError,
    LoginTimeoutError,
)
from .exceptions import BossHelperError

logger = logging.getLogger(__name__)


class _LoggedInCondition:
    """
    登录状态检测条件类
    
    用于 WebDriverWait 等待登录完成。
    """
    
    LOGOUT_SELECTORS = [
        (By.CSS_SELECTOR, "a.link-signout"),
        (By.XPATH, "//a[contains(text(), '退出登录')]"),
        (By.XPATH, "//*[contains(text(), '退出登录')]"),
    ]
    
    LOGIN_INDICATORS = [
        (By.CSS_SELECTOR, ".user-info"),
        (By.CSS_SELECTOR, ".user-name"),
        (By.CSS_SELECTOR, ".avatar"),
        (By.XPATH, "//div[contains(@class, 'user')]"),
    ]
    
    def __init__(self, cookie_names: Optional[List[str]] = None):
        self.cookie_names = cookie_names or ["__zp_stoken__", "wt2"]
    
    def __call__(self, driver: Any) -> bool:
        try:
            if self._check_cookies(driver):
                return True
            if self._check_selectors(driver, self.LOGOUT_SELECTORS):
                return True
            if self._check_selectors(driver, self.LOGIN_INDICATORS):
                return True
            url = driver.current_url or ""
            if "zhipin.com" in url and "/web/chat/recommend" in url:
                return True
        except Exception:
            pass
        return False
    
    def _check_cookies(self, driver: Any) -> bool:
        if not self.cookie_names:
            return False
        try:
            names = {c.get("name") for c in (driver.get_cookies() or [])}
            return any(n in names for n in self.cookie_names)
        except Exception:
            return False
    
    def _check_selectors(
        self,
        driver: Any,
        selectors: List[tuple]
    ) -> bool:
        for by, selector in selectors:
            try:
                el = driver.find_element(by, selector)
                if el.is_displayed():
                    return True
            except NoSuchElementException:
                continue
        return False


class BrowserManager:
    """
    浏览器管理器
    
    负责浏览器的创建、连接和基本操作。
    """
    
    def __init__(self, settings: Optional[BrowserSettings] = None):
        """
        初始化浏览器管理器
        
        Args:
            settings: 浏览器配置，为 None 则使用默认配置
        """
        self._settings = settings or BrowserSettings()
        self._driver: Optional[webdriver.Chrome] = None
    
    @property
    def driver(self) -> webdriver.Chrome:
        """
        获取 WebDriver 实例
        
        Returns:
            Chrome WebDriver 实例
        """
        if self._driver is None:
            self._driver = self._create_driver()
        return self._driver
    
    @staticmethod
    def _is_port_open(host: str, port: int, timeout: float = 2.0) -> bool:
        """
        检查端口是否开放
        
        Args:
            host: 主机地址
            port: 端口号
            timeout: 超时时间
        
        Returns:
            True 表示端口开放
        """
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (socket.timeout, socket.error, OSError):
            return False
    
    def _create_driver(self) -> webdriver.Chrome:
        """
        创建 WebDriver 实例
        
        Returns:
            Chrome WebDriver 实例
        
        Raises:
            BrowserError: 创建失败
        """
        settings = self._settings
        debug_port = settings.debug_port
        
        if debug_port and self._is_port_open("127.0.0.1", debug_port):
            try:
                options = webdriver.ChromeOptions()
                options.add_experimental_option(
                    "debuggerAddress",
                    f"127.0.0.1:{debug_port}"
                )
                driver = self._init_chrome(options, settings.driver_path)
                driver.maximize_window()
                logger.info("已连接到已有浏览器实例")
                return driver
            except Exception as e:
                logger.debug(f"连接已有浏览器失败: {e}")
        
        options = webdriver.ChromeOptions()
        
        for arg in [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-software-rasterizer",
        ]:
            options.add_argument(arg)
        
        if debug_port:
            options.add_argument(f"--remote-debugging-port={debug_port}")
        
        if settings.user_data_dir:
            options.add_argument(f"--user-data-dir={settings.user_data_dir}")
        
        if settings.headless:
            options.add_argument("--headless=new")
        
        try:
            driver = self._init_chrome(options, settings.driver_path)
            driver.maximize_window()
            logger.info("浏览器实例已创建")
            return driver
        except WebDriverException as e:
            err_msg = str(e).lower()
            if settings.user_data_dir and any(
                k in err_msg for k in ["user data", "already in use", "lock", "profile"]
            ):
                raise BrowserError(
                    "启动浏览器失败：用户数据目录已被占用",
                    {"user_data_dir": settings.user_data_dir}
                ) from e
            raise BrowserError("启动浏览器失败") from e
    
    def _init_chrome(
        self,
        options: webdriver.ChromeOptions,
        driver_path: str
    ) -> webdriver.Chrome:
        """
        初始化 Chrome 浏览器
        
        Args:
            options: Chrome 选项
            driver_path: ChromeDriver 路径
        
        Returns:
            Chrome WebDriver 实例
        """
        if driver_path:
            return webdriver.Chrome(
                executable_path=driver_path,
                options=options
            )
        return webdriver.Chrome(options=options)
    
    def get(self, url: str) -> None:
        """
        导航到指定 URL
        
        Args:
            url: 目标 URL
        """
        self.driver.get(url)
    
    @property
    def current_url(self) -> str:
        """当前页面 URL"""
        return self.driver.current_url
    
    @property
    def window_handles(self) -> List[str]:
        """所有窗口句柄"""
        return self.driver.window_handles
    
    def switch_to_window(self, handle: str) -> None:
        """
        切换到指定窗口
        
        Args:
            handle: 窗口句柄
        """
        self.driver.switch_to.window(handle)
    
    def switch_to_frame(self, iframe: Any) -> None:
        """
        切换到 iframe
        
        Args:
            iframe: iframe 元素或索引
        """
        self.driver.switch_to.frame(iframe)
    
    def switch_to_default_content(self) -> None:
        """切换回主文档"""
        self.driver.switch_to.default_content()
    
    def find_element(
        self,
        by: str,
        selector: str
    ) -> Any:
        """
        查找单个元素
        
        Args:
            by: 定位方式
            selector: 选择器
        
        Returns:
            WebElement
        
        Raises:
            ElementNotFoundError: 元素未找到
        """
        try:
            return self.driver.find_element(by, selector)
        except NoSuchElementException:
            raise ElementNotFoundError(selector, by)
    
    def find_elements(
        self,
        by: str,
        selector: str
    ) -> List[Any]:
        """
        查找多个元素
        
        Args:
            by: 定位方式
            selector: 选择器
        
        Returns:
            WebElement 列表
        """
        return self.driver.find_elements(by, selector)
    
    def wait_for_element(
        self,
        by: str,
        selector: str,
        timeout: float = 10.0
    ) -> Any:
        """
        等待元素出现
        
        Args:
            by: 定位方式
            selector: 选择器
            timeout: 超时时间
        
        Returns:
            WebElement
        
        Raises:
            ElementNotFoundError: 元素未找到
        """
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
        except TimeoutException:
            raise ElementNotFoundError(selector, by)
    
    def wait_for_login(
        self,
        timeout: int = 300,
        cookie_names: Optional[List[str]] = None,
        poll_interval: float = 2.0
    ) -> bool:
        """
        等待用户完成登录
        
        Args:
            timeout: 超时时间（秒）
            cookie_names: 用于检测登录的 Cookie 名称
            poll_interval: 轮询间隔（秒）
        
        Returns:
            True 表示登录成功
        
        Raises:
            LoginTimeoutError: 登录超时
        """
        try:
            WebDriverWait(
                self.driver,
                timeout,
                poll_frequency=poll_interval
            ).until(_LoggedInCondition(cookie_names))
            return True
        except TimeoutException:
            raise LoginTimeoutError(timeout)
    
    def execute_script(self, script: str, *args) -> Any:
        """
        执行 JavaScript 脚本
        
        Args:
            script: 脚本内容
            *args: 脚本参数
        
        Returns:
            脚本返回值
        """
        return self.driver.execute_script(script, *args)
    
    def safe_click(self, element: Any) -> bool:
        """
        安全点击元素
        
        尝试多种方式点击，提高成功率。
        
        Args:
            element: 要点击的元素
        
        Returns:
            True 表示点击成功
        """
        try:
            element.click()
            return True
        except Exception:
            try:
                self.driver.execute_script("arguments[0].click();", element)
                return True
            except Exception:
                return False
    
    def click_by_text(self, text: str) -> bool:
        """
        通过文本点击元素
        
        Args:
            text: 元素文本
        
        Returns:
            True 表示点击成功
        """
        try:
            el = self.driver.find_element(
                By.XPATH,
                f"//*[contains(text(), '{text}')]"
            )
            if el.is_displayed() and el.is_enabled() and self.safe_click(el):
                return True
        except NoSuchElementException:
            pass
        return False
    
    def close(self) -> None:
        """关闭浏览器"""
        if self._driver is not None:
            try:
                self._driver.quit()
                logger.info("浏览器已关闭")
            except Exception:
                pass
            finally:
                self._driver = None
    
    def __enter__(self) -> "BrowserManager":
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
