"""
自定义异常体系

提供清晰的异常层次结构，便于错误处理和调试。
"""
from typing import Optional, Any


class BossHelperError(Exception):
    """
    基础异常类
    
    所有 boss_helper 相关异常的基类。
    """
    
    def __init__(self, message: str, details: Optional[dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | 详情: {self.details}"
        return self.message


class BrowserError(BossHelperError):
    """
    浏览器相关错误
    
    当浏览器启动、连接或操作失败时抛出。
    """
    pass


class LoginError(BossHelperError):
    """
    登录相关错误
    
    当登录过程出现问题时抛出。
    """
    pass


class LoginTimeoutError(LoginError):
    """
    登录超时错误
    
    当用户在指定时间内未完成登录时抛出。
    """
    
    def __init__(self, timeout: int, message: Optional[str] = None):
        self.timeout = timeout
        msg = message or f"登录超时，等待时间: {timeout}秒"
        super().__init__(msg, {"timeout": timeout})


class ElementNotFoundError(BossHelperError):
    """
    元素未找到错误
    
    当无法在页面上找到指定元素时抛出。
    """
    
    def __init__(
        self, 
        selector: str, 
        selector_type: str = "css",
        message: Optional[str] = None
    ):
        self.selector = selector
        self.selector_type = selector_type
        msg = message or f"未找到元素: [{selector_type}] {selector}"
        super().__init__(msg, {"selector": selector, "type": selector_type})


class ElementNotInteractableError(BossHelperError):
    """
    元素不可交互错误
    
    当元素存在但无法进行交互（点击、输入等）时抛出。
    """
    
    def __init__(
        self, 
        selector: str, 
        action: str = "interact",
        message: Optional[str] = None
    ):
        self.selector = selector
        self.action = action
        msg = message or f"元素不可执行操作 '{action}': {selector}"
        super().__init__(msg, {"selector": selector, "action": action})


class RiskControlDetectedError(BossHelperError):
    """
    风控检测错误
    
    当检测到平台风控机制触发时抛出。
    """
    
    def __init__(self, message: str = "检测到风控验证，请手动完成验证"):
        super().__init__(message, {"requires_manual_action": True})


class ConfigurationError(BossHelperError):
    """
    配置错误
    
    当配置项无效或缺失时抛出。
    """
    
    def __init__(self, config_key: str, message: Optional[str] = None):
        self.config_key = config_key
        msg = message or f"配置项无效或缺失: {config_key}"
        super().__init__(msg, {"config_key": config_key})


class SelectorNotFoundError(BossHelperError):
    """
    选择器配置未找到错误
    
    当选择器配置文件中不存在指定选择器时抛出。
    """
    
    def __init__(self, page: str, element: str):
        self.page = page
        self.element = element
        msg = f"选择器配置未找到: {page}.{element}"
        super().__init__(msg, {"page": page, "element": element})
