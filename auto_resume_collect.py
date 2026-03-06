import logging
import random
import time

from selenium_utils import NoSuchElementException, StaleElementReferenceException, TimeoutException, By, Keys, EC, WebDriverWait
from base_bot import BaseBot

logger = logging.getLogger(__name__)

GEEK_ITEM_SELECTOR = (By.CSS_SELECTOR, "div.geek-item")
AGREE_SELECTORS = [(By.CSS_SELECTOR, "span.card-btn"), (By.CSS_SELECTOR, "a.btn")]
PREVIEW_RESUME_TEXT = "点击预览附件简历"
ATTACHMENT_BTNS_CLASS = "attachment-resume-btns"
LOADING_TEXT = "正在加载简历"
RISK_CONTROL_TEXTS = ("正在加载验证", "异常访问行为", "完成验证后即可正常使用")
MSG_ASK_RESUME = "你好，方便的话可以发简历过来看看"
CHAT_INPUT_SELECTORS = [
    (By.CSS_SELECTOR, "#boss-chat-editor-input"),
    (By.CSS_SELECTOR, "div.boss-chat-editor-input[contenteditable='true']"),
]
REQUEST_RESUME_BTN = (By.XPATH, "//span[contains(@class,'operate-btn') and text()='求简历']")
CONFIRM_RESUME_BTN = (By.XPATH, "//span[contains(@class,'boss-btn-primary') and contains(@class,'boss-btn') and text()='确定']")


def _random_sleep(min_sec: float, max_sec: float) -> None:
    if max_sec > min_sec:
        time.sleep(random.uniform(min_sec, max_sec))
    else:
        time.sleep(min_sec)


