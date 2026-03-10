"""
配置系统 - 基于 Pydantic 的类型安全配置

支持：
- 环境变量覆盖
- 配置验证
- 敏感信息保护
"""
import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class BrowserSettings(BaseSettings):
    """
    浏览器配置
    
    支持通过环境变量覆盖：BOSS_BROWSER_*
    """
    model_config = SettingsConfigDict(
        env_prefix="BOSS_BROWSER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    driver_path: str = Field(
        default="",
        description="ChromeDriver路径，为空则使用系统PATH中的驱动"
    )
    user_data_dir: str = Field(
        default="",
        description="Chrome用户数据目录",
        exclude=True  # 敏感信息，不序列化
    )
    debug_port: int = Field(
        default=9222,
        ge=1,
        le=65535,
        description="Chrome远程调试端口"
    )
    headless: bool = Field(
        default=False,
        description="是否使用无头模式"
    )
    
    @field_validator("user_data_dir", mode="before")
    @classmethod
    def validate_user_data_dir(cls, v: str) -> str:
        if v and not Path(v).exists():
            pass
        return v


class UrlSettings(BaseSettings):
    """
    URL配置
    
    支持通过环境变量覆盖：BOSS_URL_*
    """
    model_config = SettingsConfigDict(
        env_prefix="BOSS_URL_",
        env_file=".env",
        extra="ignore",
    )
    
    login_url: str = Field(
        default="https://www.zhipin.com/",
        description="BOSS直聘登录页面"
    )
    recommend_page_url: str = Field(
        default="https://www.zhipin.com/web/chat/recommend",
        description="推荐牛人页面"
    )
    chat_page_url: str = Field(
        default="https://www.zhipin.com/web/chat/index",
        description="聊天页面"
    )


class TimingSettings(BaseSettings):
    """
    时间等待配置
    
    支持通过环境变量覆盖：BOSS_TIMING_*
    """
    model_config = SettingsConfigDict(
        env_prefix="BOSS_TIMING_",
        env_file=".env",
        extra="ignore",
    )
    
    wait_login_timeout: int = Field(
        default=300,
        ge=30,
        le=3600,
        description="等待登录超时时间（秒）"
    )
    login_page_wait_seconds: float = Field(
        default=3.0,
        ge=0,
        le=60,
        description="打开登录页后等待稳定时间（秒）"
    )
    login_poll_interval_seconds: float = Field(
        default=2.0,
        ge=0.5,
        le=10,
        description="登录状态检测轮询间隔（秒）"
    )
    wait_card_list_seconds: int = Field(
        default=15,
        ge=1,
        le=60,
        description="等待候选人卡片列表加载时间（秒）"
    )
    wait_modal_seconds: int = Field(
        default=5,
        ge=1,
        le=30,
        description="等待弹窗加载时间（秒）"
    )
    interval_min: float = Field(
        default=0.1,
        ge=0,
        le=60,
        description="操作间隔最小时间（秒）"
    )
    interval_max: float = Field(
        default=0.6,
        ge=0,
        le=120,
        description="操作间隔最大时间（秒）"
    )
    
    @model_validator(mode="after")
    def validate_intervals(self):
        if self.interval_max < self.interval_min:
            raise ValueError("interval_max 必须大于等于 interval_min")
        return self


class FilterSettings(BaseSettings):
    """
    候选人筛选配置
    
    支持通过环境变量覆盖：BOSS_FILTER_*
    """
    model_config = SettingsConfigDict(
        env_prefix="BOSS_FILTER_",
        env_file=".env",
        extra="ignore",
    )
    
    use_vip_filters: bool = Field(
        default=True,
        description="是否启用VIP筛选功能"
    )
    filter_school: str = Field(
        default="双一流院校",
        description="院校筛选条件"
    )
    filter_no_resume_exchange: str = Field(
        default="近一个月没有",
        description="简历交换状态筛选"
    )
    filter_education: List[str] = Field(
        default=["本科", "硕士", "博士"],
        description="学历筛选条件"
    )


