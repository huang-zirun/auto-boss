import time
import logging

from selenium_utils import NoSuchElementException, StaleElementReferenceException, By, Keys, EC, WebDriverWait

logger = logging.getLogger(__name__)


class RecommendPage:
    DELAY_SHORT = 0.15
    DELAY_MEDIUM = 0.2
    DELAY_HALF = 0.5
    DELAY_LONG = 0.75
    DELAY_REFRESH = 3

    RECOMMEND_FRAME_SELECTOR = (By.CSS_SELECTOR, "iframe[name='recommendFrame']")
    CARD_LIST_SELECTOR = (By.CSS_SELECTOR, ".card-list .card-item")
    FILTER_LABEL_SELECTORS = ("div.filter-label", ".filter-label")
    OPTION_SELECTOR = (By.CSS_SELECTOR, "div.option")
    CONFIRM_BUTTON_SELECTOR = (By.CSS_SELECTOR, "div.btn")

    INPUT_SELECTORS = [
        "textarea[placeholder*='消息']",
        "textarea[placeholder*='输入']",
        "textarea[placeholder*='请输入']",
        "div[contenteditable='true']",
        "textarea",
    ]

    TEMPLATE_SELECTORS = [
        "//div[contains(@class,'greet')]//div[contains(@class,'item') or contains(@class,'template')]",
        "//li[contains(@class,'template') or contains(@class,'greet')]",
        "//*[contains(text(), '使用') and contains(text(), '招呼')]",
        "//*[contains(text(), '选择') and contains(text(), '语')]",
    ]

    SEND_BUTTON_SELECTORS = [
        (By.XPATH, "//button[contains(text(), '发送')]"),
        (By.XPATH, "//*[@role='button' and contains(text(), '发送')]"),
        (By.CSS_SELECTOR, "button[class*='send']"),
        (By.CSS_SELECTOR, ".btn-send"),
    ]

    CLOSE_BUTTON_XPATHS = [
        "//div[contains(@class,'close')]",
        "//i[contains(@class,'close')]",
        "//button[contains(@class,'close')]",
        "//*[@aria-label='关闭']",
    ]

    JOB_DROPDOWN_TRIGGER = (By.CSS_SELECTOR, "div.ui-dropmenu-label")
    JOB_OPTION_XPATHS = [
        "//li[contains(@class,'job-item')]//span[contains(@class,'label')]",
        "//span[contains(@class,'label') and descendant::u[contains(@class,'h')]]",
    ]

    PAYMENT_POPUP_SELECTOR = (By.CSS_SELECTOR, ".payment-layout-v2")
    PAYMENT_CLOSE_SELECTOR = (By.CSS_SELECTOR, "i.icon-close")

    def __init__(self, browser):
        self.browser = browser

    def _get_frame_element(self, wait_seconds=25):
        self.browser.switch_to_default_content()
        try:
            return WebDriverWait(self.browser.driver, wait_seconds).until(
                EC.presence_of_element_located(self.RECOMMEND_FRAME_SELECTOR)
            )
        except Exception:
            pass

        for el in self.browser.find_elements(By.TAG_NAME, "iframe"):
            try:
                src = (el.get_attribute("src") or "").lower()
                if "recommend" in src or ("zhipin" in src and "chat" in src):
                    return el
            except Exception:
                continue
        return None

    def switch_to_frame(self, wait_card_list_seconds=15):
        try:
            iframe = self._get_frame_element(wait_seconds=25)
            if iframe is None:
                return False
            self.browser.switch_to_frame(iframe)
            WebDriverWait(self.browser.driver, wait_card_list_seconds).until(
                EC.presence_of_element_located(self.CARD_LIST_SELECTOR)
            )
            return True
        except Exception:
            return False

    def open_filter_panel(self):
        for sel in self.FILTER_LABEL_SELECTORS:
            try:
                elements = self.browser.find_elements(By.CSS_SELECTOR, sel)
                for el in elements:
                    if "筛选" not in (el.text or ""):
                        continue
                    if self.browser.safe_click(el):
                        time.sleep(self.DELAY_MEDIUM)
                        return True
            except Exception:
                continue
        return self.browser.click_by_text("筛选") or self.browser.click_by_text("筛选条件")

    def click_filter_option(self, text):
        try:
            options = self.browser.find_elements(*self.OPTION_SELECTOR)
            for el in options:
                if (el.text or "").strip() != text:
                    continue
                self.browser.execute_script("""
                    var mask = document.querySelector('.vip-mask');
                    if (mask) { mask.style.pointerEvents = 'none'; }
                    arguments[0].scrollIntoView({block: 'center'});
                    arguments[0].click();
                    if (mask) { mask.style.pointerEvents = ''; }
                """, el)
                time.sleep(self.DELAY_MEDIUM)
                return True
        except Exception:
            pass
        return self.browser.click_by_text(text)

    def click_filter_confirm(self):
        try:
            buttons = self.browser.find_elements(*self.CONFIRM_BUTTON_SELECTOR)
            for el in buttons:
                if (el.text or "").strip() != "确定":
                    continue
                if self.browser.safe_click(el):
                    time.sleep(self.DELAY_MEDIUM)
                    return True
        except Exception:
            pass
        return self.browser.click_by_text("确定")

    def apply_filters(self, use_vip_filters, filter_school, filter_no_resume_exchange, filter_education):
        if not self.switch_to_frame():
            return False

        applied = False
        try:
            time.sleep(1)
            self.open_filter_panel()

            if use_vip_filters and filter_school:
                if self.click_filter_option(filter_school):
                    applied = True
            if use_vip_filters and filter_no_resume_exchange:
                if self.click_filter_option(filter_no_resume_exchange):
                    applied = True
            for edu in (filter_education or []):
                if edu and self.click_filter_option(edu):
                    applied = True

            if self.click_filter_confirm():
                applied = True
                time.sleep(self.DELAY_LONG)
        except Exception:
            pass
        finally:
            try:
                self.browser.switch_to_default_content()
            except Exception:
                pass

        return applied

    def find_first_greet_button(self):
        try:
            cards = self.browser.find_elements(By.CSS_SELECTOR, ".card-list .card-item")
            for card in cards:
                try:
                    btn = card.find_element(By.XPATH, ".//button[contains(text(), '打招呼')]")
                    text = (btn.text or "").strip()
                    if "已沟通" in text or "已打招呼" in text or "继续沟通" in text:
                        continue
                    if btn.is_displayed():
                        return btn
                except (NoSuchElementException, StaleElementReferenceException):
                    continue
        except Exception:
            pass
        return None

    def _find_send_button(self):
        for by, selector in self.SEND_BUTTON_SELECTORS:
            try:
                btn = self.browser.find_element(by, selector)
                if btn.is_displayed():
                    return btn
            except NoSuchElementException:
                continue
        return None

    def handle_greet_modal(self, wait_modal_seconds=5):
        try:
            time.sleep(self.DELAY_HALF)

            for xpath in self.TEMPLATE_SELECTORS:
                try:
                    el = self.browser.find_element(By.XPATH, xpath)
                    if el.is_displayed():
                        el.click()
                        time.sleep(self.DELAY_HALF)
                        send_btn = self._find_send_button()
                        if send_btn:
                            send_btn.click()
                            return True
                except NoSuchElementException:
                    continue

            send_btn = self._find_send_button()
            if send_btn:
                send_btn.click()
                return True
        except Exception:
            pass
        return False

    def check_and_close_payment_popup(self):
        try:
            popup = self.browser.find_element(*self.PAYMENT_POPUP_SELECTOR)
            if popup.is_displayed():
                try:
                    self.browser.find_element(*self.PAYMENT_CLOSE_SELECTOR).click()
                    time.sleep(self.DELAY_HALF)
                except Exception:
                    pass
                return True
        except Exception:
            pass
        return False

    def _close_overlay(self):
        for sel in (".boss-layer__wrapper", ".dialog-container", ".layer-wrapper"):
            try:
                for el in self.browser.find_elements(By.CSS_SELECTOR, sel):
                    if el.is_displayed():
                        self.browser.execute_script("arguments[0].style.display='none';", el)
            except Exception:
                pass

    def _open_job_dropdown(self):
        self.browser.switch_to_default_content()
        self._close_overlay()
        iframe = self._get_frame_element(wait_seconds=10)
        if iframe is not None:
            self.browser.switch_to_frame(iframe)
        trigger = self.browser.find_element(*self.JOB_DROPDOWN_TRIGGER)
        trigger.click()
        try:
            WebDriverWait(self.browser.driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.ui-dropmenu-visible"))
            )
        except Exception:
            time.sleep(0.8)
        return trigger

    def _find_job_options(self):
        for xpath in self.JOB_OPTION_XPATHS:
            try:
                els = self.browser.find_elements(By.XPATH, xpath)
                if any((e.text or "").strip() for e in els):
                    return els
            except Exception:
                continue
        return []

    def _close_dropdown(self, trigger=None):
        try:
            self.browser.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except Exception:
            if trigger:
                try:
                    trigger.click()
                except Exception:
                    pass
        time.sleep(self.DELAY_MEDIUM)

    def _get_job_options_with_dropdown(self):
        trigger = self._open_job_dropdown()
        options = self._find_job_options()
        return trigger, options

    def get_all_jobs(self):
        try:
            trigger, options = self._get_job_options_with_dropdown()
            jobs = []
            for el in options:
                try:
                    text = (el.text or "").strip()
                    if text:
                        jobs.append(text)
                except Exception:
                    continue
            self._close_dropdown(trigger)
            return jobs
        except Exception as e:
            logger.warning(f"获取岗位列表失败: {e}")
            return []

    def switch_to_job(self, job_text):
        try:
            trigger, options = self._get_job_options_with_dropdown()
            for el in options:
                try:
                    text = (el.text or "").strip()
                    if not text:
                        continue
                    if job_text in text or text in job_text:
                        self.browser.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});", el
                        )
                        time.sleep(self.DELAY_MEDIUM)
                        try:
                            el.click()
                        except Exception:
                            self.browser.execute_script("arguments[0].click();", el)
                        time.sleep(self.DELAY_REFRESH)
                        return True
                except Exception:
                    continue
            self._close_dropdown()
            logger.warning(f"未找到岗位: {job_text}")
            return False
        except Exception as e:
            logger.warning(f"切换岗位失败: {e}")
            return False

    def close_greet_panel(self):
        try:
            self.browser.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(self.DELAY_SHORT)
        except Exception:
            pass

        for xpath in self.CLOSE_BUTTON_XPATHS:
            try:
                el = self.browser.find_element(By.XPATH, xpath)
                if el.is_displayed():
                    el.click()
                    time.sleep(self.DELAY_SHORT)
                    break
            except NoSuchElementException:
                continue
