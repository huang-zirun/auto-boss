"""
推荐页面对象

封装推荐牛人页面的操作。
"""
import logging
import time
from typing import Any, List, Optional, Tuple

from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ..config.selectors import SelectorItem
from ..core.exceptions import ElementNotFoundError, RiskControlDetectedError
from .base import BasePage

logger = logging.getLogger(__name__)


class RecommendPage(BasePage):
    """
    推荐牛人页面对象
    
    封装推荐页面的所有操作。
    """
    
    PAGE_NAME = "recommend_page"
    
    DELAY_SHORT = 0.15
    DELAY_MEDIUM = 0.2
    DELAY_HALF = 0.5
    DELAY_LONG = 0.75
    DELAY_REFRESH = 3
    
    def is_loaded(self) -> bool:
        """检查页面是否已加载"""
        try:
            iframe = self._get_frame_element(wait_seconds=5)
            return iframe is not None
        except Exception:
            return False
    
    def _get_frame_element(self, wait_seconds: float = 25) -> Optional[Any]:
        """
        获取推荐页面 iframe 元素
        
        Args:
            wait_seconds: 等待时间
        
        Returns:
            iframe 元素或 None
        """
        self.switch_to_default_content()
        
        try:
            selector_item = self.get_selector("iframe")
            return WebDriverWait(self.driver, wait_seconds).until(
                EC.presence_of_element_located(
                    (selector_item.by, selector_item.selector)
                )
            )
        except TimeoutException:
            pass
        
        for el in self.driver.find_elements(By.TAG_NAME, "iframe"):
            try:
                src = (el.get_attribute("src") or "").lower()
                if "recommend" in src or ("zhipin" in src and "chat" in src):
                    return el
            except Exception:
                continue
        
        return None
    
    def switch_to_frame(self, wait_card_list_seconds: float = 15) -> bool:
        """
        切换到推荐页面 iframe
        
        Args:
            wait_card_list_seconds: 等待卡片列表加载时间
        
        Returns:
            True 表示成功
        """
        try:
            iframe = self._get_frame_element(wait_seconds=25)
            if iframe is None:
                return False
            
            self._browser.switch_to_frame(iframe)
            
            selector_item = self.get_selector("card_list")
            WebDriverWait(self.driver, wait_card_list_seconds).until(
                EC.presence_of_element_located(
                    (selector_item.by, selector_item.selector)
                )
            )
            return True
        except Exception as e:
            logger.warning(f"切换 iframe 失败: {e}")
            return False
    
    def open_filter_panel(self) -> bool:
        """
        打开筛选面板
        
        Returns:
            True 表示成功
        """
        selector_item = self.get_selector("filter.panel")
        try:
            elements = self.find_elements(selector_item)
            for el in elements:
                if "筛选" not in (el.text or ""):
                    continue
                if self.click_element(el, scroll_first=False):
                    time.sleep(self.DELAY_MEDIUM)
                    return True
        except Exception:
            pass
        
        return self._browser.click_by_text("筛选") or self._browser.click_by_text("筛选条件")
    
    def click_filter_option(self, text: str) -> bool:
        """
        点击筛选选项
        
        Args:
            text: 选项文本
        
        Returns:
            True 表示成功
        """
        selector_item = self.get_selector("filter.option")
        try:
            options = self.find_elements(selector_item)
            for el in options:
                if (el.text or "").strip() != text:
                    continue
                
                self.driver.execute_script("""
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
        
        return self._browser.click_by_text(text)
    
    def click_filter_confirm(self) -> bool:
        """
        点击筛选确认按钮
        
        Returns:
            True 表示成功
        """
        selector_item = self.get_selector("filter.confirm")
        try:
            buttons = self.find_elements(selector_item)
            for el in buttons:
                if (el.text or "").strip() != "确定":
                    continue
                if self.click_element(el, scroll_first=False):
                    time.sleep(self.DELAY_MEDIUM)
                    return True
        except Exception:
            pass
        
        return self._browser.click_by_text("确定")
    
    def apply_filters(
        self,
        use_vip_filters: bool,
        filter_school: Optional[str],
        filter_no_resume_exchange: Optional[str],
        filter_education: Optional[List[str]]
    ) -> bool:
        """
        应用筛选条件
        
        Args:
            use_vip_filters: 是否使用 VIP 筛选
            filter_school: 学校筛选
            filter_no_resume_exchange: 简历交换筛选
            filter_education: 学历筛选
        
        Returns:
            True 表示成功应用
        """
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
        except Exception as e:
            logger.warning(f"应用筛选失败: {e}")
        finally:
            try:
                self.switch_to_default_content()
            except Exception:
                pass
        
        return applied
    
    def find_first_greet_button(self) -> Optional[Any]:
        """
        查找第一个可用的打招呼按钮
        
        Returns:
            按钮元素或 None
        """
        try:
            selector_item = self.get_selector("card_list")
            cards = self.find_elements(selector_item)
            
            for card in cards:
                try:
                    greet_selector = self.get_selector("greet_button")
                    btn = card.find_element(
                        greet_selector.by,
                        greet_selector.selector
                    )
                    text = (btn.text or "").strip()
                    
                    if any(s in text for s in ["已沟通", "已打招呼", "继续沟通"]):
                        continue
                    
                    if btn.is_displayed():
                        return btn
                except (NoSuchElementException, StaleElementReferenceException):
                    continue
        except Exception:
            pass
        
        return None
    
    def handle_greet_modal(self, wait_modal_seconds: float = 5) -> bool:
        """
        处理打招呼弹窗
        
        Args:
            wait_modal_seconds: 等待时间
        
        Returns:
            True 表示成功
        """
        try:
            time.sleep(self.DELAY_HALF)
            
            template_selectors = self.get_selector("template")
            if isinstance(template_selectors, SelectorItem):
                template_selectors = [template_selectors]
            
            for selector_item in template_selectors:
                try:
                    el = self.driver.find_element(
                        selector_item.by,
                        selector_item.selector
                    )
                    if el.is_displayed():
                        el.click()
                        time.sleep(self.DELAY_HALF)
                        
                        if self._click_send_button():
                            return True
                except NoSuchElementException:
                    continue
            
            return self._click_send_button()
        except Exception:
            return False
    
    def _click_send_button(self) -> bool:
        """点击发送按钮"""
        send_selectors = self.get_selector("send_button")
        if isinstance(send_selectors, SelectorItem):
            send_selectors = [send_selectors]
        
        for selector_item in send_selectors:
            try:
                btn = self.driver.find_element(
                    selector_item.by,
                    selector_item.selector
                )
                if btn.is_displayed():
                    btn.click()
                    return True
            except NoSuchElementException:
                continue
        
        return False
    
    def check_and_close_payment_popup(self) -> bool:
        """
        检查并关闭付费弹窗
        
        Returns:
            True 表示检测到付费弹窗
        """
        try:
            container_selector = self.get_selector("payment_popup.container")
            popup = self.find_element(container_selector)
            
            if popup.is_displayed():
                try:
                    close_selector = self.get_selector("payment_popup.close")
                    close_btn = self.find_element(close_selector)
                    close_btn.click()
                    time.sleep(self.DELAY_HALF)
                except Exception:
                    pass
                return True
        except Exception:
            pass
        
        return False
    
    def get_all_jobs(self) -> List[str]:
        """
        获取所有岗位列表
        
        Returns:
            岗位名称列表
        """
        try:
            trigger = self._open_job_dropdown()
            options = self._find_job_options()
            
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
    
    def _open_job_dropdown(self) -> Any:
        """打开岗位下拉菜单"""
        self.switch_to_default_content()
        self._close_overlay()
        
        iframe = self._get_frame_element(wait_seconds=10)
        if iframe is not None:
            self._browser.switch_to_frame(iframe)
        
        trigger_selector = self.get_selector("job_dropdown.trigger")
        trigger = self.find_element(trigger_selector)
        trigger.click()
        
        try:
            WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div.ui-dropmenu-visible")
                )
            )
        except TimeoutException:
            time.sleep(0.8)
        
        return trigger
    
    def _find_job_options(self) -> List[Any]:
        """查找岗位选项"""
        option_selectors = self.get_selector("job_dropdown.option")
        if isinstance(option_selectors, SelectorItem):
            option_selectors = [option_selectors]
        
        for selector_item in option_selectors:
            try:
                els = self.driver.find_elements(
                    selector_item.by,
                    selector_item.selector
                )
                if any((e.text or "").strip() for e in els):
                    return els
            except Exception:
                continue
        
        return []
    
    def _close_dropdown(self, trigger: Optional[Any] = None) -> None:
        """关闭下拉菜单"""
        try:
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except Exception:
            if trigger:
                try:
                    trigger.click()
                except Exception:
                    pass
        
        time.sleep(self.DELAY_MEDIUM)
    
    def _close_overlay(self) -> None:
        """关闭遮罩层"""
        for sel in (".boss-layer__wrapper", ".dialog-container", ".layer-wrapper"):
            try:
                for el in self.driver.find_elements(By.CSS_SELECTOR, sel):
                    if el.is_displayed():
                        self.driver.execute_script(
                            "arguments[0].style.display='none';",
                            el
                        )
            except Exception:
                pass
    
    def switch_to_job(self, job_text: str) -> bool:
        """
        切换到指定岗位
        
        Args:
            job_text: 岗位名称
        
        Returns:
            True 表示成功
        """
        try:
            trigger = self._open_job_dropdown()
            options = self._find_job_options()
            
            for el in options:
                try:
                    text = (el.text or "").strip()
                    if not text:
                        continue
                    
                    if job_text in text or text in job_text:
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});",
                            el
                        )
                        time.sleep(self.DELAY_MEDIUM)
                        
                        try:
                            el.click()
                        except Exception:
                            self.driver.execute_script(
                                "arguments[0].click();",
                                el
                            )
                        
                        time.sleep(self.DELAY_REFRESH)
                        return True
                except Exception:
                    continue
            
            self._close_dropdown(trigger)
            logger.warning(f"未找到岗位: {job_text}")
            return False
        except Exception as e:
            logger.warning(f"切换岗位失败: {e}")
            return False
    
    def close_greet_panel(self) -> None:
        """关闭打招呼面板"""
        try:
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(self.DELAY_SHORT)
        except Exception:
            pass
        
        close_selectors = self.get_selector("close_button")
        if isinstance(close_selectors, SelectorItem):
            close_selectors = [close_selectors]
        
        for selector_item in close_selectors:
            try:
                el = self.driver.find_element(
                    selector_item.by,
                    selector_item.selector
                )
                if el.is_displayed():
                    el.click()
                    time.sleep(self.DELAY_SHORT)
                    break
            except NoSuchElementException:
                continue
