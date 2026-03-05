# Boss直聘招聘助手脚本

## 功能说明

本脚本用于帮助招聘者在Boss直聘平台上高效联系候选人，支持以下功能：

- **推荐模式**：在推荐牛人页面自动向推荐的候选人打招呼，批量联系潜在候选人
- **多岗位自动切换**：支持遍历所有招聘岗位，自动在每个岗位下执行打招呼操作
- **智能筛选**：支持按学历、学校、简历交换状态等条件筛选候选人
- **付费上限检测**：自动检测每日主动沟通次数上限，到达上限后自动切换下一个岗位
- **简历收集**：自动遍历沟通列表，检测简历交换申请并下载附件简历

## 适用对象

本脚本专为**招聘者**设计，帮助招聘人员：
- 批量联系推荐的候选人
- 自动收集候选人发送的附件简历
- 提高招聘效率
- 自动化重复性沟通工作
- 多岗位批量处理

## 环境要求

- Python 3.7+
- Selenium 4.0+
- Chrome浏览器
- ChromeDriver（与Chrome浏览器版本匹配）

## 安装步骤

1. 安装Python（如果未安装）
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 下载ChromeDriver：
   - 查看Chrome浏览器版本：在Chrome地址栏输入 `chrome://version/`
   - 下载对应版本的ChromeDriver：https://chromedriver.chromium.org/downloads
   - 将ChromeDriver.exe文件放在Python安装目录或系统PATH中

## 配置说明

打开 `config.py` 文件，修改以下配置：

### 浏览器配置 (BrowserConfig)
- `driver_path`：ChromeDriver路径，为空则使用PATH中的驱动
- `user_data_dir`：Chrome用户数据目录，用于保持登录状态
- `debug_port`：远程调试端口（默认9222），用于复用已打开的浏览器

### URL配置 (UrlConfig)
- `login_url`：Boss直聘登录页面
- `recommend_page_url`：推荐牛人页面
- `chat_page_url`：沟通列表页面

### 时间配置 (TimingConfig)
- `wait_login_timeout`：等待登录检测的超时时间（秒）
- `wait_card_list_seconds`：等待卡片列表加载时间
- `wait_modal_seconds`：等待弹窗加载时间
- `interval_min`：每次打招呼最小间隔（秒）
- `interval_max`：每次打招呼最大间隔（秒）

### 筛选配置 (FilterConfig)
- `use_vip_filters`：是否使用VIP筛选器
- `filter_school`：学校筛选条件（如"双一流院校"）
- `filter_no_resume_exchange`：简历未交换筛选条件（如"近一个月没有"）
- `filter_education`：学历筛选条件（如["本科", "硕士", "博士"]）

### 职位配置 (JobConfig)
- `job_positions`：指定处理的职位列表，为空则处理所有职位
- `max_count`：每个岗位最多联系候选人数量

### 简历配置 (ResumeConfig)
- `resume_load_timeout`：等待附件简历加载完成的超时时间（秒）
- `resume_chat_interval`：切换会话间隔（秒）
- `resume_max_collect`：最多处理多少个有简历申请的会话（0表示不限制）

## 使用说明

### 自动打招呼

1. 配置 `config.py` 文件中的参数

2. 运行脚本：
   ```bash
   python auto_greeting.py
   ```

3. 脚本会打开Chrome浏览器，进入Boss直聘网站，请在浏览器中登录您的招聘账号

4. 脚本会自动检测登录状态，登录成功后自动跳转到推荐牛人页面

5. 自动执行打招呼操作：
   - 如果配置了 `job_positions`，则只处理指定岗位
   - 如果 `job_positions` 为空，则自动获取所有岗位并依次处理
   - 每个岗位处理完成后会自动切换到下一个岗位

### 自动收集简历

1. 配置 `config.py` 文件中的简历相关参数

2. 运行脚本：
   ```bash
   python auto_resume_collect.py
   ```

