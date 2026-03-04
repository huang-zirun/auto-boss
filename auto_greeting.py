from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import time
import random
import socket

def _is_port_open(host, port, timeout=1):
    """检测端口是否有进程在监听，避免无谓的长连接等待。"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False

class BossAutoGreeting:
    def __init__(self, driver_path=None, user_data_dir=None, debug_port=9222):
        self.driver = None
        port = int(debug_port) if debug_port else 0
        # 仅当端口有监听时才尝试连接已有浏览器，否则会长时间超时
        if port and _is_port_open("127.0.0.1", port):
            try:
                opts = webdriver.ChromeOptions()
                opts.add_experimental_option("debuggerAddress", f"127.0.0.1:{port}")
                self.driver = webdriver.Chrome(options=opts) if not driver_path else webdriver.Chrome(executable_path=driver_path, options=opts)
                print("已连接已有浏览器，无需重新登录。")
            except Exception as e:
                print("连接已有浏览器失败，将启动新浏览器:", e)
                self.driver = None
        elif port:
            print("未检测到已有浏览器，正在启动新浏览器...")
        if self.driver is None:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-software-rasterizer")
            if port:
                chrome_options.add_argument(f"--remote-debugging-port={port}")
            try:
                if driver_path:
                    self.driver = webdriver.Chrome(executable_path=driver_path, options=chrome_options)
                else:
                    self.driver = webdriver.Chrome(options=chrome_options)
            except Exception as e:
                if port:
                    raise RuntimeError(
                        f"启动浏览器失败（当前调试端口 {port}）。若报错含 port/address，请换一个端口：在 config.py 中修改 debug_port（如 9222、9233），或改为 0 关闭复用功能。"
                    ) from e
                raise
        self.driver.maximize_window()

    def _is_logged_in(self):
        """检测当前是否已登录（通过退出登录入口或关键 Cookie）。"""
        try:
            # 方式1：页面上存在「退出登录」链接（登录后才有）
            logout_selectors = [
                (By.CSS_SELECTOR, "a.link-signout"),
                (By.XPATH, "//a[contains(text(), '退出登录')]"),
                (By.XPATH, "//*[contains(text(), '退出登录')]"),
            ]
            for by, selector in logout_selectors:
                try:
                    el = self.driver.find_element(by, selector)
                    if el.is_displayed():
                        return True
                except NoSuchElementException:
                    continue
            # 方式2：存在登录态 Cookie（zp_at 等）
            cookies = self.driver.get_cookies()
            names = {c.get("name") for c in cookies}
            if "zp_at" in names or "wt2" in names:
                return True
        except Exception:
            pass
        return False

    def _ensure_recommend_window(self, redirect_url):
        """若当前标签是 data:, 或非 zhipin 页，尝试切换到包含推荐页的标签；若只有 data:, 则重载推荐页并多等 iframe 加载。"""
        try:
            current = (self.driver.current_url or "").strip().lower()
            if current.startswith("data:") or "zhipin.com" not in current:
                for handle in self.driver.window_handles:
                    self.driver.switch_to.window(handle)
                    u = (self.driver.current_url or "").strip().lower()
                    if "zhipin.com" in u and ("recommend" in u or "chat" in u):
                        return
                # 只有 data:, 等单标签时：重载推荐页并多等 iframe 出现
                self.driver.get(redirect_url)
                time.sleep(4)
        except Exception:
            pass

    def _get_recommend_frame_element(self, wait_seconds=25):
        """获取推荐页 iframe 元素：先按 name=recommendFrame，再按 src 含 recommend/zhipin。"""
        self.driver.switch_to.default_content()
        try:
            iframe = WebDriverWait(self.driver, wait_seconds).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[name='recommendFrame']"))
            )
            return iframe
        except Exception:
            pass
        for el in self.driver.find_elements(By.TAG_NAME, "iframe"):
            try:
                src = (el.get_attribute("src") or "").lower()
                if "recommend" in src or ("zhipin" in src and "chat" in src):
                    return el
            except Exception:
                continue
        return None

    def login(self, url="https://www.zhipin.com/", redirect_url="https://www.zhipin.com/web/chat/recommend", wait_login_timeout=300):
        """打开网站，自动检测登录状态；登录成功后自动跳转到 redirect_url。"""
        self.driver.get(url)
        print("请在浏览器中完成登录，脚本将自动检测登录状态并跳转到推荐牛人页面...")
        start = time.time()
        while (time.time() - start) < wait_login_timeout:
            time.sleep(1)
            if self._is_logged_in():
                print("检测到已登录，正在跳转到推荐牛人页面...")
                self.driver.get(redirect_url)
                time.sleep(1.5)
                self._ensure_recommend_window(redirect_url)
                print("已打开推荐牛人页面")
                return
            print("尚未检测到登录，请完成登录后等待自动跳转...")
        print("等待登录超时，将尝试直接打开目标页面（若未登录可能无法使用）。")
        self.driver.get(redirect_url)
        time.sleep(1.5)
        self._ensure_recommend_window(redirect_url)
    
    def get_essential_cookies(self):
        """获取Boss直聘核心登录Cookie"""
        all_cookies = self.driver.get_cookies()
        essential_names = ['zp_at', 'wt2', 'wbg', 'HMACCOUNT']
        essential_cookies = [c for c in all_cookies if c['name'] in essential_names]
        return essential_cookies
    
    def debug_page_elements(self):
        """调试功能：打印页面上所有可能的按钮元素"""
        print("\n========== 开始调试页面元素 ==========")
        
        # 首先检查是否有iframe
        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
        print(f"\n找到 {len(iframes)} 个 iframe:")
        for i, iframe in enumerate(iframes):
            try:
                name = iframe.get_attribute("name")
                src = iframe.get_attribute("src")
                print(f"  [{i}] name: '{name}' | src: '{src[:80]}...' " if len(str(src)) > 80 else f"  [{i}] name: '{name}' | src: '{src}'")
            except:
                pass
        
        # 尝试切换到推荐页面的iframe
        iframe_switched = False
        if iframes:
            try:
                iframe = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[name='recommendFrame']"))
                )
                self.driver.switch_to.frame(iframe)
                print("\n已切换到 iframe 'recommendFrame'")
                iframe_switched = True
            except:
                try:
                    self.driver.switch_to.frame(0)
                    print("\n已切换到第1个iframe")
                    iframe_switched = True
                except Exception as e:
                    print(f"\n切换iframe失败: {e}")
        
        # 给iframe内页面加载时间
        if iframe_switched:
            time.sleep(1.5)
        
        # 查找所有按钮
        all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
        print(f"\n找到 {len(all_buttons)} 个 button 元素:")
        for i, btn in enumerate(all_buttons[:15]):
            try:
                text = btn.text.strip()
                class_name = btn.get_attribute("class")
                onclick = btn.get_attribute("onclick")
                print(f"  [{i}] 文本: '{text}' | class: '{class_name}' | onclick: '{onclick}'")
            except:
                pass
        
        # 查找包含特定文本的元素
        print("\n查找包含特定文本的元素:")
        text_patterns = ["打招呼", "立即沟通", "沟通", "开始沟通", "发送"]
        for pattern in text_patterns:
            elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{pattern}')]")
            if elements:
                print(f"\n  包含'{pattern}'的元素: {len(elements)} 个")
                for elem in elements[:3]:
                    try:
                        tag = elem.tag_name
                        text = elem.text.strip()
                        class_name = elem.get_attribute("class")
                        print(f"    <{tag}> 文本: '{text}' | class: '{class_name}'")
                    except:
                        pass
        
        # 查找可能的选择器
        print("\n尝试常见class选择器:")
        class_selectors = [
            "[class*='greet']",
            "[class*='chat']",
            "[class*='btn-primary']",
            "[class*='btn-start']",
            "[data-type='greet']",
            "[data-type='chat']",
            "a[href*='chat']",
            ".btn-operate"
        ]
        for selector in class_selectors:
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                print(f"  '{selector}': 找到 {len(elements)} 个元素")
                for elem in elements[:3]:
                    try:
                        text = elem.text.strip()
                        class_name = elem.get_attribute("class")
                        print(f"    文本: '{text}' | class: '{class_name}'")
                    except:
                        pass
        
        # 查找所有链接
        all_links = self.driver.find_elements(By.TAG_NAME, "a")
        print(f"\n找到 {len(all_links)} 个 a 元素:")
        chat_links = [link for link in all_links if 'chat' in (link.get_attribute('href') or '')]
        if chat_links:
            print(f"  其中包含'chat'的链接: {len(chat_links)} 个")
            for i, link in enumerate(chat_links[:5]):
                try:
                    text = link.text.strip()
                    href = link.get_attribute("href")
                    print(f"    [{i}] 文本: '{text}' | href: '{href}'")
                except:
                    pass
        
        # 保存页面源码供分析
        try:
            page_source = self.driver.page_source
            with open("page_debug.html", "w", encoding="utf-8") as f:
                f.write(page_source)
            print("\n页面源码已保存到 page_debug.html")
        except Exception as e:
            print(f"保存页面源码失败: {e}")
        
        # 切换回主页面
        if iframe_switched:
            try:
                self.driver.switch_to.default_content()
                print("\n已切换回主页面")
            except:
                pass
        
        print("\n========== 调试结束 ==========\n")
        input("按回车键继续...")

    def _safe_click(self, element):
        try:
            element.click()
            return True
        except Exception:
            try:
                self.driver.execute_script("arguments[0].click();", element)
                return True
            except Exception:
                return False

    def _click_by_text(self, text, log):
        try:
            el = self.driver.find_element(By.XPATH, f"//*[contains(text(), '{text}')]")
            if not (el.is_displayed() and el.is_enabled()):
                log(f"[筛选]   _click_by_text('{text}') -> 元素不可见或不可用")
                return False
            if self._safe_click(el):
                time.sleep(0.2)
                log(f"[筛选]   _click_by_text('{text}') -> 成功")
                return True
            log(f"[筛选]   _click_by_text('{text}') -> 点击失败")
        except NoSuchElementException:
            log(f"[筛选]   _click_by_text('{text}') -> 未找到元素")
        return False

    def _open_filter_panel(self, log):
        for sel in ("div.filter-label", ".filter-label"):
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, sel)
                log(f"[筛选] 选择器 '{sel}' 找到 {len(elements)} 个元素")
                for el in elements:
                    if "筛选" not in (el.text or ""):
                        continue
                    if self._safe_click(el):
                        time.sleep(0.2)
                        log("[筛选] 通过 CSS 选择器点击筛选按钮 -> 成功")
                        return True
            except Exception as e:
                log(f"[筛选] 选择器 '{sel}' 异常: {e}")
        log("[筛选] CSS 选择器未找到筛选按钮，回退到文本匹配...")
        result = self._click_by_text("筛选", log) or self._click_by_text("筛选条件", log)
        log(f"[筛选] 文本匹配回退结果: {result}")
        return result

    def _click_filter_option(self, text, log):
        try:
            options = self.driver.find_elements(By.CSS_SELECTOR, "div.option")
            log(f"[筛选] 查找选项 '{text}' | div.option 共 {len(options)} 个")
            for i, el in enumerate(options):
                el_text = (el.text or "").strip()
                if i < 20:
                    log(f"[筛选]   [{i}] 文本='{el_text}' class='{el.get_attribute('class')}'")
                if el_text != text:
                    continue
                self.driver.execute_script("""
                    var mask = document.querySelector('.vip-mask');
                    if (mask) { mask.style.pointerEvents = 'none'; }
                    arguments[0].scrollIntoView({block: 'center'});
                    arguments[0].click();
                    if (mask) { mask.style.pointerEvents = ''; }
                """, el)
                time.sleep(0.2)
                log(f"[筛选] 点击选项 '{text}' -> 成功")
                return True
        except Exception as e:
            log(f"[筛选] _click_filter_option 异常: {e}")
        return self._click_by_text(text, log)

    def _click_filter_confirm(self, log):
        try:
            buttons = self.driver.find_elements(By.CSS_SELECTOR, "div.btn")
            log(f"[筛选] 查找确定按钮 | div.btn 共 {len(buttons)} 个")
            for i, el in enumerate(buttons):
                el_text = (el.text or "").strip()
                log(f"[筛选]   [{i}] 文本='{el_text}' class='{el.get_attribute('class')}'")
                if el_text != "确定":
                    continue
                if self._safe_click(el):
                    time.sleep(0.2)
                    log("[筛选] 点击确定按钮 -> 成功")
                    return True
        except Exception as e:
            log(f"[筛选] _click_filter_confirm 异常: {e}")
        return self._click_by_text("确定", log)
    
    def _apply_recommend_filters(self, use_vip_filters, filter_school, filter_no_resume_exchange, filter_education, debug_filter=False):
        """在推荐页 iframe 内应用筛选条件。"""
        _log = print if debug_filter else lambda *a, **k: None

        _log(f"[筛选] 开始应用筛选 | use_vip={use_vip_filters}, school={filter_school}, "
             f"no_resume_exchange={filter_no_resume_exchange}, education={filter_education}")

        applied = False
        iframe = self._get_recommend_frame_element(wait_seconds=25)
        if iframe is None:
            _log("[筛选] 未找到推荐页 iframe，放弃筛选")
            return False
        _log(f"[筛选] 找到 iframe: name='{iframe.get_attribute('name')}' src='{(iframe.get_attribute('src') or '')[:80]}'")
        try:
            self.driver.switch_to.frame(iframe)
            _log("[筛选] 已切换到 iframe")
        except Exception as e:
            _log(f"[筛选] 切换 iframe 失败: {e}")
            return False

        try:
            time.sleep(1)
            page_text_sample = self.driver.execute_script(
                "return document.body ? document.body.innerText.substring(0, 300) : '(body为空)'"
            )
            _log(f"[筛选] iframe 内页面文本前300字: {repr(page_text_sample)}")
            all_divs = self.driver.find_elements(By.CSS_SELECTOR, "div")
            _log(f"[筛选] iframe 内共 {len(all_divs)} 个 div 元素")

            filter_opened = self._open_filter_panel(_log)
            _log(f"[筛选] 筛选面板打开结果: {filter_opened}")
            if filter_opened:
                time.sleep(0.6)
            else:
                _log("[筛选] ⚠ 筛选面板未能打开，后续选项点击大概率失败")

            if use_vip_filters and filter_school:
                result = self._click_filter_option(filter_school, _log)
                _log(f"[筛选] 院校筛选 '{filter_school}': {result}")
                if result:
                    applied = True
            if use_vip_filters and filter_no_resume_exchange:
                result = self._click_filter_option(filter_no_resume_exchange, _log)
                _log(f"[筛选] 简历交换筛选 '{filter_no_resume_exchange}': {result}")
                if result:
                    applied = True
            for edu in (filter_education or []):
                if edu:
                    result = self._click_filter_option(edu, _log)
                    _log(f"[筛选] 学历筛选 '{edu}': {result}")
                    if result:
                        applied = True

            confirm_result = self._click_filter_confirm(_log)
            _log(f"[筛选] 确定按钮点击结果: {confirm_result}")
            if confirm_result:
                applied = True
                time.sleep(0.75)
        except Exception as e:
            _log(f"[筛选] 筛选过程异常: {e}")
        finally:
            try:
                self.driver.switch_to.default_content()
            except Exception:
                pass

        _log(f"[筛选] 最终结果: applied={applied}")
        if applied:
            print("已应用筛选条件")
        return applied

    def _switch_to_recommend_frame(self, wait_card_list_seconds=15):
        """切换到推荐页 iframe 并等待列表出现。"""
        try:
            iframe = self._get_recommend_frame_element(wait_seconds=25)
            if iframe is None:
                return False
            self.driver.switch_to.frame(iframe)
            WebDriverWait(self.driver, wait_card_list_seconds).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".card-list .card-item"))
            )
            return True
        except Exception:
            return False

    def _find_first_greet_button(self):
        """在候选人卡片中找到首个可用的打招呼按钮。"""
        try:
            cards = self.driver.find_elements(By.CSS_SELECTOR, ".card-list .card-item")
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

    def _handle_greet_modal(self, greeting_message, wait_modal_seconds=5):
        """处理打招呼弹窗并尝试发送消息。"""
        try:
            time.sleep(0.5)
            input_selectors = [
                "textarea[placeholder*='消息']",
                "textarea[placeholder*='输入']",
                "textarea[placeholder*='请输入']",
                "div[contenteditable='true']",
                "textarea",
            ]
            for selector in input_selectors:
                try:
                    inp = WebDriverWait(self.driver, 2).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if inp.is_displayed() and inp.is_enabled():
                        inp.click()
                        time.sleep(0.15)
                        inp.clear()
                        inp.send_keys(greeting_message)
                        time.sleep(0.25)
                        send_btn = self._find_send_button()
                        if send_btn:
                            send_btn.click()
                            return True
                        break
                except (TimeoutException, NoSuchElementException):
                    continue
            try:
                template_selectors = [
                    "//div[contains(@class,'greet')]//div[contains(@class,'item') or contains(@class,'template')]",
                    "//li[contains(@class,'template') or contains(@class,'greet')]",
                    "//*[contains(text(), '使用') and contains(text(), '招呼')]",
                    "//*[contains(text(), '选择') and contains(text(), '语')]",
                ]
                for xpath in template_selectors:
                    try:
                        el = self.driver.find_element(By.XPATH, xpath)
                        if el.is_displayed():
                            el.click()
                            time.sleep(0.5)
                            send_btn = self._find_send_button()
                            if send_btn:
                                send_btn.click()
                                return True
                    except NoSuchElementException:
                        continue
            except Exception:
                pass
            send_btn = self._find_send_button()
            if send_btn:
                send_btn.click()
                return True
        except Exception:
            pass
        return False

    def _find_send_button(self):
        """在当前上下文中查找「发送」按钮。"""
        send_selectors = [
            (By.XPATH, "//button[contains(text(), '发送')]"),
            (By.XPATH, "//*[@role='button' and contains(text(), '发送')]"),
            (By.CSS_SELECTOR, "button[class*='send']"),
            (By.CSS_SELECTOR, ".btn-send"),
        ]
        for by, selector in send_selectors:
            try:
                btn = self.driver.find_element(by, selector)
                if btn.is_displayed():
                    return btn
            except NoSuchElementException:
                continue
        return None

    def _close_greet_panel(self):
        """关闭招呼弹窗/侧栏：ESC 或关闭按钮。"""
        try:
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(0.15)
        except Exception:
            pass
        for xpath in [
            "//div[contains(@class,'close')]",
            "//i[contains(@class,'close')]",
            "//button[contains(@class,'close')]",
            "//*[@aria-label='关闭']",
        ]:
            try:
                el = self.driver.find_element(By.XPATH, xpath)
                if el.is_displayed():
                    el.click()
                    time.sleep(0.15)
                    break
            except NoSuchElementException:
                continue

    def auto_greeting_recommend_page(
        self,
        greeting_message,
        max_count=100,
        interval_min=2.0,
        interval_max=5.0,
        wait_card_list_seconds=15,
        wait_modal_seconds=5,
        use_vip_filters=False,
        filter_school=None,
        filter_no_resume_exchange=None,
        filter_education=None,
        debug_filter=False,
    ):
        """在推荐页自动打招呼。"""
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

            applied = self._apply_recommend_filters(
                use_vip_filters=use_vip_filters,
                filter_school=filter_school,
                filter_no_resume_exchange=filter_no_resume_exchange,
                filter_education=filter_education or [],
                debug_filter=debug_filter,
            )
            has_filter_config = bool(filter_education or (use_vip_filters and (filter_school or filter_no_resume_exchange)))
            if has_filter_config and not applied:
                print("提示：已配置筛选但未成功应用，请检查页面或手动点选筛选后再运行。")
            time.sleep(2)

            if not self._switch_to_recommend_frame(wait_card_list_seconds=wait_card_list_seconds):
                print("切换推荐页 iframe 或等待列表失败，请确认已在推荐牛人页。")
                return 0

            print("已进入推荐列表，开始自动打招呼...")

            while count < max_count:
                try:
                    btn = self._find_first_greet_button()
                    if btn is None:
                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(1)
                        new_height = self.driver.execute_script("return document.body.scrollHeight")
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
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", btn)
                        time.sleep(0.25)
                    except StaleElementReferenceException:
                        continue
                    try:
                        btn.click()
                    except Exception:
                        try:
                            self.driver.execute_script("arguments[0].click();", btn)
                        except Exception as e:
                            print(f"点击失败: {e}")
                            continue

                    time.sleep(0.75)
                    self._handle_greet_modal(greeting_message, wait_modal_seconds=wait_modal_seconds)
                    time.sleep(0.5)
                    self._close_greet_panel()
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
                self.driver.switch_to.default_content()
            except Exception:
                pass

            print(f"自动打招呼结束，共 {count} 人。")
            return count
        except Exception as e:
            print(f"自动打招呼过程错误: {e}")
            return 0

    def close(self):
        try:
            self.driver.quit()
            print("浏览器已关闭")
        except Exception:
            pass  # 浏览器可能已关闭或连接已断开，静默处理

if __name__ == "__main__":
    import config

    bot = BossAutoGreeting(driver_path=config.driver_path, user_data_dir=config.user_data_dir, debug_port=getattr(config, "debug_port", 9222))

    try:
        bot.login(
            url=config.login_url,
            redirect_url=config.recommend_page_url,
            wait_login_timeout=getattr(config, "wait_login_timeout", 300),
        )

        bot.auto_greeting_recommend_page(
            config.greeting_message,
            max_count=config.max_count,
            interval_min=config.interval_min,
            interval_max=config.interval_max,
            wait_card_list_seconds=config.wait_card_list_seconds,
            wait_modal_seconds=config.wait_modal_seconds,
            use_vip_filters=getattr(config, "use_vip_filters", False),
            filter_school=getattr(config, "filter_school", None),
            filter_no_resume_exchange=getattr(config, "filter_no_resume_exchange", None),
            filter_education=getattr(config, "filter_education", []),
            debug_filter=getattr(config, "debug_filter", False),
        )
    finally:
        bot.close()