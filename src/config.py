# -*- coding: utf-8 -*-
"""
===================================
Raise - 配置管理模块
===================================

职责：
1. 使用单例模式管理全局配置
2. 从 .env 文件加载敏感配置
3. 提供类型安全的配置访问接口
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any

from dotenv import load_dotenv, dotenv_values
from loguru import logger


def setup_env(override: bool = False):
    """
    Initialize environment variables from .env file.

    Args:
        override: If True, overwrite existing environment variables with values
                  from .env file. Set to True when reloading config after updates.
                  Default is False to preserve behavior on initial load where
                  system environment variables take precedence.
    """
    # src/config.py -> src/ -> root
    env_file = os.getenv("ENV_FILE")
    if env_file:
        env_path = Path(env_file)
    else:
        env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(dotenv_path=env_path, override=override)


@dataclass
class Config:
    """
    系统配置类 - 单例模式
    
    设计说明：
    - 使用 dataclass 简化配置属性定义
    - 所有配置项从环境变量读取，支持默认值
    - 类方法 get_instance() 实现单例访问
    """
    
    # === 数据源 API Token ===
    tushare_token: Optional[str] = None
    
    # === AI 分析配置 ===
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-3-flash-preview"  # 主模型
    gemini_model_fallback: str = "gemini-2.5-flash"  # 备选模型
    gemini_temperature: float = 0.7  # 温度参数（0.0-2.0，控制输出随机性，默认0.7）

    # Gemini API 请求配置（防止 429 限流）
    gemini_request_delay: float = 2.0  # 请求间隔（秒）
    gemini_max_retries: int = 5  # 最大重试次数
    gemini_retry_delay: float = 5.0  # 重试基础延时（秒）

    # OpenAI 兼容 API（备选，当 Gemini 不可用时使用）
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None  # 如: https://api.openai.com/v1
    openai_model: str = "gpt-4o-mini"  # OpenAI 兼容模型名称
    openai_temperature: float = 0.7  # OpenAI 温度参数（0.0-2.0，默认0.7）
    
    # === LiteLLM 统一层 ===
    litellm_model: str = ""  # 主模型，如 "gemini/gemini-3-flash-preview"
    litellm_fallback_models: List[str] = field(default_factory=list)
    litellm_config_path: Optional[str] = None  # litellm_config.yaml 路径
    llm_temperature: float = 0.7
    llm_channels: List[Dict[str, Any]] = field(default_factory=list)
    llm_model_list: List[Dict[str, Any]] = field(default_factory=list)
    llm_models_source: str = "legacy_env"  # "legacy_env" | "channels" | "yaml"

    # Gemini 多Key支持
    gemini_api_keys: List[str] = field(default_factory=list)

    # Anthropic
    anthropic_api_keys: List[str] = field(default_factory=list)
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    anthropic_temperature: float = 0.7
    anthropic_max_tokens: int = 8192

    # OpenAI 多Key支持
    openai_api_keys: List[str] = field(default_factory=list)

    # DeepSeek
    deepseek_api_keys: List[str] = field(default_factory=list)

    # AIHUBMIX 中转Key
    aihubmix_key: Optional[str] = None

    # Agent 独立模型（Agent 分析与主分析解耦）
    agent_litellm_model: str = ""

    # Vision 模型
    vision_model: str = ""
    vision_provider_priority: str = "gemini,anthropic,openai"

    # === 搜索引擎配置（支持多 Key 负载均衡）===
    bocha_api_keys: List[str] = field(default_factory=list)  # Bocha API Keys
    tavily_api_keys: List[str] = field(default_factory=list)  # Tavily API Keys
    brave_api_keys: List[str] = field(default_factory=list)  # Brave Search API Keys
    serpapi_keys: List[str] = field(default_factory=list)  # SerpAPI Keys

    # 新增搜索引擎
    anspire_api_keys: List[str] = field(default_factory=list)  # 专为A股中文优化
    minimax_api_keys: List[str] = field(default_factory=list)  # MiniMax结构化搜索
    searxng_base_urls: List[str] = field(default_factory=list)  # 自托管SearXNG
    searxng_public_instances_enabled: bool = True  # 自动发现公共实例

    # 自选股列表（从环境变量 STOCK_LIST 加载）
    stock_list: List[str] = field(default_factory=list)

    # Telegram 配置（需要同时配置 Bot Token 和 Chat ID）
    telegram_bot_token: Optional[str] = None  # Bot Token（@BotFather 获取）
    telegram_chat_id: Optional[str] = None  # Chat ID
    telegram_message_thread_id: Optional[str] = None  # Topic ID (Message Thread ID) for groups
    
    # 邮件配置（只需邮箱和授权码，SMTP 自动识别）
    email_sender: Optional[str] = None  # 发件人邮箱
    email_sender_name: str = "raise股票分析助手"  # 发件人显示名称
    email_password: Optional[str] = None  # 邮箱密码/授权码
    email_receivers: List[str] = field(default_factory=list)  # 收件人列表（留空则发给自己）
    
    # 自定义 Webhook（支持多个，逗号分隔）
    # 适用于：钉钉、Discord、Slack、自建服务等任意支持 POST JSON 的 Webhook
    custom_webhook_urls: List[str] = field(default_factory=list)
    custom_webhook_bearer_token: Optional[str] = None  # Bearer Token（用于需要认证的 Webhook）
    
    # Discord 通知配置
    discord_bot_token: Optional[str] = None  # Discord Bot Token
    discord_main_channel_id: Optional[str] = None  # Discord 主频道 ID
    discord_webhook_url: Optional[str] = None  # Discord Webhook URL

    # AstrBot 通知配置
    astrbot_token: Optional[str] = None
    astrbot_url: Optional[str] = None

    # 单股推送模式：每分析完一只股票立即推送，而不是汇总后推送
    single_stock_notify: bool = False

    # 报告类型：simple(精简) 或 full(完整)
    report_type: str = "simple"

    # 分析间隔时间（秒）- 用于避免API限流
    analysis_delay: float = 0.0  # 个股分析与大盘分析之间的延迟
    
    # === 数据库配置 ===
    database_url: Optional[str] = None
    database_path: str = "./data/raise.db"

    # === 数据源扩展 ===
    tickflow_api_key: Optional[str] = None  # TickFlow A股行情增强
    longbridge_app_key: Optional[str] = None  # 长桥 美股/港股
    longbridge_app_secret: Optional[str] = None
    longbridge_access_token: Optional[str] = None

    # 飞书云文档（用于导出报告）
    feishu_app_id: Optional[str] = None
    feishu_app_secret: Optional[str] = None
    feishu_folder_token: Optional[str] = None

    # === SQLite 稳定性配置 ===
    sqlite_wal_enabled: bool = True
    sqlite_busy_timeout_ms: int = 5000
    sqlite_write_retry_max: int = 3
    sqlite_write_retry_base_delay: float = 0.1

    # 是否保存分析上下文快照（用于历史回溯）
    save_context_snapshot: bool = True

    # === 回测配置 ===
    backtest_enabled: bool = True
    backtest_eval_window_days: int = 10
    backtest_min_age_days: int = 14
    backtest_engine_version: str = "v1"
    backtest_neutral_band_pct: float = 2.0
    
    # === 日志配置 ===
    log_dir: str = "./logs"  # 日志文件目录
    log_level: str = "INFO"  # 日志级别
    
    # === 系统配置 ===
    max_workers: int = 3  # 低并发防封禁
    debug: bool = False
    http_proxy: Optional[str] = None  # HTTP 代理 (例如: http://127.0.0.1:10809)
    https_proxy: Optional[str] = None # HTTPS 代理
    
    # === 定时任务配置 ===
    schedule_enabled: bool = False            # 是否启用定时任务
    schedule_time: str = "18:00"              # 每日推送时间（HH:MM 格式）
    market_review_enabled: bool = True        # 是否启用大盘复盘

    # 语言和地区
    report_language: str = "zh"  # "zh" | "en"
    market_review_region: str = "cn"  # "cn" | "us"
    schedule_run_immediately: bool = True
    trading_day_check_enabled: bool = True

    # === 实时行情增强数据配置 ===
    # 实时行情开关（关闭后使用历史收盘价进行分析）
    enable_realtime_quote: bool = True
    # 筹码分布开关（该接口不稳定，云端部署建议关闭）
    enable_chip_distribution: bool = True

    # === 社交舆情配置 ===
    social_sentiment_api_key: Optional[str] = None
    social_sentiment_api_url: str = "https://api.adanos.org"
    news_max_age_days: int = 3
    news_strategy_profile: str = "short"

    # 实时行情数据源优先级（逗号分隔）
    # 推荐顺序：tencent > akshare_sina > efinance > akshare_em > tushare
    # - tencent: 腾讯财经，有量比/换手率/市盈率等，单股查询稳定（推荐）
    # - akshare_sina: 新浪财经，基本行情稳定，但无量比
    # - efinance/akshare_em: 东财全量接口，数据最全但容易被封
    # - tushare: Tushare Pro，需要2000积分，数据全面（付费用户可优先使用）
    realtime_source_priority: str = "tencent,akshare_sina,efinance,akshare_em"
    # 实时行情缓存时间（秒）
    realtime_cache_ttl: int = 600
    # 熔断器冷却时间（秒）
    circuit_breaker_cooldown: int = 300

    # === 多智能体分析配置 ===
    enable_multi_agent: bool = False              # 是否启用多智能体辩论分析模式
    multi_agent_invest_debate_rounds: int = 1     # 投研辩论轮次（1-3，越多质量越高但成本越高）
    multi_agent_risk_debate_rounds: int = 1       # 风控辩论轮次（1-3）
    multi_agent_llm_temperature: float = 0.3      # 智能体 LLM 温度（低于主分析器以提升一致性）

    # === 原生 Agent 系统配置（upstream src/agent/）===
    native_agent_enabled: bool = False  # 启用上游原生agent（区别于trading_agents辩论框架）
    agent_mode: bool = False
    agent_max_steps: int = 10
    agent_skills: List[str] = field(default_factory=list)
    agent_arch: str = "single"  # "single" | "multi"
    agent_orchestrator_mode: str = "standard"  # "quick"|"standard"|"full"|"specialist"
    agent_orchestrator_timeout_s: int = 600
    agent_risk_override: bool = True
    agent_memory_enabled: bool = False
    agent_skill_autoweight: bool = True

    # === 基本面分析管道 ===
    enable_fundamental_pipeline: bool = True
    fundamental_stage_timeout_seconds: float = 1.5
    fundamental_fetch_timeout_seconds: float = 0.8
    fundamental_retry_max: int = 1
    fundamental_cache_ttl_seconds: int = 120
    fundamental_cache_max_entries: int = 256

    # Discord 机器人状态
    discord_bot_status: str = "A股智能分析 | /help"

    # === 流控配置（防封禁关键参数）===
    # Akshare 请求间隔范围（秒）
    akshare_sleep_min: float = 2.0
    akshare_sleep_max: float = 5.0
    
    # Tushare 每分钟最大请求数（免费配额）
    tushare_rate_limit_per_minute: int = 80
    
    # 重试配置
    max_retries: int = 3
    retry_base_delay: float = 1.0
    retry_max_delay: float = 30.0
    
    # === WebUI 配置 ===
    webui_enabled: bool = False
    webui_host: str = "127.0.0.1"
    webui_port: int = 8000
    
    # === 机器人配置 ===
    bot_enabled: bool = True              # 是否启用机器人功能
    bot_command_prefix: str = "/"         # 命令前缀
    bot_rate_limit_requests: int = 10     # 频率限制：窗口内最大请求数
    bot_rate_limit_window: int = 60       # 频率限制：窗口时间（秒）
    bot_admin_users: List[str] = field(default_factory=list)  # 管理员用户 ID 列表
    
    # Telegram 机器人 - 已有 telegram_bot_token, telegram_chat_id
    telegram_webhook_secret: Optional[str] = None   # Webhook 密钥
    
    # 单例实例存储
    _instance: Optional['Config'] = None
    
    @classmethod
    def get_instance(cls) -> 'Config':
        """
        获取配置单例实例
        
        单例模式确保：
        1. 全局只有一个配置实例
        2. 配置只从环境变量加载一次
        3. 所有模块共享相同配置
        """
        if cls._instance is None:
            cls._instance = cls._load_from_env()
        return cls._instance
    
    @classmethod
    def _load_from_env(cls) -> 'Config':
        """
        从 .env 文件加载配置
        
        加载优先级：
        1. 系统环境变量
        2. .env 文件
        3. 代码中的默认值
        """
        # 确保环境变量已加载
        setup_env()

        # === 智能代理配置 (关键修复) ===
        # 如果配置了代理，自动设置 NO_PROXY 以排除国内数据源，避免行情获取失败
        http_proxy = os.getenv('HTTP_PROXY') or os.getenv('http_proxy')
        if http_proxy:
            # 国内金融数据源域名列表
            domestic_domains = [
                'eastmoney.com',   # 东方财富 (Efinance/Akshare)
                'sina.com.cn',     # 新浪财经 (Akshare)
                '163.com',         # 网易财经 (Akshare)
                'tushare.pro',     # Tushare
                'baostock.com',    # Baostock
                'sse.com.cn',      # 上交所
                'szse.cn',         # 深交所
                'csindex.com.cn',  # 中证指数
                'cninfo.com.cn',   # 巨潮资讯
                'localhost',
                '127.0.0.1'
            ]

            # 获取现有的 no_proxy
            current_no_proxy = os.getenv('NO_PROXY') or os.getenv('no_proxy') or ''
            existing_domains = current_no_proxy.split(',') if current_no_proxy else []

            # 合并去重
            final_domains = list(set(existing_domains + domestic_domains))
            final_no_proxy = ','.join(filter(None, final_domains))

            # 设置环境变量 (requests/urllib3/aiohttp 都会遵守此设置)
            os.environ['NO_PROXY'] = final_no_proxy
            os.environ['no_proxy'] = final_no_proxy

            # 确保 HTTP_PROXY 也被正确设置（以防仅在 .env 中定义但未导出）
            os.environ['HTTP_PROXY'] = http_proxy
            os.environ['http_proxy'] = http_proxy

            # HTTPS_PROXY 同理
            https_proxy = os.getenv('HTTPS_PROXY') or os.getenv('https_proxy')
            if https_proxy:
                os.environ['HTTPS_PROXY'] = https_proxy
                os.environ['https_proxy'] = https_proxy

        
        # 解析自选股列表（逗号分隔）
        stock_list_str = os.getenv('STOCK_LIST', '')
        stock_list = [
            code.strip() 
            for code in stock_list_str.split(',') 
            if code.strip()
        ]
        
        # 如果没有配置，使用默认的示例股票
        if not stock_list:
            stock_list = ['600519', '000001', '300750']
        
        # 解析搜索引擎 API Keys（支持多个 key，逗号分隔）
        bocha_keys_str = os.getenv('BOCHA_API_KEYS', '')
        bocha_api_keys = [k.strip() for k in bocha_keys_str.split(',') if k.strip()]
        
        tavily_keys_str = os.getenv('TAVILY_API_KEYS', '')
        tavily_api_keys = [k.strip() for k in tavily_keys_str.split(',') if k.strip()]
        
        serpapi_keys_str = os.getenv('SERPAPI_API_KEYS', '')
        serpapi_keys = [k.strip() for k in serpapi_keys_str.split(',') if k.strip()]

        brave_keys_str = os.getenv('BRAVE_API_KEYS', '')
        brave_api_keys = [k.strip() for k in brave_keys_str.split(',') if k.strip()]

        return cls(
            stock_list=stock_list,
            tushare_token=os.getenv('TUSHARE_TOKEN'),
            gemini_api_key=os.getenv('GEMINI_API_KEY'),
            gemini_model=os.getenv('GEMINI_MODEL', 'gemini-3-flash-preview'),
            gemini_model_fallback=os.getenv('GEMINI_MODEL_FALLBACK', 'gemini-2.5-flash'),
            gemini_temperature=float(os.getenv('GEMINI_TEMPERATURE', '0.7')),
            gemini_request_delay=float(os.getenv('GEMINI_REQUEST_DELAY', '2.0')),
            gemini_max_retries=int(os.getenv('GEMINI_MAX_RETRIES', '5')),
            gemini_retry_delay=float(os.getenv('GEMINI_RETRY_DELAY', '5.0')),
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            openai_base_url=os.getenv('OPENAI_BASE_URL'),
            openai_model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
            openai_temperature=float(os.getenv('OPENAI_TEMPERATURE', '0.7')),
            # LiteLLM
            litellm_model=os.getenv('LITELLM_MODEL', ''),
            litellm_fallback_models=[m.strip() for m in os.getenv('LITELLM_FALLBACK_MODELS', '').split(',') if m.strip()],
            litellm_config_path=os.getenv('LITELLM_CONFIG', os.getenv('LITELLM_CONFIG_YAML')),
            llm_temperature=float(os.getenv('LLM_TEMPERATURE', '0.7')),
            # Multi-key Gemini
            gemini_api_keys=[k.strip() for k in os.getenv('GEMINI_API_KEYS', '').split(',') if k.strip()],
            # Anthropic
            anthropic_api_keys=[k.strip() for k in os.getenv('ANTHROPIC_API_KEYS', os.getenv('ANTHROPIC_API_KEY', '')).split(',') if k.strip()],
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
            anthropic_model=os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022'),
            anthropic_temperature=float(os.getenv('ANTHROPIC_TEMPERATURE', '0.7')),
            anthropic_max_tokens=int(os.getenv('ANTHROPIC_MAX_TOKENS', '8192')),
            # OpenAI multi-key
            openai_api_keys=[k.strip() for k in os.getenv('OPENAI_API_KEYS', '').split(',') if k.strip()],
            # DeepSeek
            deepseek_api_keys=[k.strip() for k in os.getenv('DEEPSEEK_API_KEYS', os.getenv('DEEPSEEK_API_KEY', '')).split(',') if k.strip()],
            # AIHUBMIX
            aihubmix_key=os.getenv('AIHUBMIX_KEY'),
            agent_litellm_model=os.getenv('AGENT_LITELLM_MODEL', ''),
            vision_model=os.getenv('VISION_MODEL', ''),
            vision_provider_priority=os.getenv('VISION_PROVIDER_PRIORITY', 'gemini,anthropic,openai'),
            bocha_api_keys=bocha_api_keys,
            tavily_api_keys=tavily_api_keys,
            brave_api_keys=brave_api_keys,
            serpapi_keys=serpapi_keys,
            # New search
            anspire_api_keys=[k.strip() for k in os.getenv('ANSPIRE_API_KEYS', '').split(',') if k.strip()],
            minimax_api_keys=[k.strip() for k in os.getenv('MINIMAX_API_KEYS', '').split(',') if k.strip()],
            searxng_base_urls=[u.strip() for u in os.getenv('SEARXNG_BASE_URLS', '').split(',') if u.strip()],
            searxng_public_instances_enabled=os.getenv('SEARXNG_PUBLIC_INSTANCES_ENABLED', 'true').lower() == 'true',
            telegram_bot_token=os.getenv('TELEGRAM_BOT_TOKEN'),
            telegram_chat_id=os.getenv('TELEGRAM_CHAT_ID'),
            telegram_message_thread_id=os.getenv('TELEGRAM_MESSAGE_THREAD_ID'),
            email_sender=os.getenv('EMAIL_SENDER'),
            email_sender_name=os.getenv('EMAIL_SENDER_NAME', 'raise股票分析助手'),
            email_password=os.getenv('EMAIL_PASSWORD'),
            email_receivers=[r.strip() for r in os.getenv('EMAIL_RECEIVERS', '').split(',') if r.strip()],
            custom_webhook_urls=[u.strip() for u in os.getenv('CUSTOM_WEBHOOK_URLS', '').split(',') if u.strip()],
            custom_webhook_bearer_token=os.getenv('CUSTOM_WEBHOOK_BEARER_TOKEN'),
            discord_bot_token=os.getenv('DISCORD_BOT_TOKEN'),
            discord_main_channel_id=os.getenv('DISCORD_MAIN_CHANNEL_ID'),
            discord_webhook_url=os.getenv('DISCORD_WEBHOOK_URL'),
            astrbot_url=os.getenv('ASTRBOT_URL'),
            astrbot_token=os.getenv('ASTRBOT_TOKEN'),
            single_stock_notify=os.getenv('SINGLE_STOCK_NOTIFY', 'false').lower() == 'true',
            report_type=os.getenv('REPORT_TYPE', 'simple').lower(),
            analysis_delay=float(os.getenv('ANALYSIS_DELAY', '0')),
            database_url=os.getenv('DATABASE_URL'),
            database_path=os.getenv('DATABASE_PATH', './data/raise.db'),
            # Data providers
            tickflow_api_key=os.getenv('TICKFLOW_API_KEY'),
            longbridge_app_key=os.getenv('LONGBRIDGE_APP_KEY'),
            longbridge_app_secret=os.getenv('LONGBRIDGE_APP_SECRET'),
            longbridge_access_token=os.getenv('LONGBRIDGE_ACCESS_TOKEN'),
            feishu_app_id=os.getenv('FEISHU_APP_ID'),
            feishu_app_secret=os.getenv('FEISHU_APP_SECRET'),
            feishu_folder_token=os.getenv('FEISHU_FOLDER_TOKEN'),
            # SQLite stability
            sqlite_wal_enabled=os.getenv('SQLITE_WAL_ENABLED', 'true').lower() == 'true',
            sqlite_busy_timeout_ms=int(os.getenv('SQLITE_BUSY_TIMEOUT_MS', '5000')),
            sqlite_write_retry_max=int(os.getenv('SQLITE_WRITE_RETRY_MAX', '3')),
            sqlite_write_retry_base_delay=float(os.getenv('SQLITE_WRITE_RETRY_BASE_DELAY', '0.1')),
            save_context_snapshot=os.getenv('SAVE_CONTEXT_SNAPSHOT', 'true').lower() == 'true',
            backtest_enabled=os.getenv('BACKTEST_ENABLED', 'true').lower() == 'true',
            backtest_eval_window_days=int(os.getenv('BACKTEST_EVAL_WINDOW_DAYS', '10')),
            backtest_min_age_days=int(os.getenv('BACKTEST_MIN_AGE_DAYS', '14')),
            backtest_engine_version=os.getenv('BACKTEST_ENGINE_VERSION', 'v1'),
            backtest_neutral_band_pct=float(os.getenv('BACKTEST_NEUTRAL_BAND_PCT', '2.0')),
            log_dir=os.getenv('LOG_DIR', './logs'),
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            max_workers=int(os.getenv('MAX_WORKERS', '3')),
            debug=os.getenv('DEBUG', 'false').lower() == 'true',
            http_proxy=os.getenv('HTTP_PROXY'),
            https_proxy=os.getenv('HTTPS_PROXY'),
            schedule_enabled=os.getenv('SCHEDULE_ENABLED', 'false').lower() == 'true',
            schedule_time=os.getenv('SCHEDULE_TIME', '18:00'),
            market_review_enabled=os.getenv('MARKET_REVIEW_ENABLED', 'true').lower() == 'true',
            # Language/region
            report_language=os.getenv('REPORT_LANGUAGE', 'zh').lower() or 'zh',
            market_review_region=os.getenv('MARKET_REVIEW_REGION', 'cn').lower(),
            schedule_run_immediately=os.getenv('SCHEDULE_RUN_IMMEDIATELY', 'true').lower() == 'true',
            trading_day_check_enabled=os.getenv('TRADING_DAY_CHECK_ENABLED', 'true').lower() == 'true',
            webui_enabled=os.getenv('WEBUI_ENABLED', 'false').lower() == 'true',
            webui_host=os.getenv('WEBUI_HOST', '127.0.0.1'),
            webui_port=int(os.getenv('WEBUI_PORT', '8000')),
            # 机器人配置
            bot_enabled=os.getenv('BOT_ENABLED', 'true').lower() == 'true',
            bot_command_prefix=os.getenv('BOT_COMMAND_PREFIX', '/'),
            bot_rate_limit_requests=int(os.getenv('BOT_RATE_LIMIT_REQUESTS', '10')),
            bot_rate_limit_window=int(os.getenv('BOT_RATE_LIMIT_WINDOW', '60')),
            bot_admin_users=[u.strip() for u in os.getenv('BOT_ADMIN_USERS', '').split(',') if u.strip()],
            # Telegram
            telegram_webhook_secret=os.getenv('TELEGRAM_WEBHOOK_SECRET'),
            # Discord 机器人扩展配置
            discord_bot_status=os.getenv('DISCORD_BOT_STATUS', 'A股智能分析 | /help'),
            # 实时行情增强数据配置
            enable_realtime_quote=os.getenv('ENABLE_REALTIME_QUOTE', 'true').lower() == 'true',
            enable_chip_distribution=os.getenv('ENABLE_CHIP_DISTRIBUTION', 'true').lower() == 'true',
            # Social sentiment
            social_sentiment_api_key=os.getenv('SOCIAL_SENTIMENT_API_KEY'),
            social_sentiment_api_url=os.getenv('SOCIAL_SENTIMENT_API_URL', 'https://api.adanos.org'),
            news_max_age_days=int(os.getenv('NEWS_MAX_AGE_DAYS', '3')),
            news_strategy_profile=os.getenv('NEWS_STRATEGY_PROFILE', 'short'),
            # 实时行情数据源优先级：
            # - tencent: 腾讯财经，有量比/换手率/PE/PB等，单股查询稳定（推荐）
            # - akshare_sina: 新浪财经，基本行情稳定，但无量比
            # - efinance/akshare_em: 东财全量接口，数据最全但容易被封
            # - tushare: Tushare Pro，需要2000积分，数据全面
            realtime_source_priority=cls._resolve_realtime_source_priority(),
            realtime_cache_ttl=int(os.getenv('REALTIME_CACHE_TTL', '600')),
            circuit_breaker_cooldown=int(os.getenv('CIRCUIT_BREAKER_COOLDOWN', '300')),
            # 多智能体配置
            enable_multi_agent=os.getenv('ENABLE_MULTI_AGENT', 'false').lower() == 'true',
            multi_agent_invest_debate_rounds=int(os.getenv('MULTI_AGENT_INVEST_DEBATE_ROUNDS', '1')),
            multi_agent_risk_debate_rounds=int(os.getenv('MULTI_AGENT_RISK_DEBATE_ROUNDS', '1')),
            multi_agent_llm_temperature=float(os.getenv('MULTI_AGENT_LLM_TEMPERATURE', '0.3')),
            # Native agent system
            native_agent_enabled=os.getenv('NATIVE_AGENT_ENABLED', 'false').lower() == 'true',
            agent_mode=os.getenv('AGENT_MODE', 'false').lower() == 'true',
            agent_max_steps=int(os.getenv('AGENT_MAX_STEPS', '10')),
            agent_skills=[s.strip() for s in os.getenv('AGENT_SKILLS', '').split(',') if s.strip()],
            agent_arch=os.getenv('AGENT_ARCH', 'single'),
            agent_orchestrator_mode=os.getenv('AGENT_ORCHESTRATOR_MODE', 'standard'),
            agent_orchestrator_timeout_s=int(os.getenv('AGENT_ORCHESTRATOR_TIMEOUT_S', '600')),
            agent_risk_override=os.getenv('AGENT_RISK_OVERRIDE', 'true').lower() == 'true',
            agent_memory_enabled=os.getenv('AGENT_MEMORY_ENABLED', 'false').lower() == 'true',
            agent_skill_autoweight=os.getenv('AGENT_SKILL_AUTOWEIGHT', 'true').lower() == 'true',
            # Fundamental pipeline
            enable_fundamental_pipeline=os.getenv('ENABLE_FUNDAMENTAL_PIPELINE', 'true').lower() == 'true',
            fundamental_stage_timeout_seconds=float(os.getenv('FUNDAMENTAL_STAGE_TIMEOUT_SECONDS', '1.5')),
            fundamental_fetch_timeout_seconds=float(os.getenv('FUNDAMENTAL_FETCH_TIMEOUT_SECONDS', '0.8')),
            fundamental_retry_max=int(os.getenv('FUNDAMENTAL_RETRY_MAX', '1')),
            fundamental_cache_ttl_seconds=int(os.getenv('FUNDAMENTAL_CACHE_TTL_SECONDS', '120')),
            fundamental_cache_max_entries=int(os.getenv('FUNDAMENTAL_CACHE_MAX_ENTRIES', '256')),
        )
    
    @classmethod
    def _resolve_realtime_source_priority(cls) -> str:
        """
        Resolve realtime source priority with automatic tushare injection.

        When TUSHARE_TOKEN is configured but REALTIME_SOURCE_PRIORITY is not
        explicitly set, automatically prepend 'tushare' to the default priority
        so that the paid data source is utilized for realtime quotes as well.
        """
        explicit = os.getenv('REALTIME_SOURCE_PRIORITY')
        default_priority = 'tencent,akshare_sina,efinance,akshare_em'

        if explicit:
            # User explicitly set priority, respect it
            return explicit

        tushare_token = os.getenv('TUSHARE_TOKEN', '').strip()
        if tushare_token:
            # Token configured but no explicit priority override
            # Prepend tushare so the paid source is tried first
            resolved = f'tushare,{default_priority}'
            logger.info(
                f"TUSHARE_TOKEN detected, auto-injecting tushare into realtime priority: {resolved}"
            )
            return resolved

        return default_priority

    @classmethod
    def reset_instance(cls) -> None:
        """重置单例（主要用于测试）"""
        cls._instance = None

    def refresh_stock_list(self) -> None:
        """
        热读取 STOCK_LIST 环境变量并更新配置中的自选股列表
        
        支持两种配置方式：
        1. .env 文件（本地开发、定时任务模式） - 修改后下次执行自动生效
        2. 系统环境变量（GitHub Actions、Docker） - 启动时固定，运行中不变
        """
        # 优先从 .env 文件读取最新配置，这样即使在容器环境中修改了 .env 文件，
        # 也能获取到最新的股票列表配置
        env_file = os.getenv("ENV_FILE")
        env_path = Path(env_file) if env_file else (Path(__file__).parent.parent / '.env')
        stock_list_str = ''
        if env_path.exists():
            # 直接从 .env 文件读取最新的配置
            env_values = dotenv_values(env_path)
            stock_list_str = (env_values.get('STOCK_LIST') or '').strip()

        # 如果 .env 文件不存在或未配置，才尝试从系统环境变量读取
        if not stock_list_str:
            stock_list_str = os.getenv('STOCK_LIST', '')

        stock_list = [
            code.strip()
            for code in stock_list_str.split(',')
            if code.strip()
        ]

        if not stock_list:        
            stock_list = ['000001']

        self.stock_list = stock_list
    
    def validate(self) -> List[str]:
        """
        验证配置完整性
        
        Returns:
            缺失或无效配置项的警告列表
        """
        warnings = []
        
        if not self.stock_list:
            warnings.append("警告：未配置自选股列表 (STOCK_LIST)")
        
        if not self.tushare_token:
            warnings.append("提示：未配置 Tushare Token，将使用其他数据源")
        
        if not self.gemini_api_key and not self.openai_api_key:
            warnings.append("警告：未配置 Gemini 或 OpenAI API Key，AI 分析功能将不可用")
        elif not self.gemini_api_key:
            warnings.append("提示：未配置 Gemini API Key，将使用 OpenAI 兼容 API")
        
        if not self.bocha_api_keys and not self.tavily_api_keys and not self.brave_api_keys and not self.serpapi_keys and not self.anspire_api_keys and not self.minimax_api_keys and not self.searxng_base_urls:
            warnings.append("提示：未配置搜索引擎 API Key，新闻搜索功能将不可用")
        
        # 检查通知配置
        has_notification = (
            (self.telegram_bot_token and self.telegram_chat_id) or
            (self.email_sender and self.email_password) or
            (self.custom_webhook_urls and len(self.custom_webhook_urls) > 0) or
            (self.discord_bot_token and self.discord_main_channel_id) or
            self.discord_webhook_url or
            (self.astrbot_url and self.astrbot_token)
        )
        if not has_notification:
            warnings.append("提示：未配置通知渠道，将不发送推送通知")
        
        return warnings
    
    def get_db_url(self) -> str:
        """
        获取 SQLAlchemy 数据库连接 URL
        
        自动创建数据库目录（如果不存在）
        """
        database_url = (self.database_url or "").strip()
        if database_url:
            return database_url

        db_path = Path(self.database_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{db_path.absolute()}"


# === 便捷的配置访问函数 ===
def get_config() -> Config:
    """获取全局配置实例的快捷方式"""
    return Config.get_instance()


# === Agent helper functions (used by src/agent/ pipeline system) ===

# Default maximum steps for the agent loop
AGENT_MAX_STEPS_DEFAULT: int = 10


def get_effective_agent_primary_model(config: Optional['Config'] = None) -> str:
    """Return the primary model for the agent, preferring agent_litellm_model then litellm_model."""
    if config is None:
        config = get_config()
    model = (getattr(config, 'agent_litellm_model', '') or '').strip()
    if not model:
        model = (getattr(config, 'litellm_model', '') or '').strip()
    return model


def get_effective_agent_models_to_try(config: Optional['Config'] = None) -> List[str]:
    """Return ordered list of models to try for agent calls (primary + fallbacks)."""
    if config is None:
        config = get_config()
    primary = get_effective_agent_primary_model(config)
    fallbacks = list(getattr(config, 'litellm_fallback_models', []) or [])
    models = []
    if primary:
        models.append(primary)
    for m in fallbacks:
        m = (m or '').strip()
        if m and m not in models:
            models.append(m)
    return models or ['gemini/gemini-2.5-flash']


def get_configured_llm_models(model_list: List[Dict[str, Any]]) -> List[str]:
    """Return unique model names from a litellm model_list config."""
    seen = []
    for entry in (model_list or []):
        lp = entry.get('litellm_params', {})
        m = lp.get('model', '') if isinstance(lp, dict) else ''
        if m and m not in seen:
            seen.append(m)
    return seen


def get_api_keys_for_model(model: str, config: Optional['Config'] = None) -> List[str]:
    """Return API key(s) for the given model based on its provider prefix."""
    if config is None:
        config = get_config()
    if not model:
        return []
    prefix = model.split('/')[0].lower() if '/' in model else ''
    if prefix in ('gemini', 'google') or 'gemini' in model.lower():
        keys = list(getattr(config, 'gemini_api_keys', []) or [])
        if not keys:
            k = getattr(config, 'gemini_api_key', '') or ''
            if k:
                keys = [k]
        return keys
    if prefix == 'anthropic' or 'claude' in model.lower():
        keys = list(getattr(config, 'anthropic_api_keys', []) or [])
        if not keys:
            k = getattr(config, 'anthropic_api_key', '') or ''
            if k:
                keys = [k]
        return keys
    if prefix == 'openai' or not prefix:
        keys = list(getattr(config, 'openai_api_keys', []) or [])
        if not keys:
            k = getattr(config, 'openai_api_key', '') or ''
            if k:
                keys = [k]
        return keys
    if prefix == 'deepseek':
        return list(getattr(config, 'deepseek_api_keys', []) or [])
    return []


def extra_litellm_params(model: str, config: Optional['Config'] = None) -> Dict[str, Any]:
    """Return extra litellm params (e.g. api_base) for a given model."""
    if config is None:
        config = get_config()
    params: Dict[str, Any] = {}
    prefix = model.split('/')[0].lower() if '/' in model else ''
    if (prefix == 'openai' or not prefix):
        base = getattr(config, 'openai_base_url', '') or ''
        if base:
            params['api_base'] = base
    return params


if __name__ == "__main__":
    # 测试配置加载
    config = get_config()
    print("=== 配置加载测试 ===")
    print(f"自选股列表: {config.stock_list}")
    print(f"数据库路径: {config.database_path}")
    print(f"最大并发数: {config.max_workers}")
    print(f"调试模式: {config.debug}")
    
    # 验证配置
    warnings = config.validate()
    if warnings:
        print("\n配置验证结果:")
        for w in warnings:
            print(f"  - {w}")
