# Boss直聘招聘助手脚本

## 功能说明

本脚本用于帮助招聘者在Boss直聘平台上高效联系候选人，支持以下功能：

- **推荐模式**：在推荐牛人页面自动向推荐的候选人打招呼，批量联系潜在候选人
- **搜索模式**：根据关键词搜索候选人，自动向符合条件的候选人打招呼

## 适用对象

本脚本专为**招聘者**设计，帮助招聘人员：
- 批量联系推荐的候选人
- 提高招聘效率
- 自动化重复性沟通工作

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

## 配置说明

打开 `config.py` 文件，修改以下配置：

### 基础配置
- `driver_path`：ChromeDriver路径，为空则使用PATH中的驱动
- `user_data_dir`：Chrome用户数据目录（当前未使用，保留供后续扩展）

### 登录与入口
- `login_url`：Boss直聘登录页面
- `recommend_page_url`：推荐牛人页面
- `wait_login_timeout`：等待登录检测的超时时间（秒）

### 运行模式
- `mode`：运行模式，可选值：
  - `"search"`：搜索候选人后打招呼
  - `"recommend"`：推荐牛人页打招呼（默认）

### 搜索模式配置（mode="search" 时生效）
- `keywords`：搜索关键词，如 "Python开发"
- `greeting_message`：打招呼消息
- `max_count`：最大打招呼数量

### 推荐模式配置（mode="recommend" 时生效）
- `greeting_message`：打招呼消息
- `max_count`：最多联系候选人数量
- `interval_min`：每次打招呼最小间隔（秒）
- `interval_max`：每次打招呼最大间隔（秒）
- `wait_card_list_seconds`：等待iframe内列表出现的超时（秒）
- `wait_modal_seconds`：点击打招呼后等待弹窗出现的超时（秒）

## 使用说明

1. 配置 `config.py` 文件中的参数

2. 运行脚本：
   ```bash
   python auto_greeting.py
   ```

3. 脚本会打开Chrome浏览器，进入Boss直聘网站，请在浏览器中登录您的招聘账号

4. 脚本会自动检测登录状态，登录成功后自动跳转到目标页面

5. 根据配置的模式自动执行打招呼操作

## 主要功能

### 自动登录检测
- 自动检测是否已登录（通过退出登录入口或Cookie）
- 登录成功后自动跳转到目标页面

### 推荐模式（推荐使用）
- 在推荐牛人页面自动向候选人打招呼
- 自动滚动加载更多候选人
- 智能识别打招呼按钮（排除已沟通、已打招呼等状态）
- 支持自定义消息或使用模板
- 随机间隔避免被检测，模拟人工操作

### 搜索模式
- 根据关键词搜索候选人
- 自动向符合条件的候选人打招呼
- 支持翻页操作

### 调试功能
- `debug_page_elements()` 方法可以打印页面元素信息
- 帮助定位元素选择器问题

## 注意事项

1. 请合理使用本脚本，避免过度频繁操作，以免被平台限制
2. 推荐使用随机间隔功能，模拟人工操作，提高账号安全性
3. 如果遇到元素定位失败的问题，可能是因为网站结构发生变化，需要更新XPath或CSS选择器
4. 建议先使用调试功能测试页面元素是否正确
5. 请遵守Boss直聘平台的使用规范，合理使用自动化工具

## 常见问题

1. **ChromeDriver版本不匹配**：请下载与Chrome浏览器版本对应的ChromeDriver
2. **元素定位失败**：网站结构可能发生变化，需要更新XPath或CSS选择器
3. **登录检测失败**：脚本会尝试多种方式检测登录状态，如果仍失败请检查网络连接
4. **iframe切换失败**：推荐模式需要切换到iframe，如果失败请确认页面结构未变化
5. **候选人列表为空**：请确认您的账号是否有推荐的候选人，或者检查筛选条件

## 代码示例

### 推荐模式（推荐使用）
```python
from auto_greeting import BossAutoGreeting

bot = BossAutoGreeting()
bot.login()
bot.auto_greeting_recommend_page(
    greeting_message="您好，我是XX公司的招聘负责人，看到您的简历很匹配我们的职位，期待与您沟通！",
    max_count=50,
    interval_min=2,
    interval_max=5
)
bot.close()
```

### 搜索模式
```python
from auto_greeting import BossAutoGreeting

bot = BossAutoGreeting()
bot.login()
bot.auto_greeting("Python开发", "您好，我是XX公司的招聘负责人，看到您的简历很匹配我们的职位，期待与您沟通！", 20)
bot.close()
```

### 调试页面元素
```python
from auto_greeting import BossAutoGreeting

bot = BossAutoGreeting()
bot.login()
bot.debug_page_elements()  # 打印页面元素信息
bot.close()
```

## 配置示例

```python
# 使用推荐模式（推荐）
mode = "recommend"
greeting_message = "您好，我是XX公司的招聘负责人，看到您的简历很匹配我们的职位，期待与您沟通！"
max_count = 50
interval_min = 2
interval_max = 5

# 使用搜索模式
mode = "search"
keywords = "Python开发"
greeting_message = "您好，我是XX公司的招聘负责人，看到您的简历很匹配我们的职位，期待与您沟通！"
max_count = 20
```

## 招聘场景建议

1. **打招呼消息建议**：
   - 简洁明了，突出职位亮点
   - 说明为什么选择联系该候选人
   - 提供明确的下一步行动指引

2. **使用频率建议**：
   - 建议设置合理的间隔时间（2-5秒）
   - 每日联系数量建议控制在合理范围内
   - 避免在短时间内大量操作

3. **最佳实践**：
   - 先筛选出真正匹配的候选人
   - 个性化打招呼消息，提高回复率
   - 及时跟进候选人的回复
