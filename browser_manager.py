import logging
import time

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)


class _LoggedInCondition:
    """检测登录状态的条件类。"""

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

    def __init__(self, cookie_names=None):
        self.cookie_names = cookie_names or ["__zp_stoken__", "wt2"]

    def __call__(self, driver):
        try:
            if self.cookie_names:
                names = {c.get("name") for c in (driver.get_cookies() or [])}
                if any(n in names for n in self.cookie_names):
                    return True

            for by, selector in self.LOGOUT_SELECTORS:
                try:
                    el = driver.find_element(by, selector)
                    if el.is_displayed():
                        return True
                except NoSuchElementException:
                    continue

            for by, selector in self.LOGIN_INDICATORS:
                try:
                    el = driver.find_element(by, selector)
                    if el.is_displayed():
                        return True
                except NoSuchElementException:
                    continue

            current_url = driver.current_url or ""
            if "zhipin.com" in current_url and "/web/chat/recommend" in current_url:
                return True

        except Exception:
            pass
        return False


class BrowserManager:
    """浏览器管理类，负责浏览器生命周期和基础操作。"""

    def __init__(self, driver_path=None, user_data_dir=None, debug_port=9222):
        self.driver = self._create_driver(driver_path, user_data_dir, debug_port)

    def _create_driver(self, driver_path, user_data_dir, debug_port):
        """创建并配置 WebDriver。若调试端口上已有浏览器则复用，否则启动新浏览器并开启调试端口。"""
        # 先尝试连接已有浏览器（上次脚本未关窗口时可直接复用）
        if debug_port:
            try:
                attach_options = webdriver.ChromeOptions()
                attach_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
                driver = webdriver.Chrome(options=attach_options) if not driver_path else webdriver.Chrome(executable_path=driver_path, options=attach_options)
                driver.maximize_window()
                logger.info("已连接已有浏览器")
                return driver
            except Exception:
                pass

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-software-rasterizer")
        if debug_port:
            chrome_options.add_argument(f"--remote-debugging-port={debug_port}")

        if user_data_dir:
            chrome_options.add_argument(f"--user-data-dir={user_data_dir}")

        try:
            if driver_path:
                driver = webdriver.Chrome(executable_path=driver_path, options=chrome_options)
            else:
                driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            err_msg = str(e).lower()
            if user_data_dir and ("user data" in err_msg or "already in use" in err_msg or "lock" in err_msg or "profile" in err_msg):
                raise RuntimeError(
                    "启动浏览器失败：当前用户数据目录已被占用。请先关闭占用该目录的 Chrome 窗口，或确认已配置 debug_port 以复用浏览器。\n"
                    f"用户数据目录: {user_data_dir}"
                ) from e
            raise RuntimeError("启动浏览器失败") from e

        driver.maximize_window()
        return driver

    def get(self, url):
        """访问指定 URL。"""
        self.driver.get(url)

    @property
    def current_url(self):
        """获取当前 URL。"""
        return self.driver.current_url

    @property
    def window_handles(self):
        """获取所有窗口句柄。"""
        return self.driver.window_handles

    def switch_to_window(self, handle):
        """切换到指定窗口。"""
        self.driver.switch_to.window(handle)

    def switch_to_frame(self, iframe):
        """切换到指定 iframe。"""
        self.driver.switch_to.frame(iframe)

    def switch_to_default_content(self):
        """切换回主文档。"""
        self.driver.switch_to.default_content()

    def find_element(self, by, selector):
        """查找单个元素。"""
        return self.driver.find_element(by, selector)

    def find_elements(self, by, selector):
        """查找多个元素。"""
        return self.driver.find_elements(by, selector)

    def wait_for_element(self, by, selector, timeout=10):
        """等待元素出现。"""
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, selector))
        )

    def wait_for_login(self, timeout=300, cookie_names=None):
        """等待用户登录完成。"""
        from selenium.common.exceptions import TimeoutException
        try:
            WebDriverWait(self.driver, timeout, poll_frequency=0.5).until(
                _LoggedInCondition(cookie_names=cookie_names)
            )
            return True
        except TimeoutException:
            return False

    def execute_script(self, script, *args):
        """执行 JavaScript。"""
        return self.driver.execute_script(script, *args)

    def safe_click(self, element):
        """尝试点击元素，失败时改用 JavaScript 点击。"""
        try:
            element.click()
            return True
        except Exception:
            try:
                self.driver.execute_script("arguments[0].click();", element)
                return True
            except Exception:
                return False

    def click_by_text(self, text):
        """通过文本查找并点击元素。"""
        try:
            el = self.driver.find_element(By.XPATH, f"//*[contains(text(), '{text}')]")
            if not (el.is_displayed() and el.is_enabled()):
                return False
            if self.safe_click(el):
                time.sleep(0.2)
                return True
        except NoSuchElementException:
            pass
        return False

    def close(self):
        """关闭浏览器。"""
        try:
            self.driver.quit()
            logger.info("浏览器已关闭")
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
