# Upstream Merge Log

## Merge Date: 2026-04-18

**Source Repo**: [ZhuLinsen/daily_stock_analysis](https://github.com/ZhuLinsen/daily_stock_analysis)
**Diverged Since**: 2026-02-20
**Target Branch**: `claude/analyze-upstream-changes-baEev`

---

## Summary of Changes Merged

### 1. LLM Unified Layer — LiteLLM (`src/analyzer.py`)

- **Before**: Separate Gemini SDK + OpenAI SDK calls with manual branching
- **After**: Single `litellm.completion()` entry point supporting Gemini/Anthropic/OpenAI/DeepSeek/AIHubMix
- Key features:
  - Multi-key rotation (list of keys for each provider, cycled on failure)
  - `RateLimitError` handling with 0.5–2s backoff
  - `ContextWindowExceededError` handling (skip model, no retry)
  - Fallback chain: AIHubMix → Gemini → Anthropic → OpenAI → DeepSeek
  - `generate_text(prompt, max_tokens, temperature)` as primary public API
  - `GeminiAnalyzer` class name kept for backward compatibility
  - `_call_openai_api()` kept as backward-compat shim

### 2. Search Providers (`src/search_service.py`)

Three new search providers added:

| Provider | Class | Notes |
|----------|-------|-------|
| Anspire | `AnspireSearchProvider` | Chinese A-share optimized, `https://plugin.anspire.cn/api/ntsearch/search` |
| MiniMax | `MiniMaxSearchProvider` | Structured search, `https://api.minimaxi.com/v1/coding_plan/search` |
| SearXNG | `SearXNGSearchProvider` | Self-hosted + public instance auto-discovery via searx.space |

Priority order: Anspire → Bocha → MiniMax → Tavily → Brave → SerpAPI → SearXNG

### 3. Data Providers

#### Tushare HK Support (`data_provider/tushare_fetcher.py`)
- New `_is_hk_code()` function to detect HK stock codes
- `_convert_hk_stock_code_for_tushare()` normalizes codes to `NNNNN.HK`
- `_fetch_hk_raw_data()` uses Tushare `hk_daily` API (requires elevated permissions)
- `_normalize_data()` skips unit conversion for HK stocks

#### LongBridge (`data_provider/longbridge_fetcher.py`) — **NEW FILE**
- `LongBridgeFetcher(BaseFetcher)` for US/HK real-time quotes and historical data
- Requires `pip install longbridge`
- Configured via `longbridge_app_key`, `longbridge_app_secret`, `longbridge_access_token`
- `_to_lb_symbol()` converts stock codes to LongBridge format

#### TickFlow (`data_provider/tickflow_fetcher.py`) — **NEW FILE**
- `TickFlowFetcher` for A-share market enhancement data
- `get_realtime_quote()` and `get_market_sentiment()` endpoints
- Configured via `tickflow_api_key`

#### `data_provider/__init__.py`
- Registered `LongBridgeFetcher` and `TickFlowFetcher` in exports

### 4. Stock Index Loader (`src/data/stock_index_loader.py`) — **NEW FILE**

- Lazy-loaded, thread-safe cache for stock code → name mapping
- Reads from `web/public/stocks.index.json` (or `STOCKS_INDEX_PATH` env var)
- Supports list `[{code, name}]` and dict `{code: name}` formats
- Multi-format code normalization: bare codes, `.SH/.SZ/.HK` suffix, `HK` prefix
- Priority between static map and live fetchers in `data_provider/base.py`

### 5. Configuration (`src/config.py`)

Added ~165 lines of new config fields:

| Category | Fields |
|----------|--------|
| LiteLLM | `litellm_model`, `litellm_fallback_models`, `litellm_config_path`, `llm_temperature`, `llm_channels`, `llm_model_list`, `llm_models_source` |
| Multi-key | `gemini_api_keys`, `openai_api_keys`, `anthropic_api_keys`, `anthropic_api_key`, `anthropic_model`, `deepseek_api_keys`, `aihubmix_key` |
| Agent | `agent_litellm_model`, `vision_model`, `vision_provider_priority` |
| Search | `anspire_api_keys`, `minimax_api_keys`, `searxng_base_urls`, `searxng_public_instances_enabled` |
| Data | `tickflow_api_key`, `longbridge_app_key`, `longbridge_app_secret`, `longbridge_access_token`, `feishu_app_id`, `feishu_app_secret`, `feishu_folder_token` |
| SQLite | `sqlite_wal_enabled`, `sqlite_busy_timeout_ms`, `sqlite_write_retry_max`, `sqlite_write_retry_base_delay` |
| Behavior | `report_language`, `market_review_region`, `schedule_run_immediately`, `trading_day_check_enabled` |
| Sentiment | `social_sentiment_api_key`, `social_sentiment_url`, `news_max_age_days`, `news_strategy_profile` |
| Native Agent | `native_agent_enabled`, `agent_mode`, `agent_max_steps`, `agent_skills`, `agent_arch`, `agent_orchestrator_mode`, `agent_orchestrator_timeout_s`, `agent_risk_override`, `agent_memory_enabled`, `agent_skill_autoweight` |
| Fundamental | `enable_fundamental_pipeline`, `fundamental_stage_timeout_seconds`, etc. |

**Deliberately excluded** (raise removed these intentionally):
- Notification sender configs: WeChat, Feishu bot, Pushover, PushPlus, Server酱3, Slack webhook

### 6. Bug Fixes

| Fix | Location |
|-----|----------|
| `max_output_tokens` 2048 → 8192 | `src/market_analyzer.py` |
| Replace private API branching with `generate_text()` | `src/market_analyzer.py` |
| SearchService init wrapped in try/except | `src/core/pipeline.py` |
| All `search_service` calls guarded with None check | `src/core/pipeline.py` |
| SQLite WAL mode + busy timeout PRAGMA | `src/storage.py` |
| Tushare trade date calculation fix | `data_provider/tushare_fetcher.py` |

### 7. SQLite WAL Mode (`src/storage.py`)

- `PRAGMA journal_mode=WAL` for reduced lock contention
- `PRAGMA busy_timeout` configurable (default 5000ms)
- Controlled by `sqlite_wal_enabled` and `sqlite_busy_timeout_ms` config fields

### 8. Multi-Agent System (`src/agent/`) — **NEW DIRECTORY**

Full pipeline-based multi-agent system from upstream, keeping raise's existing `trading_agents/` debate framework:

#### New Files
```
src/agent/
├── __init__.py          (lazy imports)
├── orchestrator.py      (AgentOrchestrator — pipeline coordinator)
├── runner.py            (run_agent_loop, RunLoopResult)
├── executor.py          (AgentExecutor — single-agent tool loop)
├── factory.py           (build_agent_executor / create_agent)
├── llm_adapter.py       (LLMToolAdapter — LiteLLM + tool calling)
├── protocols.py         (AgentContext, StageResult, AgentOpinion, etc.)
├── conversation.py      (ConversationMemory)
├── memory.py            (AgentMemory)
├── events.py            (AgentEvent types)
├── research.py          (ResearchAgent)
├── agents/
│   ├── base_agent.py
│   ├── technical_agent.py
│   ├── intel_agent.py
│   ├── risk_agent.py
│   ├── decision_agent.py
│   └── portfolio_agent.py
├── skills/
│   ├── base.py, defaults.py, aggregator.py, router.py, skill_agent.py
└── tools/
    ├── registry.py, analysis_tools.py, backtest_tools.py,
    ├── data_tools.py, market_tools.py, search_tools.py
```

#### Pipeline Modes
- `quick`: Technical → Decision (~2 LLM calls)
- `standard`: Technical → Intel → Decision (default)
- `full`: Technical → Intel → Risk → Decision
- `specialist`: Technical → Intel → Risk → Specialist → Decision

#### Supporting Modules (new)
- `src/report_language.py` — language normalization, localization helpers
- `src/market_context.py` — market detection (A/HK/US), role/guideline descriptions

#### Pipeline Toggle (`src/core/pipeline.py` Step 7)

Three modes in priority order:
1. `native_agent_enabled=True` → uses `src/agent/` pipeline (Technical→Intel→Risk→Decision)
2. `enable_multi_agent=True` (and `native_agent_enabled=False`) → uses `trading_agents/` LangGraph debate (11 agents, bull/bear debate)
3. Default → standard single-LLM analysis

---

## Not Merged (Intentional)

- **GitHub Actions** — skip (upstream CI workflows not applicable)
- **Notification sender configs** — raise deliberately removed WeChat/Feishu/Pushover/PushPlus/Server酱3/Slack webhook senders
- **Frontend settings page** — new config fields are backend-only, no frontend UI change needed

---

## Future Merge Notes

For the next upstream merge, watch for:
1. Changes to `src/agent/` — check for new agent types or protocol changes
2. Changes to `src/report_language.py` — new localization keys
3. Changes to `src/market_context.py` — new market types (e.g. crypto)
4. New notification providers (still intentionally excluded)
5. Tushare permission-level changes for HK data
6. LiteLLM version bumps in requirements

## Dependencies Added

```
litellm          # LiteLLM unified LLM layer
longbridge       # LongBridge SDK (optional, for US/HK data)
json-repair      # Used by src/agent/ for LLM output parsing
```
