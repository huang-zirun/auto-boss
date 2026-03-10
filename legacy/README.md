# Legacy Code (旧版代码)

此目录包含重构前的原始代码，保留用于参考和向后兼容。

## 文件说明

| 文件 | 说明 |
|------|------|
| `auto_greeting.py` | 自动打招呼主程序（旧版） |
| `auto_resume_collect.py` | 自动收集简历程序（旧版） |
| `base_bot.py` | 抽象基类（旧版） |
| `browser_manager.py` | 浏览器管理模块（旧版） |
| `config.py` | 配置文件（旧版） |
| `page_objects.py` | 页面对象封装（旧版） |
| `selenium_utils.py` | Selenium 统一导入模块（旧版） |

## 新版代码

重构后的新代码位于 `src/boss_helper/` 目录，建议使用新版本：

```python
# 新版使用方式
from boss_helper.services import GreetingService, ResumeService

# 打招呼服务
with GreetingService() as service:
    service.login()
    service.auto_greeting_all_jobs()

# 简历收集服务
with ResumeService() as service:
    service.login()
    service.run_all_chats()
```

## 旧版使用方式（仍可使用）

```bash
cd legacy
python auto_greeting.py
python auto_resume_collect.py
```

> **注意**: 旧版代码不再维护，建议尽快迁移到新版本。
