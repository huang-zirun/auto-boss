"""
工具模块测试
"""
import pytest
from unittest.mock import Mock, patch
import time

from boss_helper.utils.wait import SmartWait, wait_for_condition
from boss_helper.utils.helpers import (
    random_sleep,
    format_duration,
    truncate_text,
)


class TestSmartWait:
    """智能等待测试"""
    
    def test_until_success(self):
        """测试条件满足"""
        counter = [0]
        
        def condition():
            counter[0] += 1
            return counter[0] >= 3
        
        wait = SmartWait(timeout=5, poll_interval=0.1)
        result = wait.until(condition)
        
        assert result is True
        assert counter[0] >= 3
    
    def test_until_timeout(self):
        """测试超时"""
        def condition():
            return False
        
        wait = SmartWait(timeout=0.5, poll_interval=0.1)
        
        with pytest.raises(TimeoutError):
            wait.until(condition)
    
    def test_until_not(self):
        """测试条件不满足"""
        counter = [0]
        
        def condition():
            counter[0] += 1
            return counter[0] < 3
        
        wait = SmartWait(timeout=5, poll_interval=0.1)
        result = wait.until_not(condition)
        
        assert result is True
    
    def test_with_retry_success(self):
        """测试重试成功"""
        counter = [0]
        
        def func():
            counter[0] += 1
            if counter[0] < 2:
                raise ValueError("临时错误")
            return "success"
        
        wait = SmartWait()
        result = wait.with_retry(func, max_attempts=3, retry_interval=0.1)
        
        assert result == "success"
        assert counter[0] == 2
    
    def test_with_retry_failure(self):
        """测试重试失败"""
        def func():
            raise ValueError("持续错误")
        
        wait = SmartWait()
        
        with pytest.raises(ValueError):
            wait.with_retry(func, max_attempts=2, retry_interval=0.1)


class TestWaitForCondition:
    """条件等待函数测试"""
    
    def test_immediate_success(self):
        """测试立即成功"""
        result = wait_for_condition(lambda: True, timeout=1)
        assert result is True
    
    def test_eventual_success(self):
        """测试最终成功"""
        counter = [0]
        
        def condition():
            counter[0] += 1
            return counter[0] >= 2
        
        result = wait_for_condition(condition, timeout=5, poll_interval=0.1)
        assert result is True


class TestRandomSleep:
    """随机等待测试"""
    
    def test_fixed_sleep(self):
        """测试固定等待"""
        start = time.time()
        random_sleep(0.1)
        elapsed = time.time() - start
        
        assert elapsed >= 0.1
        assert elapsed < 0.2
    
    def test_range_sleep(self):
        """测试范围等待"""
        start = time.time()
        random_sleep(0.1, 0.2)
        elapsed = time.time() - start
        
        assert elapsed >= 0.1
        assert elapsed < 0.3
    
    def test_max_less_than_min(self):
        """测试最大值小于最小值"""
        start = time.time()
        random_sleep(0.2, 0.1)
        elapsed = time.time() - start
        
        assert elapsed >= 0.2


class TestFormatDuration:
    """时长格式化测试"""
    
    def test_seconds(self):
        """测试秒"""
        result = format_duration(5.5)
        assert "5.5秒" == result
    
    def test_minutes(self):
        """测试分钟"""
        result = format_duration(125)
        assert "2分5秒" == result
    
    def test_hours(self):
        """测试小时"""
        result = format_duration(3665)
        assert "1小时1分" == result


class TestTruncateText:
    """文本截断测试"""
    
    def test_short_text(self):
        """测试短文本"""
        result = truncate_text("短文本", 50)
        assert result == "短文本"
    
    def test_long_text(self):
        """测试长文本"""
        result = truncate_text("这是一段很长的文本用于测试截断功能", 10)
        assert len(result) == 10
        assert result.endswith("...")
