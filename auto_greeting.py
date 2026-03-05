import logging
import random
import time

from selenium_utils import StaleElementReferenceException
from base_bot import BaseBot
from page_objects import RecommendPage

logger = logging.getLogger(__name__)


class BossAutoGreeting(BaseBot):
    RECOMMEND_PAGE_URL = "https://www.zhipin.com/web/chat/recommend"

    def __init__(self, driver_path=None, user_data_dir=None, debug_port=9222):
        super().__init__(driver_path, user_data_dir, debug_port)
        self.recommend_page = RecommendPage(self.browser)

    def _get_default_redirect_url(self):
        return self.RECOMMEND_PAGE_URL

    def _after_login_redirect(self):
        self._ensure_recommend_window(self.RECOMMEND_PAGE_URL)

    def _ensure_recommend_window(self, redirect_url):
        try:
            current = (self.browser.current_url or "").strip().lower()
            if current.startswith("data:") or "zhipin.com" not in current:
                for handle in self.browser.window_handles:
                    self.browser.switch_to_window(handle)
                    u = (self.browser.current_url or "").strip().lower()
                    if "zhipin.com" in u and ("recommend" in u or "chat" in u):
                        return
                self.browser.get(redirect_url)
                time.sleep(4)
        except Exception:
            pass

    def auto_greeting_recommend_page(
        self,
        max_count=100,
        interval_min=2.0,
        interval_max=5.0,
        wait_card_list_seconds=15,
        wait_modal_seconds=5,
        use_vip_filters=False,
        filter_school=None,
        filter_no_resume_exchange=None,
        filter_education=None,
    ):
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
                filter_education=filter_education or [],
            )
            has_filter_config = bool(filter_education or (use_vip_filters and (filter_school or filter_no_resume_exchange)))
            if has_filter_config and not applied:
                print("筛选未成功应用")
            time.sleep(2)

            if not self.recommend_page.switch_to_frame(wait_card_list_seconds=wait_card_list_seconds):
                print("切换页面失败")
                return 0

            print("开始打招呼...")

            while count < max_count:
                try:
                    btn = self.recommend_page.find_first_greet_button()
                    if btn is None:
                        self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(1)
                        new_height = self.browser.execute_script("return document.body.scrollHeight")
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
                        self.browser.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", btn)
                        time.sleep(0.25)
                    except StaleElementReferenceException:
                        continue
                    try:
                        btn.click()
                    except Exception:
                        try:
                            self.browser.execute_script("arguments[0].click();", btn)
                        except Exception:
                            continue

                    time.sleep(0.75)

                    try:
                        self.browser.switch_to_default_content()
                        if self.recommend_page.check_and_close_payment_popup():
                            print("今日沟通数已达上限")
                            break
                        self.browser.driver.switch_to.frame("recommendFrame")
                    except Exception:
                        pass

                    self.recommend_page.handle_greet_modal(wait_modal_seconds=wait_modal_seconds)
                    time.sleep(0.5)
                    self.recommend_page.close_greet_panel()
                    count += 1
                    print(f"已打招呼 {count} 人")

                    delay = random.uniform(interval_min, interval_max)
                    time.sleep(delay)
                except StaleElementReferenceException:
                    continue
                except Exception:
                    time.sleep(1)

            try:
                self.browser.switch_to_default_content()
            except Exception:
                pass

            print(f"完成，共 {count} 人")
            return count
        except Exception as e:
            print(f"错误: {e}")
            return 0

    def auto_greeting_all_jobs(
        self,
        max_count_per_job=100,
        interval_min=2.0,
        interval_max=5.0,
        wait_card_list_seconds=15,
        wait_modal_seconds=5,
        use_vip_filters=False,
        filter_school=None,
        filter_no_resume_exchange=None,
        filter_education=None,
        job_positions=None,
    ):
        self._ensure_recommend_window(self.RECOMMEND_PAGE_URL)
        time.sleep(2)

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
                    filter_education=filter_education,
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
                filter_education=filter_education,
            )
            total_count += count

        print(f"\n全部完成，共打招呼 {total_count} 人")
        return total_count


if __name__ == "__main__":
    import config

    with BossAutoGreeting(
        driver_path=config.config.browser.driver_path,
        user_data_dir=config.config.browser.user_data_dir,
        debug_port=config.config.browser.debug_port,
    ) as bot:
        bot.login(
            url=config.config.urls.login_url,
            redirect_url=config.config.urls.recommend_page_url,
            wait_login_timeout=config.config.timing.wait_login_timeout,
        )

        bot.auto_greeting_all_jobs(
            max_count_per_job=config.config.jobs.max_count,
            interval_min=config.config.timing.interval_min,
            interval_max=config.config.timing.interval_max,
            wait_card_list_seconds=config.config.timing.wait_card_list_seconds,
            wait_modal_seconds=config.config.timing.wait_modal_seconds,
            use_vip_filters=config.config.filters.use_vip_filters,
            filter_school=config.config.filters.filter_school,
            filter_no_resume_exchange=config.config.filters.filter_no_resume_exchange,
            filter_education=config.config.filters.filter_education,
            job_positions=config.config.jobs.job_positions,
        )
