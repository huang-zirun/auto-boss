"""
选择器模块测试
"""
import pytest
from boss_helper.config.selectors import (
    SelectorItem,
    SelectorProvider,
    SelectorNotFoundError,
)


class TestSelectorItem:
    """选择器项测试"""
    
    def test_css_selector(self):
        """测试 CSS 选择器"""
        item = SelectorItem(".test-class", "css", "测试描述")
        assert item.selector == ".test-class"
        assert item.selector_type == "css"
        assert item.description == "测试描述"
    
    def test_xpath_selector(self):
        """测试 XPath 选择器"""
        item = SelectorItem("//div[@id='test']", "xpath")
        assert item.selector == "//div[@id='test']"
        assert item.selector_type == "xpath"
    
    def test_by_property(self):
        """测试 By 属性"""
        from selenium.webdriver.common.by import By
        
        css_item = SelectorItem(".test", "css")
        assert css_item.by == By.CSS_SELECTOR
        
        xpath_item = SelectorItem("//div", "xpath")
        assert xpath_item.by == By.XPATH
    
    def test_repr(self):
        """测试字符串表示"""
        item = SelectorItem(".test", "css")
        assert "css" in repr(item)
        assert ".test" in repr(item)


class TestSelectorProvider:
    """选择器提供者测试"""
    
    def test_get_simple_selector(self, selector_provider):
        """测试获取简单选择器"""
        item = selector_provider.get("recommend_page", "iframe")
        assert isinstance(item, SelectorItem)
        assert "iframe" in item.selector.lower()
    
    def test_get_nested_selector(self, selector_provider):
        """测试获取嵌套选择器"""
        item = selector_provider.get("recommend_page", "filter.panel")
        assert isinstance(item, SelectorItem)
    
    def test_get_list_selectors(self, selector_provider):
        """测试获取选择器列表"""
        items = selector_provider.get("recommend_page", "send_button")
        assert isinstance(items, list)
        assert len(items) > 0
        assert all(isinstance(i, SelectorItem) for i in items)
    
    def test_selector_not_found(self, selector_provider):
        """测试选择器未找到"""
        with pytest.raises(SelectorNotFoundError):
            selector_provider.get("nonexistent_page", "nonexistent_element")
    
    def test_get_with_default(self, selector_provider):
        """测试带默认值获取"""
        item = selector_provider.get(
            "nonexistent_page",
            "nonexistent_element",
            default=".default-selector"
        )
        assert isinstance(item, SelectorItem)
        assert item.selector == ".default-selector"
    
    def test_get_text(self, selector_provider):
        """测试获取文本"""
        text = selector_provider.get_text("common", "loading_text")
        assert text is not None
        assert "加载" in text
    
    def test_get_texts(self, selector_provider):
        """测试获取文本列表"""
        texts = selector_provider.get_texts("common", "risk_control_texts")
        assert isinstance(texts, list)
        assert len(texts) > 0
