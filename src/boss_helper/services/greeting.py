"""
打招呼服务

封装自动打招呼的业务逻辑。
"""
import logging
import random
import time
from typing import List, Optional

from selenium.common.exceptions import StaleElementReferenceException

from ..config.settings import Settings, get_settings
from ..core.browser import BrowserManager
from ..core.exceptions import LoginTimeoutError, RiskControlDetectedError
from ..pages.recommend import RecommendPage
from ..utils.helpers import random_sleep

logger = logging.getLogger(__name__)


class GreetingService:
    """
    打招呼服务
    
    提供自动打招呼的业务逻辑。
    """
    
    RECOMMEND_PAGE_URL = "https://www.zhipin.com/web/chat/recommend"
    
    def __init__(
        self,
        browser: Optional[BrowserManager] = None,
        settings: Optional[Settings] = None
    ):
        """
        初始化打招呼服务
        
        Args:
            browser: 浏览器管理器
            settings: 配置实例
        """
        self._settings = settings or get_settings()
        self._browser = browser or BrowserManager(self._settings.browser)
        self._recommend_page: Optional[RecommendPage] = None
    
    @property
    def browser(self) -> BrowserManager:
        """获取浏览器管理器"""
        return self._browser
    
    @property
    def recommend_page(self) -> RecommendPage:
        """获取推荐页面对象"""
        if self._recommend_page is None:
            self._recommend_page = RecommendPage(self._browser)
        return self._recommend_page
    
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
        redirect_url = redirect_url or self.RECOMMEND_PAGE_URL
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
        
        self._ensure_recommend_window(redirect_url)
        print("已打开目标页面")
    
    def _ensure_recommend_window(self, redirect_url: str) -> None:
        """确保在推荐页面窗口"""
        try:
            current = (self._browser.current_url or "").strip().lower()
            if current.startswith("data:") or "zhipin.com" not in current:
                for handle in self._browser.window_handles:
                    self._browser.switch_to_window(handle)
                    u = (self._browser.current_url or "").strip().lower()
                    if "zhipin.com" in u and ("recommend" in u or "chat" in u):
                        return
                self._browser.get(redirect_url)
                time.sleep(4)
        except Exception:
            pass
    
    def auto_greeting_recommend_page(
        self,
        max_count: Optional[int] = None,
        interval_min: Optional[float] = None,
        interval_max: Optional[float] = None,
        wait_card_list_seconds: Optional[int] = None,
        wait_modal_seconds: Optional[int] = None,
        use_vip_filters: Optional[bool] = None,
        filter_school: Optional[str] = None,
        filter_no_resume_exchange: Optional[str] = None,
        filter_education: Optional[List[str]] = None
    ) -> int:
        """
        在推荐页面自动打招呼
        
        Args:
            max_count: 最大打招呼数量
            interval_min: 最小间隔时间
            interval_max: 最大间隔时间
            wait_card_list_seconds: 等待卡片列表加载时间
            wait_modal_seconds: 等待弹窗加载时间
            use_vip_filters: 是否使用 VIP 筛选
            filter_school: 学校筛选
            filter_no_resume_exchange: 简历交换筛选
            filter_education: 学历筛选
        
        Returns:
            打招呼数量
        """
        timing = self._settings.timing
        filters = self._settings.filters
        jobs = self._settings.jobs
        
        max_count = max_count or jobs.max_count
        interval_min = interval_min or timing.interval_min
        interval_max = interval_max or timing.interval_max
        wait_card_list_seconds = wait_card_list_seconds or timing.wait_card_list_seconds
        wait_modal_seconds = wait_modal_seconds or timing.wait_modal_seconds
        use_vip_filters = use_vip_filters if use_vip_filters is not None else filters.use_vip_filters
        filter_school = filter_school or filters.filter_school
        filter_no_resume_exchange = filter_no_resume_exchange or filters.filter_no_resume_exchange
        filter_education = filter_education or filters.filter_education
        
        try:
            count = 0
            no_new_count = 0
            last_height = 0
            
            print("等待页面加载...")
            time.sleep(1.5)
            self._ensure_recommend_window(self.RECOMMEND_PAGE_URL)
            
            applied = self.recommend_page.apply_filters(
                use_vip_filters=use_vip_filters,
                filter_school=filter_school,
                filter_no_resume_exchange=filter_no_resume_exchange,
                filter_education=filter_education
            )
            
            has_filter_config = bool(
                filter_education or
                (use_vip_filters and (filter_school or filter_no_resume_exchange))
            )
            
            if has_filter_config and not applied:
                print("筛选未成功应用")
            
            time.sleep(2)
            
            if not self.recommend_page.switch_to_frame(
                wait_card_list_seconds=wait_card_list_seconds
            ):
                print("切换页面失败")
                return 0
            
            print("开始打招呼...")
            
            while count < max_count:
                try:
                    btn = self.recommend_page.find_first_greet_button()
                    
                    if btn is None:
                        self._browser.execute_script(
                            "window.scrollTo(0, document.body.scrollHeight);"
                        )
                        time.sleep(1)
                        new_height = self._browser.execute_script(
                            "return document.body.scrollHeight"
                        )
                        
                        if new_height == last_height:
                            no_new_count += 1
                            if no_new_count >= 3:
                                print("已到底部")
                                break
                        else:
                            no_new_count = 0
                            last_height = new_height
                        continue
                    
                    no_new_count = 0
                    
                    try:
                        self._browser.execute_script(
                            "arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});",
                            btn
                        )
                        time.sleep(0.25)
                    except StaleElementReferenceException:
                        continue
                    
                    try:
                        btn.click()
                    except Exception:
                        try:
                            self._browser.execute_script("arguments[0].click();", btn)
                        except Exception:
                            continue
                    
                    time.sleep(0.75)
                    
                    try:
                        self._browser.switch_to_default_content()
                        if self.recommend_page.check_and_close_payment_popup():
                            print("今日沟通数已达上限")
                            break
                        self._browser.driver.switch_to.frame("recommendFrame")
                    except Exception:
                        pass
                    
                    self.recommend_page.handle_greet_modal(
                        wait_modal_seconds=wait_modal_seconds
                    )
                    time.sleep(0.5)
                    self.recommend_page.close_greet_panel()
                    
                    count += 1
                    print(f"已打招呼 {count} 人")
                    
                    random_sleep(interval_min, interval_max)
                except StaleElementReferenceException:
                    continue
                except Exception:
                    time.sleep(1)
            
            try:
                self._browser.switch_to_default_content()
            except Exception:
                pass
            
            print(f"完成，共 {count} 人")
            return count
        except Exception as e:
            print(f"错误: {e}")
            return 0
    
    def auto_greeting_all_jobs(
        self,
        max_count_per_job: Optional[int] = None,
        interval_min: Optional[float] = None,
        interval_max: Optional[float] = None,
        wait_card_list_seconds: Optional[int] = None,
        wait_modal_seconds: Optional[int] = None,
        use_vip_filters: Optional[bool] = None,
        filter_school: Optional[str] = None,
        filter_no_resume_exchange: Optional[str] = None,
        filter_education: Optional[List[str]] = None,
        job_positions: Optional[List[str]] = None
    ) -> int:
        """
        遍历所有岗位自动打招呼
        
        Args:
            max_count_per_job: 每个岗位最大打招呼数量
            interval_min: 最小间隔时间
            interval_max: 最大间隔时间
            wait_card_list_seconds: 等待卡片列表加载时间
            wait_modal_seconds: 等待弹窗加载时间
            use_vip_filters: 是否使用 VIP 筛选
            filter_school: 学校筛选
            filter_no_resume_exchange: 简历交换筛选
            filter_education: 学历筛选
            job_positions: 指定岗位列表
        
        Returns:
            总打招呼数量
        """
        jobs_config = self._settings.jobs
        
        self._ensure_recommend_window(self.RECOMMEND_PAGE_URL)
        time.sleep(2)
        
        if job_positions is None:
            job_positions = jobs_config.job_positions
        
        if job_positions:
            jobs = job_positions
            print(f"使用配置的岗位列表，共 {len(jobs)} 个")
        else:
            jobs = self.recommend_page.get_all_jobs()
            if not jobs:
                print("未获取到岗位列表，仅处理当前岗位")
                return self.auto_greeting_recommend_page(
                    max_count=max_count_per_job,
                    interval_min=interval_min,
                    interval_max=interval_max,
                    wait_card_list_seconds=wait_card_list_seconds,
                    wait_modal_seconds=wait_modal_seconds,
                    use_vip_filters=use_vip_filters,
                    filter_school=filter_school,
                    filter_no_resume_exchange=filter_no_resume_exchange,
                    filter_education=filter_education
                )
            print(f"检测到 {len(jobs)} 个岗位")
        
        total_count = 0
        for i, job in enumerate(jobs):
            print(f"\n[{i+1}/{len(jobs)}] 处理岗位：{job}")
            
            if not self.recommend_page.switch_to_job(job):
                print(f"切换岗位失败: {job}")
                continue
            
            count = self.auto_greeting_recommend_page(
                max_count=max_count_per_job,
                interval_min=interval_min,
                interval_max=interval_max,
                wait_card_list_seconds=wait_card_list_seconds,
                wait_modal_seconds=wait_modal_seconds,
                use_vip_filters=use_vip_filters,
                filter_school=filter_school,
                filter_no_resume_exchange=filter_no_resume_exchange,
                filter_education=filter_education
            )
            total_count += count
        
        print(f"\n全部完成，共打招呼 {total_count} 人")
        return total_count
    
    def close(self) -> None:
        """关闭服务"""
        self._browser.close()
    
    def __enter__(self) -> "GreetingService":
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


def main() -> None:
    """主入口函数"""
    settings = get_settings()
    
    with GreetingService(settings=settings) as service:
        service.login(
            url=settings.urls.login_url,
            redirect_url=settings.urls.recommend_page_url,
            wait_login_timeout=settings.timing.wait_login_timeout,
            login_page_wait=settings.timing.login_page_wait_seconds,
            login_poll_interval=settings.timing.login_poll_interval_seconds
        )
        
        service.auto_greeting_all_jobs(
            max_count_per_job=settings.jobs.max_count,
            interval_min=settings.timing.interval_min,
            interval_max=settings.timing.interval_max,
            wait_card_list_seconds=settings.timing.wait_card_list_seconds,
            wait_modal_seconds=settings.timing.wait_modal_seconds,
            use_vip_filters=settings.filters.use_vip_filters,
            filter_school=settings.filters.filter_school,
            filter_no_resume_exchange=settings.filters.filter_no_resume_exchange,
            filter_education=settings.filters.filter_education,
            job_positions=settings.jobs.job_positions
        )


if __name__ == "__main__":
    main()
