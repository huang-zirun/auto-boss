import logging
import socket

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)


class _LoggedInCondition:
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

    def _check_cookies(self, driver):
        if not self.cookie_names:
            return False
        names = {c.get("name") for c in (driver.get_cookies() or [])}
        return any(n in names for n in self.cookie_names)

    def _check_selectors(self, driver, selectors):
        for by, selector in selectors:
            try:
                if driver.find_element(by, selector).is_displayed():
                    return True
            except NoSuchElementException:
                continue
        return False


class BrowserManager:
    def __init__(self, driver_path=None, user_data_dir=None, debug_port=9222):
        self.driver = self._create_driver(driver_path, user_data_dir, debug_port)

    @staticmethod
    def _is_port_open(host, port, timeout=2):
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (socket.timeout, socket.error, OSError):
            return False

    def _create_driver(self, driver_path, user_data_dir, debug_port):
        if debug_port and self._is_port_open("127.0.0.1", debug_port):
            try:
                options = webdriver.ChromeOptions()
                options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
                driver = webdriver.Chrome(executable_path=driver_path, options=options) if driver_path else webdriver.Chrome(options=options)
                driver.maximize_window()
                logger.info("已连接已有浏览器")
                return driver
            except Exception:
                pass

        options = webdriver.ChromeOptions()
        for arg in ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--disable-software-rasterizer"]:
            options.add_argument(arg)
        if debug_port:
            options.add_argument(f"--remote-debugging-port={debug_port}")
        if user_data_dir:
            options.add_argument(f"--user-data-dir={user_data_dir}")

        try:
            driver = webdriver.Chrome(executable_path=driver_path, options=options) if driver_path else webdriver.Chrome(options=options)
        except Exception as e:
            err_msg = str(e).lower()
            if user_data_dir and any(k in err_msg for k in ["user data", "already in use", "lock", "profile"]):
                raise RuntimeError(f"启动浏览器失败：用户数据目录已被占用\n{user_data_dir}") from e
            raise RuntimeError("启动浏览器失败") from e

        driver.maximize_window()
        return driver

    def get(self, url):
        self.driver.get(url)

    @property
    def current_url(self):
        return self.driver.current_url

    @property
    def window_handles(self):
        return self.driver.window_handles

    def switch_to_window(self, handle):
        self.driver.switch_to.window(handle)

    def switch_to_frame(self, iframe):
        self.driver.switch_to.frame(iframe)

    def switch_to_default_content(self):
        self.driver.switch_to.default_content()

    def find_element(self, by, selector):
        return self.driver.find_element(by, selector)

    def find_elements(self, by, selector):
        return self.driver.find_elements(by, selector)

    def wait_for_element(self, by, selector, timeout=10):
        return WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((by, selector)))

    def wait_for_login(self, timeout=300, cookie_names=None):
        try:
            WebDriverWait(self.driver, timeout, poll_frequency=0.5).until(_LoggedInCondition(cookie_names))
            return True
        except TimeoutException:
            return False

    def execute_script(self, script, *args):
        return self.driver.execute_script(script, *args)

    def safe_click(self, element):
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
        try:
            el = self.driver.find_element(By.XPATH, f"//*[contains(text(), '{text}')]")
            if el.is_displayed() and el.is_enabled() and self.safe_click(el):
                return True
        except NoSuchElementException:
            pass
        return False

    def close(self):
        try:
            self.driver.quit()
            logger.info("浏览器已关闭")
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
