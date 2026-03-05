# Chrome 驱动配置
driver_path = ""                              # ChromeDriver 路径，留空使用系统默认
user_data_dir = r"C:\Users\Admin\AppData\Local\Google\Chrome\User Data\Profile 2"  # Chrome 用户数据目录
debug_port = 9222                             # 远程调试端口，用于复用已打开的浏览器（不关上次窗口时可直接连上）

# 页面 URL
login_url = "https://www.zhipin.com/"         # 登录页面
recommend_page_url = "https://www.zhipin.com/web/chat/recommend"  # 推荐候选人页面
wait_login_timeout = 300                      # 等待登录超时时间（秒）

# 操作限制
max_count = 1000000                           # 最大处理数量

# 操作间隔（秒）
interval_min = 0.1                            # 最小间隔
interval_max = 0.6                            # 最大间隔

# 等待时间（秒）
wait_card_list_seconds = 15                   # 等待卡片列表加载时间
wait_modal_seconds = 5                        # 等待弹窗加载时间

# 筛选配置
use_vip_filters = True                        # 是否使用 VIP 筛选器
filter_school = "双一流院校"                   # 学校筛选条件
filter_no_resume_exchange = "近一个月没有"      # 简历未交换筛选条件
filter_education = ["本科", "硕士", "博士"]     # 学历筛选条件

# 职位配置
job_positions = []                            # 职位列表，为空则处理所有职位