3. 脚本会打开Chrome浏览器，登录后跳转到沟通列表页

4. 自动遍历所有会话，检测是否有简历交换申请：
   - 发现有「对方想发送附件简历」的申请时，自动点击同意
   - 自动点击预览附件简历
   - 自动点击下载按钮

## 项目结构

```
auto-boos/
├── config.py              # 配置文件（dataclass分组配置）
├── browser_manager.py     # 浏览器管理模块
├── selenium_utils.py      # Selenium统一导入模块
├── base_bot.py            # 抽象基类，封装公共逻辑
├── page_objects.py        # 页面对象封装
├── auto_greeting.py       # 自动打招呼主程序
├── auto_resume_collect.py # 自动收集简历程序
├── requirements.txt       # 依赖清单
└── README.md              # 项目说明文档
```

### 模块依赖关系

```
                    config.py
                        ↑
          ┌─────────────┼─────────────┐
          │             │             │
    auto_greeting.py  auto_resume_collect.py
          │             │
          └──────┬──────┘
                 ↓
            base_bot.py (抽象基类)
                 ↓
          page_objects.py
                 ↓
          browser_manager.py
                 ↓
          selenium_utils.py
```

## 主要功能

### 自动登录检测
- 自动检测是否已登录（通过退出登录入口或Cookie）
- 登录成功后自动跳转到目标页面
- 支持复用已打开的浏览器窗口（通过debug_port）

### 推荐模式（推荐使用）
- 在推荐牛人页面自动向候选人打招呼
- 自动滚动加载更多候选人
- 智能识别打招呼按钮（排除已沟通、已打招呼等状态）
- 随机间隔避免被检测，模拟人工操作

### 多岗位自动切换
- 自动获取所有招聘岗位列表
- 依次在每个岗位下执行打招呼操作
- 支持指定特定岗位列表进行处理

### 智能筛选
- 支持按学历筛选（本科、硕士、博士等）
- 支持按学校类型筛选（双一流院校等）
- 支持按简历交换状态筛选
- 自动应用筛选条件后执行打招呼

### 付费上限检测
- 自动检测每日主动沟通次数是否达到上限
- 达到上限后自动关闭弹窗并切换到下一个岗位
- 避免脚本卡在上限提示页面

### 简历自动收集
- 自动遍历沟通列表中的所有会话
- 检测候选人发送的附件简历申请
- 自动同意、预览并下载附件简历

### 浏览器复用
- 支持通过debug_port复用已打开的浏览器
- 不关闭浏览器窗口时，下次运行可直接连接
- 保持登录状态，无需重复登录

## 注意事项

1. 请合理使用本脚本，避免过度频繁操作，以免被平台限制
2. 推荐使用随机间隔功能，模拟人工操作，提高账号安全性
3. 如果遇到元素定位失败的问题，可能是因为网站结构发生变化，需要更新XPath或CSS选择器
4. 建议先使用调试功能测试页面元素是否正确
5. 请遵守Boss直聘平台的使用规范，合理使用自动化工具
6. 配置 `user_data_dir` 时，请确保该目录没有被其他Chrome进程占用

## 常见问题

1. **ChromeDriver版本不匹配**：请下载与Chrome浏览器版本对应的ChromeDriver
2. **元素定位失败**：网站结构可能发生变化，需要更新XPath或CSS选择器
3. **登录检测失败**：脚本会尝试多种方式检测登录状态，如果仍失败请检查网络连接
4. **iframe切换失败**：推荐模式需要切换到iframe，如果失败请确认页面结构未变化
5. **候选人列表为空**：请确认您的账号是否有推荐的候选人，或者检查筛选条件
6. **用户数据目录被占用**：请先关闭占用该目录的Chrome窗口，或更换其他用户数据目录
7. **付费上限弹窗**：脚本会自动处理，如果仍卡住请手动关闭弹窗