class BossAutoResumeCollect(BaseBot):
    CHAT_PAGE_URL = "https://www.zhipin.com/web/chat/index"

    def _get_default_redirect_url(self):
        return self.CHAT_PAGE_URL

    def is_risk_control_page(self) -> bool:
        try:
            self.browser.switch_to_default_content()
            body = self.browser.driver.find_element(By.TAG_NAME, "body")
            text = (body.text or "").strip()
            return any(k in text for k in RISK_CONTROL_TEXTS)
        except Exception:
            return False

    def _get_chat_list_items(self):
        try:
            self.browser.switch_to_default_content()
            items = self.browser.find_elements(*GEEK_ITEM_SELECTOR)
            return [el for el in items if el.is_displayed()]
        except Exception as e:
            logger.warning("获取会话列表失败: %s", e)
            return []

    def _get_chat_list_scroll_container(self):
        try:
            items = self.browser.find_elements(*GEEK_ITEM_SELECTOR)
            if not items:
                return None
            container = self.browser.driver.execute_script(
                """
                var el = arguments[0];
                while (el && el !== document.body) {
                    var s = window.getComputedStyle(el);
                    var o = (s.overflow + s.overflowY).toLowerCase();
                    if (/auto|scroll|overlay/.test(o)) return el;
                    el = el.parentElement;
                }
                return null;
                """,
                items[0],
            )
            return container
        except Exception as e:
            logger.warning("获取会话列表滚动容器失败: %s", e)
            return None

    def _scroll_chat_list_down(self, step=200):
        container = self._get_chat_list_scroll_container()
        if not container:
            return False
        try:
            self.browser.driver.execute_script("arguments[0].scrollTop += arguments[1];", container, step)
            return True
        except Exception as e:
            logger.warning("滚动会话列表失败: %s", e)
            return False

    def has_resume_agree_request(self):
        for by, selector in AGREE_SELECTORS:
            try:
                els = self.browser.find_elements(by, selector)
                for el in els:
                    if (el.text or "").strip() != "同意":
                        continue
                    if el.is_displayed():
                        return True
            except Exception:
                continue
        return False

    def _click_agree(self, timeout=10):
        for by, selector in AGREE_SELECTORS:
            try:
                els = self.browser.find_elements(by, selector)
                for el in els:
                    if (el.text or "").strip() != "同意":
                        continue
                    if not el.is_displayed():
                        continue
                    self.browser.safe_click(el)
                    return True
            except Exception:
                continue
        return False

    def _click_preview_resume(self, timeout=15):
        try:
            el = WebDriverWait(self.browser.driver, timeout).until(
                EC.element_to_be_clickable((By.XPATH, f"//span[contains(@class,'card-btn') and contains(text(),'{PREVIEW_RESUME_TEXT}')]")
            ))
            self.browser.safe_click(el)
            return True
        except TimeoutException:
            try:
                el = self.browser.driver.find_element(By.XPATH, f"//*[contains(@class,'card-btn') and contains(text(),'{PREVIEW_RESUME_TEXT}')]")
                if el.is_displayed():
                    self.browser.safe_click(el)
                    return True
            except NoSuchElementException:
                pass
        return False

    def _wait_resume_loaded(self, timeout=30):
        try:
            WebDriverWait(self.browser.driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, f".{ATTACHMENT_BTNS_CLASS}")))
            deadline = time.time() + min(15, timeout)
            while time.time() < deadline:
                try:
                    body_text = self.browser.driver.find_element(By.TAG_NAME, "body").text or ""
                    if LOADING_TEXT in body_text:
                        time.sleep(0.5)
                        continue
                except Exception:
                    pass
                break
            time.sleep(0.5)
            return True
        except TimeoutException:
            return False

    def _click_download(self, timeout=10):
        try:
            container = self.browser.driver.find_element(By.CSS_SELECTOR, f".{ATTACHMENT_BTNS_CLASS}")
            try:
                download_use = container.find_element(
                    By.XPATH, ".//*[name()='use' and (contains(@*[name()='xlink:href'], 'attacthment-download') or contains(@href, 'attacthment-download'))]"
                )
                wrapper = self.browser.driver.execute_script(
                    "var u = arguments[0]; return u.parentElement && u.parentElement.parentElement ? u.parentElement.parentElement : u.parentElement;", download_use
                )
                if wrapper:
                    self.browser.driver.execute_script("arguments[0].click();", wrapper)
                    return True
            except NoSuchElementException:
                pass
            try:
                download_svg = container.find_element(
                    By.CSS_SELECTOR,
                    "svg.boss-svg.svg-icon use[xlink\\:href='#icon-attacthment-download'], svg.boss-svg.svg-icon use[href='#icon-attacthment-download']"
                )
                wrapper = self.browser.driver.execute_script(
                    "var u = arguments[0]; return u.parentElement && u.parentElement.parentElement ? u.parentElement.parentElement : u.parentElement;", download_svg
                )
                if wrapper:
                    self.browser.driver.execute_script("arguments[0].click();", wrapper)
                    return True
            except NoSuchElementException:
                pass
            popovers = container.find_elements(By.CSS_SELECTOR, "div.popover.icon-content")
            if len(popovers) >= 3:
                self.browser.driver.execute_script("arguments[0].click();", popovers[2])
                return True
            download_div = container.find_element(By.XPATH, ".//div[contains(@class,'popover-content') and normalize-space(text())='下载']")
            parent = download_div.find_element(By.XPATH, "./ancestor::div[contains(@class,'popover')][1]")
            self.browser.driver.execute_script("arguments[0].click();", parent)
            return True
        except NoSuchElementException:
            try:
                container = self.browser.driver.find_element(By.CSS_SELECTOR, f".{ATTACHMENT_BTNS_CLASS}")
                el = container.find_element(By.XPATH, ".//*[contains(text(),'下载')]")
                self.browser.driver.execute_script("arguments[0].click();", el)
                return True
            except (NoSuchElementException, Exception):
                pass
        except Exception as e:
            logger.warning("点击下载按钮异常: %s", e)
        return False

    def _click_close_preview(self, timeout=5):
        try:
            el = WebDriverWait(self.browser.driver, timeout).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "i.icon-close")))
            self.browser.driver.execute_script("arguments[0].click();", el)
            return True
        except (TimeoutException, NoSuchElementException):
            try:
                el = self.browser.driver.find_element(By.CSS_SELECTOR, "i.icon-close")
                if el.is_displayed():
                    self.browser.driver.execute_script("arguments[0].click();", el)
                    return True
            except NoSuchElementException:
                pass
        except Exception as e:
            logger.warning("点击关闭按钮异常: %s", e)
        return False

    def _has_already_requested_resume(self):
        try:
            self.browser.switch_to_default_content()
            el = self.browser.driver.find_element(*REQUEST_RESUME_BTN)
            return not (el.is_displayed() and el.is_enabled())
        except NoSuchElementException:
            return True
        except Exception:
            return True

    def _send_chat_message(self, text, timeout=5):
        try:
            self.browser.switch_to_default_content()
            inp = None
            for by, selector in CHAT_INPUT_SELECTORS:
                try:
                    inp = WebDriverWait(self.browser.driver, timeout).until(EC.presence_of_element_located((by, selector)))
                    if inp.is_displayed():
                        break
                except TimeoutException:
                    continue
            if not inp or not inp.is_displayed():
                return False
            inp.click()
            time.sleep(0.2)
            inp.send_keys(text)
            time.sleep(0.2)
            inp.send_keys(Keys.ENTER)
            return True
        except Exception as e:
            logger.warning("发送聊天消息异常: %s", e)
        return False

    def _click_request_resume_then_confirm(self, timeout=5):
        try:
            self.browser.switch_to_default_content()
            btn = WebDriverWait(self.browser.driver, timeout).until(EC.element_to_be_clickable(REQUEST_RESUME_BTN))
            self.browser.safe_click(btn)
            time.sleep(0.5)
            confirm = WebDriverWait(self.browser.driver, timeout).until(EC.element_to_be_clickable(CONFIRM_RESUME_BTN))
            self.browser.safe_click(confirm)
            return True
        except (TimeoutException, NoSuchElementException):
            return False
        except Exception as e:
            logger.warning("点击求简历/确定异常: %s", e)
        return False

    def run_once(self, wait_after_agree=3, wait_after_preview=2, wait_after_agree_min=None, wait_after_agree_max=None,
                 wait_after_preview_min=None, wait_after_preview_max=None, resume_load_timeout=30):
        if not self._click_agree():
            return (False, False, False, False)
        if wait_after_agree_min is not None and wait_after_agree_max is not None:
            _random_sleep(wait_after_agree_min, wait_after_agree_max)
        else:
            time.sleep(wait_after_agree)

        if not self._click_preview_resume():
            return (True, False, False, False)
        if wait_after_preview_min is not None and wait_after_preview_max is not None:
            _random_sleep(wait_after_preview_min, wait_after_preview_max)
        else:
            time.sleep(wait_after_preview)

        if not self._wait_resume_loaded(timeout=resume_load_timeout):
            return (True, True, False, False)

        download_ok = self._click_download()
        if download_ok:
            time.sleep(0.5)
            self._click_close_preview()
            time.sleep(0.3)
        return (True, True, True, download_ok)

    def run_all_chats(self, max_count=0, wait_after_click_chat=1.5, interval_between_chats=1.5, wait_after_agree=3,
                      resume_load_timeout=30, scroll_step=200, chat_interval_min=None, chat_interval_max=None,
                      download_interval_min=None, download_interval_max=None, wait_after_agree_min=None,
                      wait_after_agree_max=None, wait_after_preview_min=None, wait_after_preview_max=None):
        time.sleep(1)
        collected = 0
        prev_count = 0
        no_new_rounds = 0
        use_random_chat = chat_interval_min is not None and chat_interval_max is not None and chat_interval_max > chat_interval_min
        use_random_download = download_interval_min is not None and download_interval_max is not None and download_interval_max > download_interval_min

        while True:
            if self.is_risk_control_page():
                print("\n检测到风控验证页，请手动完成验证后按回车继续...")
                input()
            self._scroll_chat_list_down(step=scroll_step)
            time.sleep(0.4)
            items = self._get_chat_list_items()
            if not items:
                if prev_count == 0:
                    print("未找到会话列表")
                break
            if len(items) <= prev_count and prev_count > 0:
                no_new_rounds += 1
                if no_new_rounds >= 2:
                    break
            else:
                no_new_rounds = 0
            prev_count = len(items)

            if collected == 0 and prev_count > 0:
                print(f"当前可见 {len(items)} 个会话")

            for i, item in enumerate(items):
                if max_count and collected >= max_count:
                    break
                try:
                    try:
                        self.browser.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'auto'});", item)
                        time.sleep(0.3)
                    except StaleElementReferenceException:
                        items = self._get_chat_list_items()
                        if i >= len(items):
                            break
                        item = items[i]
                    try:
                        item.click()
                    except Exception:
                        try:
                            self.browser.execute_script("arguments[0].click();", item)
                        except Exception:
                            continue

                    if use_random_chat:
                        _random_sleep(chat_interval_min, chat_interval_max)
                    else:
                        time.sleep(wait_after_click_chat)

                    if self.is_risk_control_page():
                        print("\n检测到风控验证页，请手动完成验证后按回车继续...")
                        input()
                        continue

                    if not self.has_resume_agree_request():
                        if self._has_already_requested_resume():
                            continue
                        if self._send_chat_message(MSG_ASK_RESUME):
                            time.sleep(0.5)
                            self._click_request_resume_then_confirm()
                        if use_random_chat:
                            _random_sleep(chat_interval_min, chat_interval_max)
                        else:
                            time.sleep(interval_between_chats)
                        continue

                    name_job = ""
                    try:
                        title_el = item.find_element(By.CSS_SELECTOR, ".geek-name")
                        name_job = (title_el.text or "").strip()
                        job_el = item.find_element(By.CSS_SELECTOR, ".source-job")
                        name_job = f"{name_job} ({job_el.text or ''})".strip()
                    except Exception:
                        name_job = f"会话 {i+1}"
                    print(f"\n[{collected + 1}] 检测到简历申请: {name_job}")

                    agree_ok, preview_ok, loaded_ok, download_ok = self.run_once(
                        wait_after_agree=wait_after_agree,
                        resume_load_timeout=resume_load_timeout,
                        wait_after_agree_min=wait_after_agree_min,
                        wait_after_agree_max=wait_after_agree_max,
                        wait_after_preview_min=wait_after_preview_min,
                        wait_after_preview_max=wait_after_preview_max,
                    )
                    if download_ok:
                        collected += 1
                        print(f"已收集简历，累计 {collected} 份")
                        if use_random_download:
                            delay = random.uniform(download_interval_min, download_interval_max)
                            time.sleep(delay)
                        if self.is_risk_control_page():
                            print("\n检测到风控验证页，请手动完成验证后按回车继续...")
                            input()

                    try:
                        self.browser.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                        time.sleep(0.3)
                    except Exception:
                        pass
                    if use_random_chat:
                        _random_sleep(chat_interval_min, chat_interval_max)
                    else:
                        time.sleep(interval_between_chats)
                except StaleElementReferenceException:
                    items = self._get_chat_list_items()
                    if i >= len(items):
                        break
                    continue
                except Exception:
                    time.sleep(0.5)

            if max_count and collected >= max_count:
                break

        print(f"\n完成，共收集 {collected} 份简历")
        return collected