class JobSettings(BaseSettings):
    """
    职位配置
    
    支持通过环境变量覆盖：BOSS_JOB_*
    """
    model_config = SettingsConfigDict(
        env_prefix="BOSS_JOB_",
        env_file=".env",
        extra="ignore",
    )
    
    job_positions: List[str] = Field(
        default_factory=list,
        description="目标职位列表"
    )
    max_count: int = Field(
        default=1000000,
        ge=1,
        description="每个岗位最多联系候选人数量"
    )


class ResumeSettings(BaseSettings):
    """
    简历处理配置
    
    支持通过环境变量覆盖：BOSS_RESUME_*
    """
    model_config = SettingsConfigDict(
        env_prefix="BOSS_RESUME_",
        env_file=".env",
        extra="ignore",
    )
    
    resume_load_timeout: int = Field(
        default=60,
        ge=10,
        le=300,
        description="简历加载超时时间（秒）"
    )
    resume_chat_interval: float = Field(
        default=1.5,
        ge=0,
        le=60,
        description="简历聊天间隔（秒）"
    )
    resume_chat_interval_min: float = Field(
        default=2.0,
        ge=0,
        le=60,
        description="会话间最小间隔（秒）"
    )
    resume_chat_interval_max: float = Field(
        default=5.0,
        ge=0,
        le=120,
        description="会话间最大间隔（秒）"
    )
    resume_download_interval_min: float = Field(
        default=15.0,
        ge=0,
        le=300,
        description="下载简历后最小间隔（秒）"
    )
    resume_download_interval_max: float = Field(
        default=45.0,
        ge=0,
        le=600,
        description="下载简历后最大间隔（秒）"
    )
    resume_wait_after_agree_min: float = Field(
        default=3.0,
        ge=0,
        le=60,
        description="点击同意后最小等待（秒）"
    )
    resume_wait_after_agree_max: float = Field(
        default=7.0,
        ge=0,
        le=120,
        description="点击同意后最大等待（秒）"
    )
    resume_wait_after_preview_min: float = Field(
        default=2.0,
        ge=0,
        le=60,
        description="点击预览后最小等待（秒）"
    )
    resume_wait_after_preview_max: float = Field(
        default=5.0,
        ge=0,
        le=120,
        description="点击预览后最大等待（秒）"
    )
    resume_max_collect: int = Field(
        default=0,
        ge=0,
        description="简历最大收集数量，0表示无限制"
    )
    
    @model_validator(mode="after")
    def validate_intervals(self):
        if self.resume_chat_interval_max < self.resume_chat_interval_min:
            raise ValueError("resume_chat_interval_max 必须大于等于 resume_chat_interval_min")
        if self.resume_download_interval_max < self.resume_download_interval_min:
            raise ValueError("resume_download_interval_max 必须大于等于 resume_download_interval_min")
        if self.resume_wait_after_agree_max < self.resume_wait_after_agree_min:
            raise ValueError("resume_wait_after_agree_max 必须大于等于 resume_wait_after_agree_min")
        if self.resume_wait_after_preview_max < self.resume_wait_after_preview_min:
            raise ValueError("resume_wait_after_preview_max 必须大于等于 resume_wait_after_preview_min")
        return self


class Settings(BaseSettings):
    """
    主配置类 - 聚合所有配置项
    
    支持通过环境变量覆盖：BOSS_*
    """
    model_config = SettingsConfigDict(
        env_prefix="BOSS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    browser: BrowserSettings = Field(default_factory=BrowserSettings)
    urls: UrlSettings = Field(default_factory=UrlSettings)
    timing: TimingSettings = Field(default_factory=TimingSettings)
    filters: FilterSettings = Field(default_factory=FilterSettings)
    jobs: JobSettings = Field(default_factory=JobSettings)
    resume: ResumeSettings = Field(default_factory=ResumeSettings)
    
    debug: bool = Field(
        default=False,
        description="调试模式"
    )
    log_level: str = Field(
        default="INFO",
        description="日志级别"
    )


@lru_cache()
def get_settings() -> Settings:
    """
    获取配置实例（单例模式）
    
    使用 lru_cache 确保配置只加载一次。
    """
    return Settings()


def clear_settings_cache() -> None:
    """
    清除配置缓存
    
    用于测试或需要重新加载配置的场景。
    """
    get_settings.cache_clear()
