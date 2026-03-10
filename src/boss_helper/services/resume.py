"""
简历收集服务

封装自动收集简历的业务逻辑。
"""
import logging
import random
import time
from typing import Optional, Set

from selenium.common.exceptions import StaleElementReferenceException

from ..config.settings import Settings, get_settings
from ..core.browser import BrowserManager
from ..core.exceptions import LoginTimeoutError, RiskControlDetectedError
from ..pages.chat import ChatPage
from ..utils.helpers import random_sleep

logger = logging.getLogger(__name__)


class ResumeService:
    """
    简历收集服务
    
    提供自动收集简历的业务逻辑。
    """
    
    CHAT_PAGE_URL = "https://www.zhipin.com/web/chat/index"
    
    def __init__(
        self,
        browser: Optional[BrowserManager] = None,
        settings: Optional[Settings] = None
    ):
        """
        初始化简历收集服务
        
        Args:
            browser: 浏览器管理器
            settings: 配置实例
        """
        self._settings = settings or get_settings()
        self._browser = browser or BrowserManager(self._settings.browser)
        self._chat_page: Optional[ChatPage] = None
    
    @property
    def browser(self) -> BrowserManager:
        """获取浏览器管理器"""
        return self._browser
    
    @property
    def chat_page(self) -> ChatPage:
        """获取聊天页面对象"""
        if self._chat_page is None:
            self._chat_page = ChatPage(self._browser)
        return self._chat_page
    
    def login(
        self,
        url: Optional[str] = None,
        redirect_url: Optional[str] = None,
        wait_login_timeout: Optional[int] = None,
        login_page_wait: Optional[float] = None,
        login_poll_interval: Optional[float] = None
    ) -> None:
        """
        执行登录流程
        
        Args:
            url: 登录页面 URL
            redirect_url: 登录后跳转 URL
            wait_login_timeout: 登录超时时间
            login_page_wait: 登录页等待时间
            login_poll_interval: 登录轮询间隔
        """
        timing = self._settings.timing
        urls = self._settings.urls
        
        url = url or urls.login_url
        redirect_url = redirect_url or self.CHAT_PAGE_URL
        timeout = wait_login_timeout or timing.wait_login_timeout
        page_wait = login_page_wait if login_page_wait is not None else timing.login_page_wait_seconds
        poll_interval = login_poll_interval if login_poll_interval is not None else timing.login_poll_interval_seconds
        
        self._browser.get(url)
        
        if page_wait > 0:
            print(f"等待登录页稳定（{page_wait} 秒），请准备扫码...")
            time.sleep(page_wait)
        
        print("请完成登录...")
        
        try:
            self._browser.wait_for_login(
                timeout=timeout,
                poll_interval=poll_interval
            )
            print("已登录，跳转中...")
        except LoginTimeoutError:
            print("登录超时，尝试直接打开目标页面")
        
        self._browser.get(redirect_url)
        time.sleep(1)
        print("已打开目标页面")
    
    def run_once(
        self,
        wait_after_agree: float = 3,
        wait_after_preview: float = 2,
        wait_after_agree_min: Optional[float] = None,
        wait_after_agree_max: Optional[float] = None,
        wait_after_preview_min: Optional[float] = None,
        wait_after_preview_max: Optional[float] = None,
        resume_load_timeout: float = 30
    ) -> tuple:
        """
        执行一次简历收集
        
        Returns:
            (agree_ok, preview_ok, loaded_ok, download_ok)
        """
        if not self.chat_page.click_agree():
            return (False, False, False, False)
        
        if wait_after_agree_min is not None and wait_after_agree_max is not None:
            random_sleep(wait_after_agree_min, wait_after_agree_max)
        else:
            time.sleep(wait_after_agree)
        
        if not self.chat_page.click_preview_resume():
            return (True, False, False, False)
        
        if wait_after_preview_min is not None and wait_after_preview_max is not None:
            random_sleep(wait_after_preview_min, wait_after_preview_max)
        else:
            time.sleep(wait_after_preview)
        
        if not self.chat_page.wait_resume_loaded(timeout=resume_load_timeout):
            return (True, True, False, False)
        
        download_ok = self.chat_page.click_download()
        if download_ok:
            time.sleep(0.5)
            self.chat_page.click_close_preview()
            time.sleep(0.3)
        
        return (True, True, True, download_ok)
    
    def run_all_chats(
        self,
        max_count: Optional[int] = None,
        wait_after_click_chat: Optional[float] = None,
        interval_between_chats: Optional[float] = None,
        wait_after_agree: float = 3,
        resume_load_timeout: Optional[int] = None,
        scroll_step: int = 200,
        chat_interval_min: Optional[float] = None,
        chat_interval_max: Optional[float] = None,
        download_interval_min: Optional[float] = None,
        download_interval_max: Optional[float] = None,
        wait_after_agree_min: Optional[float] = None,
        wait_after_agree_max: Optional[float] = None,
        wait_after_preview_min: Optional[float] = None,
        wait_after_preview_max: Optional[float] = None
    ) -> int:
        """
        遍历所有会话收集简历
        
        Returns:
            收集的简历数量
        """
        resume_config = self._settings.resume
        
        max_count = max_count if max_count is not None else resume_config.resume_max_collect
        wait_after_click_chat = wait_after_click_chat or resume_config.resume_chat_interval
        interval_between_chats = interval_between_chats or resume_config.resume_chat_interval
        resume_load_timeout = resume_load_timeout or resume_config.resume_load_timeout
        chat_interval_min = chat_interval_min or resume_config.resume_chat_interval_min
        chat_interval_max = chat_interval_max or resume_config.resume_chat_interval_max
        download_interval_min = download_interval_min or resume_config.resume_download_interval_min
        download_interval_max = download_interval_max or resume_config.resume_download_interval_max
        wait_after_agree_min = wait_after_agree_min or resume_config.resume_wait_after_agree_min
        wait_after_agree_max = wait_after_agree_max or resume_config.resume_wait_after_agree_max
        wait_after_preview_min = wait_after_preview_min or resume_config.resume_wait_after_preview_min
        wait_after_preview_max = wait_after_preview_max or resume_config.resume_wait_after_preview_max
        
        time.sleep(1)
        
        collected = 0
        prev_count = 0
        no_new_rounds = 0
        processed_keys: Set[str] = set()
        
        use_random_chat = (
            chat_interval_min is not None and
            chat_interval_max is not None and
            chat_interval_max > chat_interval_min
        )
        
        use_random_download = (
            download_interval_min is not None and
            download_interval_max is not None and
            download_interval_max > download_interval_min
        )
        
        while True:
            if self.chat_page.is_risk_control_page():
                print("\n检测到风控验证页，请手动完成验证后按回车继续...")
                input()
            
            self.chat_page.scroll_chat_list_down(step=scroll_step)
            time.sleep(0.4)
            
            items = self.chat_page.get_chat_list_items()
            if not items:
                if prev_count == 0:
                    print("未找到会话列表")
                break
            
            prev_count = len(items)
            round_collected = 0
            
            if collected == 0 and prev_count > 0:
                print(f"当前可见 {len(items)} 个会话")
            
            for i, item in enumerate(items):
                if max_count and collected >= max_count:
                    break
                
                try:
                    name_key = self.chat_page.get_item_name_key(item)
                    if name_key and name_key in processed_keys:
                        continue
                    
                    try:
                        self._browser.execute_script(
                            "arguments[0].scrollIntoView({block: 'center', behavior: 'auto'});",
                            item
                        )
                        time.sleep(0.3)
                    except StaleElementReferenceException:
                        items = self.chat_page.get_chat_list_items()
                        if i >= len(items):
                            break
                        item = items[i]
                        name_key = self.chat_page.get_item_name_key(item)
                        if name_key and name_key in processed_keys:
                            continue
                    
                    try:
                        item.click()
                    except Exception:
                        try:
                            self._browser.execute_script("arguments[0].click();", item)
                        except Exception:
                            continue
                    
                    if use_random_chat:
                        random_sleep(chat_interval_min, chat_interval_max)
                    else:
                        time.sleep(wait_after_click_chat)
                    
                    if self.chat_page.is_risk_control_page():
                        print("\n检测到风控验证页，请手动完成验证后按回车继续...")
                        input()
                        continue
                    
                    if not self.chat_page.has_resume_agree_request():
                        if self.chat_page.has_already_requested_resume():
                            continue
                        
                        if self.chat_page.send_chat_message(ChatPage.MSG_ASK_RESUME):
                            time.sleep(0.5)
                            self.chat_page.click_request_resume_then_confirm()
                        
                        if use_random_chat:
                            random_sleep(chat_interval_min, chat_interval_max)
                        else:
                            time.sleep(interval_between_chats)
                        continue
                    
                    name_job = name_key
                    if not name_job:
                        try:
                            name_job = self.chat_page.get_item_name_key(item)
                        except Exception:
                            name_job = f"会话 {i+1}"
                    
                    print(f"\n[{collected + 1}] 检测到简历申请: {name_job}")
                    
                    agree_ok, preview_ok, loaded_ok, download_ok = self.run_once(
                        wait_after_agree=wait_after_agree,
                        resume_load_timeout=resume_load_timeout,
                        wait_after_agree_min=wait_after_agree_min,
                        wait_after_agree_max=wait_after_agree_max,
                        wait_after_preview_min=wait_after_preview_min,
                        wait_after_preview_max=wait_after_preview_max
                    )
                    
                    if download_ok:
                        collected += 1
                        round_collected += 1
                        if name_key:
                            processed_keys.add(name_key)
                        
                        print(f"已收集简历，累计 {collected} 份")
                        
                        if use_random_download:
                            delay = random.uniform(download_interval_min, download_interval_max)
                            time.sleep(delay)
                        
                        if self.chat_page.is_risk_control_page():
                            print("\n检测到风控验证页，请手动完成验证后按回车继续...")
                            input()
                    
                    try:
                        self._browser.driver.find_element(
                            self._browser.driver.find_element_by_tag_name.__self__.TAG_NAME,
                            "body"
                        ).send_keys("\x1b")
                        time.sleep(0.3)
                    except Exception:
                        pass
                    
                    if use_random_chat:
                        random_sleep(chat_interval_min, chat_interval_max)
                    else:
                        time.sleep(interval_between_chats)
                except StaleElementReferenceException:
                    items = self.chat_page.get_chat_list_items()
                    if i >= len(items):
                        break
                    continue
                except Exception:
                    time.sleep(0.5)
            
            if max_count and collected >= max_count:
                break
            
            if round_collected == 0:
                no_new_rounds += 1
                if no_new_rounds >= 3:
                    break
            else:
                no_new_rounds = 0
            
            self.chat_page.scroll_chat_list_down(step=scroll_step * 2)
            time.sleep(0.3)
        
        print(f"\n完成，共收集 {collected} 份简历")
        return collected
    
    def close(self) -> None:
        """关闭服务"""
        self._browser.close()
    
    def __enter__(self) -> "ResumeService":
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