if __name__ == "__main__":
    import config

    with BossAutoResumeCollect(
        driver_path=config.config.browser.driver_path,
        user_data_dir=config.config.browser.user_data_dir,
        debug_port=config.config.browser.debug_port,
    ) as bot:
        bot.login(
            url=config.config.urls.login_url,
            redirect_url=config.config.urls.chat_page_url,
            wait_login_timeout=config.config.timing.wait_login_timeout,
            login_page_wait=config.config.timing.login_page_wait_seconds,
            login_poll_interval=config.config.timing.login_poll_interval_seconds,
        )
        bot.run_all_chats(
            max_count=config.config.resume.resume_max_collect,
            wait_after_click_chat=config.config.resume.resume_chat_interval,
            interval_between_chats=config.config.resume.resume_chat_interval,
            wait_after_agree=3,
            resume_load_timeout=config.config.resume.resume_load_timeout,
            chat_interval_min=config.config.resume.resume_chat_interval_min,
            chat_interval_max=config.config.resume.resume_chat_interval_max,
            download_interval_min=config.config.resume.resume_download_interval_min,
            download_interval_max=config.config.resume.resume_download_interval_max,
            wait_after_agree_min=config.config.resume.resume_wait_after_agree_min,
            wait_after_agree_max=config.config.resume.resume_wait_after_agree_max,
            wait_after_preview_min=config.config.resume.resume_wait_after_preview_min,
            wait_after_preview_max=config.config.resume.resume_wait_after_preview_max,
        )
