"""
聊天页面对象

封装聊天页面的操作。
"""
import logging
import time
from typing import Any, List, Optional

from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ..config.selectors import SelectorItem, SelectorProvider
from ..core.browser import BrowserManager
from ..core.exceptions import ElementNotFoundError, RiskControlDetectedError
from ..utils.helpers import random_sleep
from .base import BasePage

logger = logging.getLogger(__name__)


class ChatPage(BasePage):
    """
    聊天页面对象
    
    封装聊天页面的所有操作。
    """
    
    PAGE_NAME = "chat_page"
    
    MSG_ASK_RESUME = "你好，方便的话可以发简历过来看看"
    
    def is_loaded(self) -> bool:
        """检查页面是否已加载"""
        try:
            selector_item = self.get_selector("chat_list.item")
            items = self.find_elements(selector_item)
            return len(items) > 0
        except Exception:
            return False
    
    def is_risk_control_page(self) -> bool:
        """
        检测是否为风控页面
        
        Returns:
            True 表示检测到风控
        """
        try:
            self.switch_to_default_content()
            body = self.driver.find_element(By.TAG_NAME, "body")
            text = (body.text or "").strip()
            
            risk_texts = self._selectors.get_texts("common", "risk_control_texts")
            return any(k in text for k in risk_texts)
        except Exception:
            return False
    
    def get_chat_list_items(self) -> List[Any]:
        """
        获取会话列表项
        
        Returns:
            会话列表元素列表
        """
        try:
            self.switch_to_default_content()
            selector_item = self.get_selector("chat_list.item")
            items = self.find_elements(selector_item)
            return [el for el in items if el.is_displayed()]
        except Exception as e:
            logger.warning(f"获取会话列表失败: {e}")
            return []
    
    def get_chat_list_scroll_container(self) -> Optional[Any]:
        """
        获取会话列表滚动容器
        
        Returns:
            滚动容器元素或 None
        """
        try:
            items = self.get_chat_list_items()
            if not items:
                return None
            
            container = self.driver.execute_script(
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
                items[0]
            )
            return container
        except Exception as e:
            logger.warning(f"获取会话列表滚动容器失败: {e}")
            return None
    
    def scroll_chat_list_down(self, step: int = 200) -> bool:
        """
        向下滚动会话列表
        
        Args:
            step: 滚动步长
        
        Returns:
            True 表示成功
        """
        container = self.get_chat_list_scroll_container()
        if not container:
            return False
        
        try:
            self.driver.execute_script(
                "arguments[0].scrollTop += arguments[1];",
                container,
                step
            )
            return True
        except Exception as e:
            logger.warning(f"滚动会话列表失败: {e}")
            return False
    
    def has_resume_agree_request(self) -> bool:
        """
        检测是否有简历交换申请
        
        Returns:
            True 表示有申请
        """
        agree_selectors = self.get_selector("agree_button")
        if isinstance(agree_selectors, SelectorItem):
            agree_selectors = [agree_selectors]
        
        for selector_item in agree_selectors:
            try:
                els = self.driver.find_elements(
                    selector_item.by,
                    selector_item.selector
                )
                for el in els:
                    if (el.text or "").strip() != "同意":
                        continue
                    if el.is_displayed():
                        return True
            except Exception:
                continue
        
        return False
    
    def click_agree(self, timeout: float = 10) -> bool:
        """
        点击同意按钮
        
        Args:
            timeout: 超时时间
        
        Returns:
            True 表示成功
        """
        agree_selectors = self.get_selector("agree_button")
        if isinstance(agree_selectors, SelectorItem):
            agree_selectors = [agree_selectors]
        
        for selector_item in agree_selectors:
            try:
                els = self.driver.find_elements(
                    selector_item.by,
                    selector_item.selector
                )
                for el in els:
                    if (el.text or "").strip() != "同意":
                        continue
                    if not el.is_displayed():
                        continue
                    
                    self._browser.safe_click(el)
                    return True
            except Exception:
                continue
        
        return False
    
    def click_preview_resume(self, timeout: float = 15) -> bool:
        """
        点击预览简历按钮
        
        Args:
            timeout: 超时时间
        
        Returns:
            True 表示成功
        """
        try:
            selector_item = self.get_selector("preview_resume")
            el = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable(
                    (selector_item.by, selector_item.selector)
                )
            )
            self._browser.safe_click(el)
            return True
        except TimeoutException:
            try:
                selector_item = self.get_selector("preview_resume")
                el = self.driver.find_element(
                    selector_item.by,
                    selector_item.selector
                )
                if el.is_displayed():
                    self._browser.safe_click(el)
                    return True
            except NoSuchElementException:
                pass
        
        return False
    
    def wait_resume_loaded(self, timeout: float = 30) -> bool:
        """
        等待简历加载完成
        
        Args:
            timeout: 超时时间
        
        Returns:
            True 表示成功
        """
        try:
            selector_item = self.get_selector("attachment_btns")
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(
                    (selector_item.by, selector_item.selector)
                )
            )
            
            deadline = time.time() + min(15, timeout)
            loading_text = self._selectors.get_text("common", "loading_text") or "正在加载简历"
            
            while time.time() < deadline:
                try:
                    body_text = self.driver.find_element(
                        By.TAG_NAME, "body"
                    ).text or ""
                    if loading_text in body_text:
                        time.sleep(0.5)
                        continue
                except Exception:
                    pass
                break
            
            time.sleep(0.5)
            return True
        except TimeoutException:
            return False
    
    def click_download(self, timeout: float = 10) -> bool:
        """
        点击下载按钮
        
        Args:
            timeout: 超时时间
        
        Returns:
            True 表示成功
        """
        try:
            selector_item = self.get_selector("attachment_btns")
            container = self.driver.find_element(
                selector_item.by,
                selector_item.selector
            )
            
            try:
                download_use = container.find_element(
                    By.XPATH,
                    ".//*[name()='use' and (contains(@*[name()='xlink:href'], 'attacthment-download') or contains(@href, 'attacthment-download'))]"
                )
                wrapper = self.driver.execute_script(
                    "var u = arguments[0]; return u.parentElement && u.parentElement.parentElement ? u.parentElement.parentElement : u.parentElement;",
                    download_use
                )
                if wrapper:
                    self.driver.execute_script("arguments[0].click();", wrapper)
                    return True
            except NoSuchElementException:
                pass
            
            try:
                download_svg = container.find_element(
                    By.CSS_SELECTOR,
                    "svg.boss-svg.svg-icon use[xlink\\:href='#icon-attacthment-download'], svg.boss-svg.svg-icon use[href='#icon-attacthment-download']"
                )
                wrapper = self.driver.execute_script(
                    "var u = arguments[0]; return u.parentElement && u.parentElement.parentElement ? u.parentElement.parentElement : u.parentElement;",
                    download_svg
                )
                if wrapper:
                    self.driver.execute_script("arguments[0].click();", wrapper)
                    return True
            except NoSuchElementException:
                pass
            
            popovers = container.find_elements(
                By.CSS_SELECTOR,
                "div.popover.icon-content"
            )
            if len(popovers) >= 3:
                self.driver.execute_script("arguments[0].click();", popovers[2])
                return True
            
            download_div = container.find_element(
                By.XPATH,
                ".//div[contains(@class,'popover-content') and normalize-space(text())='下载']"
            )
            parent = download_div.find_element(
                By.XPATH,
                "./ancestor::div[contains(@class,'popover')][1]"
            )
            self.driver.execute_script("arguments[0].click();", parent)
            return True
        except NoSuchElementException:
            try:
                selector_item = self.get_selector("attachment_btns")
                container = self.driver.find_element(
                    selector_item.by,
                    selector_item.selector
                )
                el = container.find_element(
                    By.XPATH,
                    ".//*[contains(text(),'下载')]"
                )
                self.driver.execute_script("arguments[0].click();", el)
                return True
            except Exception:
                pass
        except Exception as e:
            logger.warning(f"点击下载按钮异常: {e}")
        
        return False
    
    def click_close_preview(self, timeout: float = 5) -> bool:
        """
        点击关闭预览按钮
        
        Args:
            timeout: 超时时间
        
        Returns:
            True 表示成功
        """
        try:
            selector_item = self.get_selector("close_preview")
            el = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable(
                    (selector_item.by, selector_item.selector)
                )
            )
            self.driver.execute_script("arguments[0].click();", el)
            return True
        except (TimeoutException, NoSuchElementException):
            try:
                selector_item = self.get_selector("close_preview")
                el = self.driver.find_element(
                    selector_item.by,
                    selector_item.selector
                )
                if el.is_displayed():
                    self.driver.execute_script("arguments[0].click();", el)
                    return True
            except NoSuchElementException:
                pass
        except Exception as e:
            logger.warning(f"点击关闭按钮异常: {e}")
        
        return False
    
    def has_already_requested_resume(self) -> bool:
        """
        检测是否已请求简历
        
        Returns:
            True 表示已请求
        """
        try:
            self.switch_to_default_content()
            selector_item = self.get_selector("request_resume")
            el = self.driver.find_element(
                selector_item.by,
                selector_item.selector
            )
            return not (el.is_displayed() and el.is_enabled())
        except NoSuchElementException:
            return True
        except Exception:
            return True
    
    def send_chat_message(self, text: str, timeout: float = 5) -> bool:
        """
        发送聊天消息
        
        Args:
            text: 消息内容
            timeout: 超时时间
        
        Returns:
            True 表示成功
        """
        try:
            self.switch_to_default_content()
            
            input_selectors = self.get_selector("chat_input")
            if isinstance(input_selectors, SelectorItem):
                input_selectors = [input_selectors]
            
            inp = None
            for selector_item in input_selectors:
                try:
                    inp = WebDriverWait(self.driver, timeout).until(
                        EC.presence_of_element_located(
                            (selector_item.by, selector_item.selector)
                        )
                    )
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
            logger.warning(f"发送聊天消息异常: {e}")
        
        return False
    
    def click_request_resume_then_confirm(self, timeout: float = 5) -> bool:
        """
        点击求简历按钮并确认
        
        Args:
            timeout: 超时时间
        
        Returns:
            True 表示成功
        """
        try:
            self.switch_to_default_content()
            
            request_selector = self.get_selector("request_resume")
            btn = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable(
                    (request_selector.by, request_selector.selector)
                )
            )
            self._browser.safe_click(btn)
            time.sleep(0.5)
            
            confirm_selector = self.get_selector("confirm_button")
            confirm = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable(
                    (confirm_selector.by, confirm_selector.selector)
                )
            )
            self._browser.safe_click(confirm)
            return True
        except (TimeoutException, NoSuchElementException):
            return False
        except Exception as e:
            logger.warning(f"点击求简历/确定异常: {e}")
        
        return False
    
    def get_item_name_key(self, item: Any) -> Optional[str]:
        """
        从列表项获取候选人标识
        
        Args:
            item: 会话列表项元素
        
        Returns:
            候选人标识字符串
        """
        try:
            name_selector = self.get_selector("chat_list.name")
            title_el = item.find_element(
                name_selector.by,
                name_selector.selector
            )
            name = (title_el.text or "").strip()
            
            job_selector = self.get_selector("chat_list.job")
            job_el = item.find_element(
                job_selector.by,
                job_selector.selector
            )
            job = (job_el.text or "").strip()
            
            key = f"{name} ({job})"
            key = " ".join(key.split()).replace("（", "(").replace("）", ")")
            return key or None
        except Exception:
            return None
