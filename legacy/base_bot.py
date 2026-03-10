import time
from abc import ABC, abstractmethod

from browser_manager import BrowserManager


class BaseBot(ABC):
    DEFAULT_LOGIN_URL = "https://www.zhipin.com/"
    DEFAULT_LOGIN_TIMEOUT = 300
    DEFAULT_LOGIN_PAGE_WAIT = 3.0
    DEFAULT_LOGIN_POLL_INTERVAL = 2.0

    def __init__(self, driver_path=None, user_data_dir=None, debug_port=9222):
        self.browser = BrowserManager(driver_path, user_data_dir, debug_port)

    def login(
        self,
        url=None,
        redirect_url=None,
        wait_login_timeout=None,
        login_cookie_names=None,
        login_page_wait=None,
        login_poll_interval=None,
    ):
        url = url or self.DEFAULT_LOGIN_URL
        redirect_url = redirect_url or self._get_default_redirect_url()
        timeout = wait_login_timeout or self.DEFAULT_LOGIN_TIMEOUT
        page_wait = login_page_wait if login_page_wait is not None else self.DEFAULT_LOGIN_PAGE_WAIT
        poll_interval = login_poll_interval if login_poll_interval is not None else self.DEFAULT_LOGIN_POLL_INTERVAL

        self.browser.get(url)
        if page_wait > 0:
            print(f"等待登录页稳定（{page_wait} 秒），请准备扫码...")
            time.sleep(page_wait)
        print("请完成登录...")
        if self.browser.wait_for_login(
            timeout=timeout, cookie_names=login_cookie_names, poll_interval=poll_interval
        ):
            print("已登录，跳转中...")
        else:
            print("登录超时，尝试直接打开目标页面")

        self.browser.get(redirect_url)
        time.sleep(1)
        self._after_login_redirect()
        print("已打开目标页面")

    @abstractmethod
    def _get_default_redirect_url(self):
        pass

    def _after_login_redirect(self):
        pass

    def close(self):
        self.browser.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