def main() -> None:
    """主入口函数"""
    settings = get_settings()
    
    with ResumeService(settings=settings) as service:
        service.login(
            url=settings.urls.login_url,
            redirect_url=settings.urls.chat_page_url,
            wait_login_timeout=settings.timing.wait_login_timeout,
            login_page_wait=settings.timing.login_page_wait_seconds,
            login_poll_interval=settings.timing.login_poll_interval_seconds
        )
        
        service.run_all_chats(
            max_count=settings.resume.resume_max_collect,
            wait_after_click_chat=settings.resume.resume_chat_interval,
            interval_between_chats=settings.resume.resume_chat_interval,
            wait_after_agree=3,
            resume_load_timeout=settings.resume.resume_load_timeout,
            chat_interval_min=settings.resume.resume_chat_interval_min,
            chat_interval_max=settings.resume.resume_chat_interval_max,
            download_interval_min=settings.resume.resume_download_interval_min,
            download_interval_max=settings.resume.resume_download_interval_max,
            wait_after_agree_min=settings.resume.resume_wait_after_agree_min,
            wait_after_agree_max=settings.resume.resume_wait_after_agree_max,
            wait_after_preview_min=settings.resume.resume_wait_after_preview_min,
            wait_after_preview_max=settings.resume.resume_wait_after_preview_max
        )


if __name__ == "__main__":
    main()
