# Boss直聘自动打招呼脚本

## 功能说明

本脚本用于在Boss直聘网站上自动向职位发布者打招呼，支持自定义搜索关键词、打招呼消息和打招呼数量。

## 环境要求

- Python 3.7+
- Selenium 4.0+
- Chrome浏览器
- ChromeDriver（与Chrome浏览器版本匹配）

## 安装步骤

1. 安装Python（如果未安装）
2. 安装Selenium库：
   ```bash
   pip install selenium
   ```
3. 下载ChromeDriver：
   - 查看Chrome浏览器版本：在Chrome地址栏输入 `chrome://version/`
   - 下载对应版本的ChromeDriver：https://chromedriver.chromium.org/downloads
   - 将ChromeDriver.exe文件放在Python安装目录或系统PATH中

## 使用说明

1. 打开 `auto_greeting.py` 文件，修改以下配置：
   - `user-data-dir`：改为您的Chrome用户数据目录
   - `keywords`：搜索关键词
   - `greeting_message`：打招呼消息
   - `max_count`：最大打招呼数量

2. 运行脚本：
   ```bash
   python auto_greeting.py
   ```

3. 脚本会打开Chrome浏览器，进入Boss直聘网站，请在浏览器中登录您的账号，登录完成后按Enter键继续。

4. 脚本会自动搜索职位并发送打招呼消息。

## 注意事项

1. 请合理使用本脚本，避免过度频繁操作，以免被网站限制。
2. 脚本使用您的Chrome用户数据，保持登录状态，无需每次手动登录。
3. 如果遇到元素定位失败的问题，可能是因为网站结构发生变化，需要更新XPath或CSS选择器。

## 常见问题

1. **ChromeDriver版本不匹配**：请下载与Chrome浏览器版本对应的ChromeDriver。
2. **元素定位失败**：网站结构可能发生变化，需要更新XPath或CSS选择器。
3. **登录失败**：请确保您的Chrome用户数据目录正确，并且已经在浏览器中登录了Boss直聘账号。

## 配置示例

```python
# 初始化
bot = BossAutoGreeting()

# 登录
bot.login()

# 自动打招呼
keywords = "Python开发"
greeting_message = "您好，我对贵公司的职位很感兴趣，期待能有机会与您沟通！"
max_count = 20

bot.auto_greeting(keywords, greeting_message, max_count)

# 关闭浏览器
bot.close()
```