# Boss直聘招聘助手

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

一款基于 Selenium 的 Boss直聘自动化招聘助手，支持自动打招呼、简历收集等功能。

## 功能特性

- **自动打招呼**：在推荐牛人页面自动向候选人打招呼，批量联系潜在候选人
- **多岗位切换**：支持遍历所有招聘岗位，自动在每个岗位下执行打招呼操作
- **智能筛选**：支持按学历、学校、简历交换状态等条件筛选候选人
- **上限检测**：自动检测每日主动沟通次数上限，到达上限后自动切换下一个岗位
- **简历收集**：自动遍历沟通列表，检测简历交换申请并下载附件简历
- **浏览器复用**：支持通过 debug_port 复用已打开的浏览器，保持登录状态

## 环境要求

- Python 3.8+
- Chrome 浏览器
- ChromeDriver（与 Chrome 浏览器版本匹配）

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填写您的配置：

```env
# 浏览器配置
BOSS_BROWSER_DEBUG_PORT=9222
BOSS_BROWSER_USER_DATA_DIR=

# 筛选配置
BOSS_FILTER_USE_VIP_FILTERS=true
BOSS_FILTER_FILTER_SCHOOL=双一流院校
```

### 3. 运行服务

**打招呼服务：**

```python
from boss_helper.services import GreetingService

with GreetingService() as service:
    service.login()
    service.auto_greeting_all_jobs()
```

**简历收集服务：**

```python
from boss_helper.services import ResumeService

with ResumeService() as service:
    service.login()
    service.run_all_chats()
```

或使用命令行：

```bash
python -m boss_helper.services.greeting
python -m boss_helper.services.resume
```

## 项目结构

```
auto-boos/
├── src/
│   └── boss_helper/
│       ├── config/           # 配置模块
│       │   ├── settings.py   # Pydantic 配置
│       │   ├── selectors.py  # 选择器管理
│       │   └── selectors.yaml # 选择器配置
│       ├── core/             # 核心模块
│       │   ├── browser.py    # 浏览器管理
│       │   └── exceptions.py # 自定义异常
│       ├── pages/            # 页面对象
│       │   ├── base.py       # 基类
│       │   ├── recommend.py  # 推荐页面
│       │   └── chat.py       # 聊天页面
│       ├── services/         # 业务服务
│       │   ├── greeting.py   # 打招呼服务
│       │   └── resume.py     # 简历收集服务
│       └── utils/            # 工具模块
│           ├── wait.py       # 智能等待
│           └── helpers.py    # 辅助函数
├── tests/                    # 单元测试
├── legacy/                   # 旧版代码（已归档）
├── .env.example              # 环境变量模板
├── pyproject.toml            # 项目配置
└── requirements.txt          # 依赖清单
```

## 配置说明

### 环境变量配置

所有配置都支持通过环境变量覆盖，格式为 `BOSS_<模块>_<配置名>`：

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `BOSS_BROWSER_DEBUG_PORT` | Chrome 调试端口 | 9222 |
| `BOSS_BROWSER_USER_DATA_DIR` | Chrome 用户数据目录 | - |
| `BOSS_TIMING_INTERVAL_MIN` | 操作最小间隔（秒） | 0.1 |
| `BOSS_TIMING_INTERVAL_MAX` | 操作最大间隔（秒） | 0.6 |
| `BOSS_FILTER_USE_VIP_FILTERS` | 是否启用 VIP 筛选 | true |
| `BOSS_JOB_MAX_COUNT` | 每岗位最大联系数 | 1000000 |

### 选择器配置

选择器配置位于 `src/boss_helper/config/selectors.yaml`，当网站结构变化时只需更新此文件：

```yaml
recommend_page:
  iframe:
    selector: "iframe[name='recommendFrame']"
    type: css
  greet_button:
    selector: ".//button[contains(text(), '打招呼')]"
    type: xpath
```

## 开发指南

### 运行测试

```bash
pytest tests/ -v
```

### 代码检查

```bash
ruff check src/
mypy src/
```

## 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                      Services Layer                      │
│  ┌─────────────────────┐  ┌─────────────────────────┐   │
│  │   GreetingService   │  │     ResumeService       │   │
│  └─────────────────────┘  └─────────────────────────┘   │
├─────────────────────────────────────────────────────────┤
│                       Pages Layer                        │
│  ┌─────────────────────┐  ┌─────────────────────────┐   │
│  │   RecommendPage     │  │      ChatPage           │   │
│  └─────────────────────┘  └─────────────────────────┘   │
├─────────────────────────────────────────────────────────┤
│                       Core Layer                         │
│  ┌─────────────────────┐  ┌─────────────────────────┐   │
│  │   BrowserManager    │  │     Exceptions          │   │
│  └─────────────────────┘  └─────────────────────────┘   │
├─────────────────────────────────────────────────────────┤
│                      Config Layer                        │
│  ┌─────────────────────┐  ┌─────────────────────────┐   │
│  │     Settings        │  │   SelectorProvider      │   │
│  └─────────────────────┘  └─────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## 注意事项

1. 请合理使用本脚本，避免过度频繁操作，以免被平台限制
2. 推荐使用随机间隔功能，模拟人工操作，提高账号安全性
3. 如果遇到元素定位失败，可能是网站结构变化，需更新 `selectors.yaml`
4. 请遵守 Boss直聘平台的使用规范，合理使用自动化工具

## 许可证

[MIT License](LICENSE)

## 更新日志

### v2.0.0 (2024)

- 重构项目架构，采用分层设计
- 配置系统迁移到 Pydantic，支持环境变量
- 选择器外部化到 YAML 配置文件
- 添加完整的异常层次结构
- 实现智能等待策略
- 添加单元测试覆盖
- 旧版代码归档到 `legacy` 目录
