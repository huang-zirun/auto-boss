"""
配置模块测试
"""
import pytest
from boss_helper.config.settings import (
    Settings,
    BrowserSettings,
    UrlSettings,
    TimingSettings,
    FilterSettings,
    JobSettings,
    ResumeSettings,
    get_settings,
    clear_settings_cache,
)


class TestBrowserSettings:
    """浏览器配置测试"""
    
    def test_default_values(self):
        """测试默认值"""
        settings = BrowserSettings()
        assert settings.driver_path == ""
        assert settings.debug_port == 9222
        assert settings.headless is False
    
    def test_port_validation(self):
        """测试端口验证"""
        settings = BrowserSettings(debug_port=8080)
        assert settings.debug_port == 8080
        
        with pytest.raises(ValueError):
            BrowserSettings(debug_port=0)
        
        with pytest.raises(ValueError):
            BrowserSettings(debug_port=70000)


class TestTimingSettings:
    """时间配置测试"""
    
    def test_default_values(self):
        """测试默认值"""
        settings = TimingSettings()
        assert settings.wait_login_timeout == 300
        assert settings.interval_min == 0.1
        assert settings.interval_max == 0.6
    
    def test_interval_validation(self):
        """测试间隔验证"""
        with pytest.raises(ValueError):
            TimingSettings(interval_min=5, interval_max=1)


class TestResumeSettings:
    """简历配置测试"""
    
    def test_default_values(self):
        """测试默认值"""
        settings = ResumeSettings()
        assert settings.resume_load_timeout == 60
        assert settings.resume_max_collect == 0
    
    def test_interval_validation(self):
        """测试间隔验证"""
        with pytest.raises(ValueError):
            ResumeSettings(
                resume_chat_interval_min=10,
                resume_chat_interval_max=5
            )


class TestSettings:
    """主配置测试"""
    
    def test_aggregation(self):
        """测试配置聚合"""
        settings = Settings()
        assert hasattr(settings, 'browser')
        assert hasattr(settings, 'urls')
        assert hasattr(settings, 'timing')
        assert hasattr(settings, 'filters')
        assert hasattr(settings, 'jobs')
        assert hasattr(settings, 'resume')
    
    def test_singleton(self):
        """测试单例模式"""
        clear_settings_cache()
        
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2
        
        clear_settings_cache()


class TestSettingsWithEnv:
    """环境变量配置测试"""
    
    def test_env_prefix(self, monkeypatch):
        """测试环境变量前缀"""
        monkeypatch.setenv("BOSS_BROWSER_DEBUG_PORT", "9999")
        
        clear_settings_cache()
        settings = get_settings()
        
        assert settings.browser.debug_port == 9999
        
        clear_settings_cache()
        monkeypatch.delenv("BOSS_BROWSER_DEBUG_PORT")
