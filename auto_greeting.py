from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import os

class BossAutoGreeting:
    def __init__(self, driver_path=None, user_data_dir=None):
        # 配置Chrome选项
        chrome_options = webdriver.ChromeOptions()
        
        # 解决DevToolsActivePort错误的关键参数
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--remote-debugging-port=0")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-software-rasterizer")
        
        # 使用干净的浏览器，不加载用户数据目录
        
        if driver_path:
            self.driver = webdriver.Chrome(executable_path=driver_path, options=chrome_options)
        else:
            self.driver = webdriver.Chrome(options=chrome_options)
        
        self.driver.maximize_window()
    
    def login(self, url="https://www.zhipin.com/"):
        """打开网站并等待用户手动登录"""
        self.driver.get(url)
        print("请在浏览器中登录您的账号，登录完成后按Enter键继续...")
        input()
        print("登录完成，正在跳转到推荐页面...")
        # 登录成功后跳转到推荐页面
        self.driver.get("https://www.zhipin.com/web/chat/recommend")
        time.sleep(3)
        print("已打开推荐页面")
    
    def get_essential_cookies(self):
        """获取Boss直聘核心登录Cookie"""
        all_cookies = self.driver.get_cookies()
        essential_names = ['zp_at', 'wt2', 'wbg', 'HMACCOUNT']
        essential_cookies = [c for c in all_cookies if c['name'] in essential_names]
        return essential_cookies
    
    def auto_greeting(self, keywords, greeting_message, max_count=10):
        try:
            # 搜索职位
            search_box = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='搜索职位、公司或地点']"))
            )
            search_box.clear()
            search_box.send_keys(keywords)
            search_box.submit()
            
            time.sleep(3)
            
            # 开始打招呼
            count = 0
            while count < max_count:
                try:
                    # 查找打招呼按钮
                    greeting_buttons = WebDriverWait(self.driver, 15).until(
                        EC.presence_of_all_elements_located((By.XPATH, "//button[contains(text(), '立即沟通') or contains(text(), '打招呼')]"))
                    )
                    
                    if not greeting_buttons:
                        print("没有找到可打招呼的职位")
                        break
                    
                    for button in greeting_buttons:
                        if count >= max_count:
                            break
                        
                        try:
                            # 点击打招呼按钮
                            button.click()
                            time.sleep(2)
                            
                            # 输入打招呼消息
                            message_input = WebDriverWait(self.driver, 15).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[placeholder='请输入消息']"))
                            )
                            message_input.clear()
                            message_input.send_keys(greeting_message)
                            time.sleep(1)
                            
                            # 发送消息
                            send_button = WebDriverWait(self.driver, 15).until(
                                EC.presence_of_element_located((By.XPATH, "//button[contains(text(), '发送')]"))
                            )
                            send_button.click()
                            time.sleep(3)
                            
                            count += 1
                            print(f"已向 {count} 个职位打招呼")
                            
                        except Exception as e:
                            print(f"操作失败: {e}")
                            time.sleep(2)
                            continue
                    
                    # 翻页
                    try:
                        next_page_button = WebDriverWait(self.driver, 15).until(
                            EC.presence_of_element_located((By.XPATH, "//a[contains(text(), '下一页')]"))
                        )
                        next_page_button.click()
                        time.sleep(3)
                    except Exception as e:
                        print(f"翻页失败: {e}")
                        break
                    
                except Exception as e:
                    print(f"错误: {e}")
                    time.sleep(2)
                    continue
            
            print(f"自动打招呼完成，共向 {count} 个职位打招呼")
            return count
        except Exception as e:
            print(f"自动打招呼过程中出现错误: {e}")
            return 0
    
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
            time.sleep(3)
        
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
    
    def auto_greeting_recommend_page(self, greeting_message, max_count=100):
        """
        在推荐页面自动打招呼
        适用于: https://www.zhipin.com/web/chat/recommend
        会持续滚动页面直到页面结束或达到最大数量
        """
        try:
            count = 0
            processed_buttons = set()
            no_new_content_count = 0
            last_height = 0
            
            print("开始自动打招呼...")
            
            # 等待iframe加载并切换到iframe
            print("等待推荐页面加载...")
            time.sleep(5)
            
            # 尝试切换到推荐页面的iframe
            iframe_found = False
            try:
                iframe = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[name='recommendFrame']"))
                )
                self.driver.switch_to.frame(iframe)
                print("已切换到推荐页面iframe")
                iframe_found = True
            except Exception as e:
                print(f"切换iframe失败: {e}")
                print("尝试在主页面查找元素...")
                iframe_found = False
            
            # 给iframe内页面额外加载时间
            time.sleep(5)
            
            while count < max_count:
                try:
                    # 使用更全面的选择器查找打招呼按钮
                    greeting_buttons = []
                    
                    # 方法1: 查找包含"打招呼"、"立即沟通"、"沟通"等文本的按钮
                    text_patterns = ["打招呼", "立即沟通", "沟通", "开始沟通"]
                    for pattern in text_patterns:
                        buttons = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{pattern}')]")
                        greeting_buttons.extend(buttons)
                    
                    # 方法2: 查找button元素
                    greeting_buttons.extend(self.driver.find_elements(By.TAG_NAME, "button"))
                    
                    # 方法3: 查找可能的选择器
                    css_selectors = [
                        "[class*='greet']",
                        "[class*='chat']",
                        "[class*='btn-primary']",
                        "[class*='btn-start']",
                        "[data-type='greet']",
                        "[data-type='chat']",
                        "a[href*='chat']",
                        ".btn-operate"
                    ]
                    for selector in css_selectors:
                        greeting_buttons.extend(self.driver.find_elements(By.CSS_SELECTOR, selector))
                    
                    # 去重
                    unique_buttons = []
                    seen_outer_html = set()
                    for btn in greeting_buttons:
                        try:
                            outer_html = btn.get_attribute("outerHTML")
                            if outer_html and outer_html not in seen_outer_html:
                                seen_outer_html.add(outer_html)
                                unique_buttons.append(btn)
                        except:
                            pass
                    
                    new_buttons_found = False
                    
                    for button in unique_buttons:
                        if count >= max_count:
                            break
                        
                        # 获取按钮的唯一标识
                        try:
                            button_id = button.get_attribute("outerHTML")
                        except:
                            continue
                        
                        # 跳过已处理的按钮
                        if button_id in processed_buttons:
                            continue
                        
                        try:
                            # 获取按钮文本
                            button_text = button.text.strip()
                            
                            # 检查按钮是否可点击（没有被点击过）
                            if not button_text or "已沟通" in button_text or "已打招呼" in button_text or "继续沟通" in button_text:
                                processed_buttons.add(button_id)
                                continue
                            
                            # 滚动到按钮位置
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", button)
                            time.sleep(1)
                            
                            # 尝试点击按钮
                            try:
                                button.click()
                            except:
                                # 尝试使用JavaScript点击
                                self.driver.execute_script("arguments[0].click();", button)
                            
                            processed_buttons.add(button_id)
                            new_buttons_found = True
                            time.sleep(2)
                            
                            # 处理可能出现的弹窗 - 输入打招呼消息
                            try:
                                # 等待弹窗出现，尝试多种选择器
                                message_input = None
                                input_selectors = [
                                    "textarea[placeholder*='消息']",
                                    "textarea[placeholder*='输入']",
                                    "div[contenteditable='true']",
                                    ".chat-input textarea",
                                    "textarea.chat-input",
                                    "textarea"
                                ]
                                
                                for selector in input_selectors:
                                    try:
                                        message_input = WebDriverWait(self.driver, 2).until(
                                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                                        )
                                        if message_input and message_input.is_displayed():
                                            break
                                    except:
                                        continue
                                
                                if message_input:
                                    message_input.clear()
                                    message_input.send_keys(greeting_message)
                                    time.sleep(1)
                                    
                                    # 发送消息
                                    send_button = None
                                    send_selectors = [
                                        "//button[contains(text(), '发送')]",
                                        "//button[contains(@class, 'send')]",
                                        "//button[contains(@class, 'submit')]",
                                        ".btn-send",
                                        ".btn-submit"
                                    ]
                                    
                                    for selector in send_selectors:
                                        try:
                                            if selector.startswith("//"):
                                                send_button = self.driver.find_element(By.XPATH, selector)
                                            else:
                                                send_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                                            if send_button and send_button.is_displayed():
                                                break
                                        except:
                                            continue
                                    
                                    if send_button:
                                        send_button.click()
                                        time.sleep(2)
                            except Exception as e:
                                # 可能不需要输入消息，直接打招呼成功
                                pass
                            
                            count += 1
                            print(f"已向 {count} 个候选人打招呼")
                            no_new_content_count = 0
                            
                            # 关闭聊天窗口（如果有弹窗）
                            try:
                                close_selectors = [
                                    "//div[contains(@class, 'close')]",
                                    "//i[contains(@class, 'close')]",
                                    "//button[contains(@class, 'close')]",
                                    ".close-btn",
                                    ".modal-close"
                                ]
                                for selector in close_selectors:
                                    try:
                                        close_btn = self.driver.find_element(By.XPATH, selector)
                                        close_btn.click()
                                        time.sleep(0.5)
                                    except:
                                        pass
                            except:
                                pass
                            
                            # 按ESC键关闭可能的弹窗
                            try:
                                self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                                time.sleep(0.5)
                            except:
                                pass
                            
                        except Exception as e:
                            print(f"点击按钮失败: {e}")
                            continue
                    
                    # 滚动页面加载更多内容
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(3)
                    
                    # 检查页面高度是否变化
                    new_height = self.driver.execute_script("return document.body.scrollHeight")
                    
                    if new_height == last_height and not new_buttons_found:
                        no_new_content_count += 1
                        print(f"没有新内容加载，计数: {no_new_content_count}/3")
                    else:
                        no_new_content_count = 0
                        last_height = new_height
                    
                    # 如果连续3次没有新内容，认为页面已结束
                    if no_new_content_count >= 3:
                        print("页面已滚动到底部，没有更多内容")
                        break
                    
                except Exception as e:
                    print(f"处理过程中出错: {e}")
                    time.sleep(2)
                    continue
            
            # 切换回主页面
            try:
                self.driver.switch_to.default_content()
            except:
                pass
            
            print(f"自动打招呼完成，共向 {count} 个候选人打招呼")
            return count
        except Exception as e:
            print(f"自动打招呼过程中出现错误: {e}")
            return 0

    def close(self):
        try:
            self.driver.quit()
            print("浏览器已关闭")
        except Exception:
            pass  # 浏览器可能已关闭或连接已断开，静默处理

if __name__ == "__main__":
    # ==================== 配置参数 ====================
    driver_path = ""  # 如果ChromeDriver不在PATH中，需要指定路径
    user_data_dir = r"C:\Users\Admin\AppData\Local\Google\Chrome\User Data\Profile 2"  # Chrome用户数据目录，保持登录状态
    
    # 自动打招呼配置
    keywords = "Python开发"
    greeting_message = "您好，我对贵公司的职位很感兴趣，期待能有机会与您沟通！"
    max_count = 20
    
    # 模式选择: "search" 使用搜索模式, "recommend" 使用推荐页面模式
    mode = "recommend"  # 修改为 "recommend" 以使用推荐页面打招呼
    # =================================================
    
    bot = BossAutoGreeting(driver_path=driver_path, user_data_dir=user_data_dir)
    
    try:
        # 登录：打开网站等待用户手动登录
        bot.login()
        
        # 根据模式选择打招呼方式
        if mode == "recommend":
            # 在推荐页面打招呼（已自动跳转到推荐页面）
            bot.auto_greeting_recommend_page(greeting_message, max_count)
        else:
            # 搜索模式打招呼
            bot.auto_greeting(keywords, greeting_message, max_count)
    finally:
        # 关闭浏览器
        bot.close()