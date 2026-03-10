"""
异常模块测试
"""
import pytest
from boss_helper.core.exceptions import (
    BossHelperError,
    BrowserError,
    LoginTimeoutError,
    ElementNotFoundError,
    RiskControlDetectedError,
    ConfigurationError,
    SelectorNotFoundError,
)


class TestBossHelperError:
    """基础异常测试"""
    
    def test_message(self):
        """测试消息"""
        error = BossHelperError("测试错误")
        assert str(error) == "测试错误"
        assert error.message == "测试错误"
    
    def test_details(self):
        """测试详情"""
        error = BossHelperError("测试错误", {"key": "value"})
        assert "key" in str(error)
        assert error.details == {"key": "value"}


class TestLoginTimeoutError:
    """登录超时异常测试"""
    
    def test_default_message(self):
        """测试默认消息"""
        error = LoginTimeoutError(300)
        assert "300" in str(error)
        assert error.timeout == 300
    
    def test_custom_message(self):
        """测试自定义消息"""
        error = LoginTimeoutError(60, "自定义消息")
        assert "自定义消息" in str(error)


class TestElementNotFoundError:
    """元素未找到异常测试"""
    
    def test_css_selector(self):
        """测试 CSS 选择器"""
        error = ElementNotFoundError(".test-class", "css")
        assert ".test-class" in str(error)
        assert error.selector_type == "css"
    
    def test_xpath_selector(self):
        """测试 XPath 选择器"""
        error = ElementNotFoundError("//div[@id='test']", "xpath")
        assert "//div[@id='test']" in str(error)
        assert error.selector_type == "xpath"


class TestRiskControlDetectedError:
    """风控检测异常测试"""
    
    def test_default_message(self):
        """测试默认消息"""
        error = RiskControlDetectedError()
        assert "风控" in str(error)
        assert error.details.get("requires_manual_action") is True


class TestConfigurationError:
    """配置异常测试"""
    
    def test_config_key(self):
        """测试配置键"""
        error = ConfigurationError("test_key")
        assert "test_key" in str(error)
        assert error.config_key == "test_key"


class TestSelectorNotFoundError:
    """选择器未找到异常测试"""
    
    def test_page_element(self):
        """测试页面元素"""
        error = SelectorNotFoundError("recommend_page", "greet_button")
        assert "recommend_page" in str(error)
        assert "greet_button" in str(error)
        assert error.page == "recommend_page"
        assert error.element == "greet_button"
