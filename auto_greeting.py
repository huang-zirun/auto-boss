import logging
import random
import time

from selenium.common.exceptions import StaleElementReferenceException

from browser_manager import BrowserManager
from page_objects import RecommendPage

logger = logging.getLogger(__name__)


class BossAutoGreeting:
    """Boss直聘自动打招呼机器人。"""

    def __init__(self, driver_path=None, user_data_dir=None):
        self.browser = BrowserManager(driver_path, user_data_dir)
        self.recommend_page = RecommendPage(self.browser)

    def _ensure_recommend_window(self, redirect_url):
        """确保当前窗口为推荐页，必要时重定向。"""
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

    def login(self, url="https://www.zhipin.com/", redirect_url="https://www.zhipin.com/web/chat/recommend", wait_login_timeout=300, login_cookie_names=None):
        """等待登录完成后跳转到目标页面。"""
        self.browser.get(url)
        print("请在浏览器中完成登录，脚本将自动检测登录状态并跳转到推荐牛人页面...")

        if self.browser.wait_for_login(timeout=wait_login_timeout, cookie_names=login_cookie_names):
            print("检测到已登录，正在跳转到推荐牛人页面...")
        else:
            print("等待登录超时，将尝试直接打开目标页面（若未登录可能无法使用）。")

        self.browser.get(redirect_url)
        time.sleep(1.5)
        self._ensure_recommend_window(redirect_url)
        print("已打开推荐牛人页面")

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
        """自动向推荐候选人打招呼。"""
        try:
            count = 0
            no_new_count = 0
            last_height = 0

            print("等待推荐页面加载...")
            time.sleep(1.5)
            try:
                from config import recommend_page_url
            except Exception:
                recommend_page_url = "https://www.zhipin.com/web/chat/recommend"
            self._ensure_recommend_window(recommend_page_url)

            applied = self.recommend_page.apply_filters(
                use_vip_filters=use_vip_filters,
                filter_school=filter_school,
                filter_no_resume_exchange=filter_no_resume_exchange,
                filter_education=filter_education or [],
            )
            has_filter_config = bool(filter_education or (use_vip_filters and (filter_school or filter_no_resume_exchange)))
            if has_filter_config and not applied:
                print("提示：已配置筛选但未成功应用，请检查页面或手动点选筛选后再运行。")
            else:
                print("已应用筛选条件")
            time.sleep(2)

            if not self.recommend_page.switch_to_frame(wait_card_list_seconds=wait_card_list_seconds):
                print("切换推荐页 iframe 或等待列表失败，请确认已在推荐牛人页。")
                return 0

            print("已进入推荐列表，开始自动打招呼...")

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
                                print("已到底部且无更多可打招呼的候选人。")
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
                        except Exception as e:
                            print(f"点击失败: {e}")
                            continue

                    time.sleep(0.75)
                    self.recommend_page.handle_greet_modal(wait_modal_seconds=wait_modal_seconds)
                    time.sleep(0.5)
                    self.recommend_page.close_greet_panel()
                    count += 1
                    print(f"已向 {count} 个候选人打招呼")

                    delay = random.uniform(interval_min, interval_max)
                    time.sleep(delay)
                except StaleElementReferenceException:
                    continue
                except Exception as e:
                    print(f"本轮出错: {e}")
                    time.sleep(1)

            try:
                self.browser.switch_to_default_content()
            except Exception:
                pass

            print(f"自动打招呼结束，共 {count} 人。")
            return count
        except Exception as e:
            print(f"自动打招呼过程错误: {e}")
            return 0

    def close(self):
        """关闭浏览器。"""
        self.browser.close()


if __name__ == "__main__":
    import config

    bot = BossAutoGreeting(driver_path=config.driver_path, user_data_dir=config.user_data_dir)

    try:
        bot.login(
            url=config.login_url,
            redirect_url=config.recommend_page_url,
            wait_login_timeout=getattr(config, "wait_login_timeout", 300),
        )

        bot.auto_greeting_recommend_page(
            max_count=config.max_count,
            interval_min=config.interval_min,
            interval_max=config.interval_max,
            wait_card_list_seconds=config.wait_card_list_seconds,
            wait_modal_seconds=config.wait_modal_seconds,
            use_vip_filters=getattr(config, "use_vip_filters", False),
            filter_school=getattr(config, "filter_school", None),
            filter_no_resume_exchange=getattr(config, "filter_no_resume_exchange", None),
            filter_education=getattr(config, "filter_education", []),
        )
    finally:
        bot.close()
