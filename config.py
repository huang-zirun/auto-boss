from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class BrowserConfig:
    """浏览器相关配置"""
    driver_path: str = ""  # ChromeDriver路径，为空则使用系统PATH中的驱动
    user_data_dir: str = r"C:\Users\Admin\AppData\Local\Google\Chrome\User Data\Profile 2"  # Chrome用户数据目录
    debug_port: int = 9222  # Chrome远程调试端口


@dataclass
class UrlConfig:
    """URL地址配置"""
    login_url: str = "https://www.zhipin.com/"  # BOSS直聘登录页面
    recommend_page_url: str = "https://www.zhipin.com/web/chat/recommend"  # 推荐牛人页面
    chat_page_url: str = "https://www.zhipin.com/web/chat/index"  # 聊天页面


@dataclass
class TimingConfig:
    """时间等待相关配置"""
    wait_login_timeout: int = 300  # 等待登录超时时间（秒）
    wait_card_list_seconds: int = 15  # 等待候选人卡片列表加载时间（秒）
    wait_modal_seconds: int = 5  # 等待弹窗加载时间（秒）
    interval_min: float = 0.1  # 操作间隔最小时间（秒）
    interval_max: float = 0.6  # 操作间隔最大时间（秒）


@dataclass
class FilterConfig:
    """候选人筛选条件配置"""
    use_vip_filters: bool = True  # 是否启用VIP筛选功能
    filter_school: str = "双一流院校"  # 院校筛选条件
    filter_no_resume_exchange: str = "近一个月没有"  # 简历交换状态筛选
    filter_education: List[str] = field(default_factory=lambda: ["本科", "硕士", "博士"])  # 学历筛选条件


@dataclass
class JobConfig:
    """职位相关配置"""
    job_positions: List[str] = field(default_factory=list)  # 目标职位列表
    max_count: int = 1000000  # 最大处理数量


@dataclass
class ResumeConfig:
    """简历处理相关配置"""
    resume_load_timeout: int = 60  # 简历加载超时时间（秒）
    resume_chat_interval: float = 1.5  # 简历聊天间隔（秒），若下面 min/max 都>0 则用随机区间
    resume_chat_interval_min: float = 2.0  # 会话间最小间隔（秒），模拟人类避免风控
    resume_chat_interval_max: float = 5.0  # 会话间最大间隔（秒）
    resume_download_interval_min: float = 15.0  # 每下载一份简历后最小间隔（秒），降低频率
    resume_download_interval_max: float = 45.0  # 每下载一份简历后最大间隔（秒）
    resume_wait_after_agree_min: float = 3.0  # 点击同意后等待区间（秒）
    resume_wait_after_agree_max: float = 7.0  # 点击同意后等待区间（秒）
    resume_wait_after_preview_min: float = 2.0  # 点击预览后等待区间（秒）
    resume_wait_after_preview_max: float = 5.0  # 点击预览后等待区间（秒）
    resume_max_collect: int = 0  # 简历最大收集数量，0表示无限制


@dataclass
class Config:
    """主配置类，聚合所有配置项"""
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    urls: UrlConfig = field(default_factory=UrlConfig)
    timing: TimingConfig = field(default_factory=TimingConfig)
    filters: FilterConfig = field(default_factory=FilterConfig)
    jobs: JobConfig = field(default_factory=JobConfig)
    resume: ResumeConfig = field(default_factory=ResumeConfig)


config = Config()

# 以下为向后兼容的全局变量导出

# 浏览器配置
driver_path = config.browser.driver_path
user_data_dir = config.browser.user_data_dir
debug_port = config.browser.debug_port

# URL配置
login_url = config.urls.login_url
recommend_page_url = config.urls.recommend_page_url
chat_page_url = config.urls.chat_page_url

# 时间配置
wait_login_timeout = config.timing.wait_login_timeout
wait_card_list_seconds = config.timing.wait_card_list_seconds
wait_modal_seconds = config.timing.wait_modal_seconds
interval_min = config.timing.interval_min
interval_max = config.timing.interval_max

# 筛选配置
use_vip_filters = config.filters.use_vip_filters
filter_school = config.filters.filter_school
filter_no_resume_exchange = config.filters.filter_no_resume_exchange
filter_education = config.filters.filter_education

# 职位配置
job_positions = config.jobs.job_positions
max_count = config.jobs.max_count

# 简历配置
resume_load_timeout = config.resume.resume_load_timeout
resume_chat_interval = config.resume.resume_chat_interval
resume_chat_interval_min = config.resume.resume_chat_interval_min
resume_chat_interval_max = config.resume.resume_chat_interval_max
resume_download_interval_min = config.resume.resume_download_interval_min
resume_download_interval_max = config.resume.resume_download_interval_max
resume_wait_after_agree_min = config.resume.resume_wait_after_agree_min
resume_wait_after_agree_max = config.resume.resume_wait_after_agree_max
resume_wait_after_preview_min = config.resume.resume_wait_after_preview_min
resume_wait_after_preview_max = config.resume.resume_wait_after_preview_max
resume_max_collect = config.resume.resume_max_collect
