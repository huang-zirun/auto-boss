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

    def __init__(self, cookie_names=None):
        self.cookie_names = cookie_names or ["__zp_stoken__"]

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
        except Exception:
            pass
        return False


class BrowserManager:
    """浏览器管理类，负责浏览器生命周期和基础操作。"""

    def __init__(self, driver_path=None, user_data_dir=None):
        self.driver = self._create_driver(driver_path, user_data_dir)

    def _create_driver(self, driver_path, user_data_dir):
        """创建并配置 WebDriver。"""
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-software-rasterizer")

        if user_data_dir:
            chrome_options.add_argument(f"--user-data-dir={user_data_dir}")

        try:
            if driver_path:
                driver = webdriver.Chrome(executable_path=driver_path, options=chrome_options)
            else:
                driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
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
            WebDriverWait(self.driver, timeout, poll_frequency=1).until(
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
