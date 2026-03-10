"""
测试配置
"""
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def mock_settings():
    """模拟配置"""
    from boss_helper.config.settings import (
        Settings, BrowserSettings, UrlSettings,
        TimingSettings, FilterSettings, JobSettings, ResumeSettings
    )
    
    return Settings(
        browser=BrowserSettings(
            driver_path="",
            user_data_dir="",
            debug_port=9222
        ),
        urls=UrlSettings(),
        timing=TimingSettings(),
        filters=FilterSettings(),
        jobs=JobSettings(),
        resume=ResumeSettings()
    )


@pytest.fixture
def selector_provider():
    """选择器提供者"""
    from boss_helper.config.selectors import SelectorProvider
    return SelectorProvider()
