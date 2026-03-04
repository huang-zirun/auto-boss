# 带筛选调试日志的入口：开启 config.debug_filter 后执行与 auto_greeting.py 相同的主流程。
# 用法：python run_with_filter_debug.py

import config

config.debug_filter = True

from auto_greeting import BossAutoGreeting

if __name__ == "__main__":
    bot = BossAutoGreeting(
        driver_path=config.driver_path,
        user_data_dir=config.user_data_dir,
        debug_port=getattr(config, "debug_port", 9222),
    )
    try:
        bot.login(
            url=config.login_url,
            redirect_url=config.recommend_page_url,
            wait_login_timeout=getattr(config, "wait_login_timeout", 300),
        )
        bot.auto_greeting_recommend_page(
            config.greeting_message,
            max_count=config.max_count,
            interval_min=config.interval_min,
            interval_max=config.interval_max,
            wait_card_list_seconds=config.wait_card_list_seconds,
            wait_modal_seconds=config.wait_modal_seconds,
            use_vip_filters=getattr(config, "use_vip_filters", False),
            filter_school=getattr(config, "filter_school", None),
            filter_no_resume_exchange=getattr(config, "filter_no_resume_exchange", None),
            filter_education=getattr(config, "filter_education", []),
        )
    finally:
        bot.close()
