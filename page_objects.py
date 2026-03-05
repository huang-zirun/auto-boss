import time
import logging

from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)


class RecommendPage:
    """Boss直聘推荐牛人页面操作类。"""

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

    def __init__(self, browser):
        self.browser = browser

    def _get_frame_element(self, wait_seconds=25):
        """获取推荐页 iframe 元素。"""
        self.browser.switch_to_default_content()
        try:
            iframe = WebDriverWait(self.browser.driver, wait_seconds).until(
                EC.presence_of_element_located(self.RECOMMEND_FRAME_SELECTOR)
            )
            return iframe
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
        """切换到推荐页 iframe 并等待卡片列表加载。"""
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
        """打开筛选面板。"""
        for sel in self.FILTER_LABEL_SELECTORS:
            try:
                elements = self.browser.find_elements(By.CSS_SELECTOR, sel)
                for el in elements:
                    if "筛选" not in (el.text or ""):
                        continue
                    if self.browser.safe_click(el):
                        time.sleep(0.2)
                        return True
            except Exception:
                continue
        return self.browser.click_by_text("筛选") or self.browser.click_by_text("筛选条件")

    def click_filter_option(self, text):
        """点击筛选选项。"""
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
                time.sleep(0.2)
                return True
        except Exception:
            pass
        return self.browser.click_by_text(text)

    def click_filter_confirm(self):
        """点击筛选确认按钮。"""
        try:
            buttons = self.browser.find_elements(*self.CONFIRM_BUTTON_SELECTOR)
            for el in buttons:
                if (el.text or "").strip() != "确定":
                    continue
                if self.browser.safe_click(el):
                    time.sleep(0.2)
                    return True
        except Exception:
            pass
        return self.browser.click_by_text("确定")

    def apply_filters(self, use_vip_filters, filter_school, filter_no_resume_exchange, filter_education):
        """应用筛选条件。"""
        applied = False
        iframe = self._get_frame_element(wait_seconds=25)
        if iframe is None:
            return False

        try:
            self.browser.switch_to_frame(iframe)
        except Exception:
            return False

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
                time.sleep(0.75)
        except Exception:
            pass
        finally:
            try:
                self.browser.switch_to_default_content()
            except Exception:
                pass

        return applied

    def find_first_greet_button(self):
        """查找首个可用的打招呼按钮。"""
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
                except NoSuchElementException:
                    continue
                except StaleElementReferenceException:
                    continue
        except Exception:
            pass
        return None

    def _find_send_button(self):
        """查找发送按钮。"""
        for by, selector in self.SEND_BUTTON_SELECTORS:
            try:
                btn = self.browser.find_element(by, selector)
                if btn.is_displayed():
                    return btn
            except NoSuchElementException:
                continue
        return None

    def handle_greet_modal(self, wait_modal_seconds=5):
        """处理打招呼弹窗。"""
        try:
            time.sleep(0.5)

            for xpath in self.TEMPLATE_SELECTORS:
                try:
                    el = self.browser.find_element(By.XPATH, xpath)
                    if el.is_displayed():
                        el.click()
                        time.sleep(0.5)
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

    def close_greet_panel(self):
        """关闭招呼弹窗。"""
        try:
            self.browser.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(0.15)
        except Exception:
            pass

        for xpath in self.CLOSE_BUTTON_XPATHS:
            try:
                el = self.browser.find_element(By.XPATH, xpath)
                if el.is_displayed():
                    el.click()
                    time.sleep(0.15)
                    break
            except NoSuchElementException:
                continue
