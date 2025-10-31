"""
Utility functions for handling timezone conversions and preparing prompts for DeepSeek.

This module provides helper functions to enrich stock records with local and UTC time
information based on the exchange each security trades on. It also includes a
prompt generator tailored for DeepSeek analysis that incorporates these time
fields alongside common financial metrics.

The primary motivation for these utilities is to allow downstream models (such
as DeepSeek) to learn about temporal context differences between exchanges.

Example usage: 

    from exchange_time_utils import add_exchange_time_fields, generate_deepseek_prompt

    records = [
        {
            "symbol": "02388.HK",
            "exchange": "SEHK",
            "eps": 3.6,
            "eps_ttm": 3.8,
            "bps": 32.8,
            "dividend": 1.999,
        },
        # ... more records ...
    ]

    # Enrich records with local and UTC timestamps
    enriched = add_exchange_time_fields(records)

    # Generate a prompt for DeepSeek analysis
    prompt = generate_deepseek_prompt(enriched)

Functions
---------
add_exchange_time_fields(records, tz_map=None, current_time=None)
    Adds 'local_time' and 'utc_time' ISO strings to each record.

generate_deepseek_prompt(records, title, tasks, extra_requirements, summary_words)
    Builds a prompt string incorporating enriched records and analysis instructions.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Iterable, List, Dict, Optional, Sequence, Union, Mapping

try:
    # zoneinfo is available in Python >= 3.9
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    # Python < 3.9 fallback; you may need to install backports.zoneinfo
    from backports.zoneinfo import ZoneInfo  # type: ignore


# Mapping of exchange codes to their respective IANA timezone names. Extend
# this mapping as needed for additional exchanges.
EXCHANGE_TZ: Mapping[str, str] = {
    "SEHK": "Asia/Hong_Kong",      # Stock Exchange of Hong Kong
    "NYSE": "America/New_York",    # New York Stock Exchange
    "NASDAQ": "America/New_York",  # NASDAQ
    "LSE": "Europe/London",        # London Stock Exchange
    "TSE": "Asia/Tokyo",           # Tokyo Stock Exchange
    "SGX": "Asia/Singapore",       # Singapore Exchange
}


def add_exchange_time_fields(
    records: Sequence[Dict[str, Union[str, float, int, list, None]]],
    tz_map: Optional[Mapping[str, str]] = None,
    current_time: Optional[datetime] = None,
) -> List[Dict[str, Union[str, float, int, list, None]]]:
    """Enrich each record with local and UTC timestamps.

    Parameters
    ----------
    records : Sequence[Dict[str, Any]]
        An iterable of dictionaries representing stock data. Each record must
        contain an 'exchange' key identifying the trading venue. The function
        does not mutate the original records; instead, it returns a new list
        containing shallow copies with additional keys.

    tz_map : Optional[Mapping[str, str]]
        A mapping from exchange codes to IANA timezone strings. If omitted,
        the module-level ``EXCHANGE_TZ`` mapping is used. Passing a custom
        mapping allows clients to override or extend default timezones.

    current_time : Optional[datetime]
        The reference UTC time used for conversion. If None, the current
        system UTC time is used via ``datetime.utcnow()``. This parameter
        exists primarily to facilitate deterministic testing.

    Returns
    -------
    List[Dict[str, Any]]
        A list of enriched records where each record now includes two
        additional keys:

        - ``local_time``: ISO-8601 formatted datetime string in the exchange's
          local timezone, or None if the exchange's timezone is unknown.
        - ``utc_time``: ISO-8601 formatted datetime string in UTC.

    Notes
    -----
    If a record lacks an 'exchange' key or its value is not present in the
    provided timezone mapping, ``local_time`` will be set to None. The
    ``utc_time`` field will always be populated.
    """

    tz_map = tz_map or EXCHANGE_TZ
    now_utc = (current_time or datetime.utcnow()).replace(tzinfo=ZoneInfo("UTC"))
    enriched: List[Dict[str, Union[str, float, int, list, None]]] = []
    for rec in records:
        # Make a shallow copy to avoid mutating the input
        enriched_rec = dict(rec)
        exchange = enriched_rec.get("exchange")
        tz_name = tz_map.get(str(exchange)) if exchange is not None else None
        if tz_name:
            try:
                local_time = now_utc.astimezone(ZoneInfo(tz_name))
                enriched_rec["local_time"] = local_time.isoformat()
            except Exception:
                # In case the timezone cannot be resolved, set None
                enriched_rec["local_time"] = None
        else:
            enriched_rec["local_time"] = None
        # Always include UTC time
        enriched_rec["utc_time"] = now_utc.isoformat()
        enriched.append(enriched_rec)
    return enriched


def generate_deepseek_prompt(
    records: Sequence[Dict[str, Union[str, float, int, list, None]]],
    title: str = "你是一名金融分析AI，请对以下股票标的基础数据进行结构化分析与比较。",
    tasks: Optional[Sequence[str]] = None,
    extra_requirements: Optional[Sequence[str]] = None,
    summary_words: int = 200,
) -> str:
    """Generate a DeepSeek analysis prompt incorporating enriched stock data.

    This function serializes the provided records to a JSON block and
    constructs a prompt instructing DeepSeek to perform various analyses
    (yield calculation, EPS growth, etc.). It assumes the records have been
    pre-enriched via ``add_exchange_time_fields`` but does not enforce it; if
    missing, the ``local_time`` and ``utc_time`` fields will appear absent
    in the JSON.

    Parameters
    ----------
    records : Sequence[Dict[str, Any]]
        The stock records to include in the prompt. Records will be
        serialized using ``json.dumps`` with non-ASCII characters preserved.

    title : str, optional
        A preamble describing the role of the AI and the overall analysis
        objective. The default introduces the AI as a financial analyst.

    tasks : Optional[Sequence[str]], optional
        A list of analysis instructions. If not provided, sensible defaults
        covering yield calculation, EPS growth, ranking, grouping by currency,
        anomaly detection, and table formatting will be used.

    extra_requirements : Optional[Sequence[str]], optional
        Additional constraints on output formatting or summarization. A
        default instructs the model to write a concise Chinese summary.

    summary_words : int, optional
        Suggested length for the concluding summary (approximate word count).
        The value is interpolated into the default extra requirements if they
        don't already specify a length.

    Returns
    -------
    str
        A structured prompt ready to be sent to DeepSeek for analysis.
    """

    default_tasks = [
        "将以上数据转换为表格形式（每行一只标的）；",
        "计算以下指标：股息收益率 = dividend / bps；EPS增长率 = (eps_ttm - eps) / eps（若 eps=0 则置为null）；",
        "统计并比较：① 股息收益率最高的前3家公司；② EPS_TTM 最高的前3家公司；",
        "按 currency 分组对比平均 eps_ttm、bps、dividend；",
        "检测异常：如 dividend > eps_ttm、eps_ttm < 0、或缺失关键字段；在结果表格中以“⚠️”标注；",
        "以 Markdown 表格输出列：symbol/name_cn/currency/eps_ttm/bps/dividend/股息收益率/EPS增长率/ local_time / utc_time；",
    ]
    default_extra = [
        "结尾给出中文总结，说明整体财务特征、差异与显著异常。",
    ]
    tasks_list = list(tasks) if tasks else default_tasks
    extra_list = list(extra_requirements) if extra_requirements else default_extra
    # Append summary length hint if absent
    summary_hint = f"中文总结请控制在约{summary_words}字。"
    if not any(summary_hint in req for req in extra_list):
        extra_list.append(summary_hint)

    # Serialize records to JSON, preserving non-ASCII characters for Chinese labels
    data_json = json.dumps(list(records), ensure_ascii=False, indent=2)

    tasks_text = "\n".join([f"{idx+1}️⃣ {t}" for idx, t in enumerate(tasks_list)])
    extra_text = "\n".join([f"- {e}" for e in extra_list])

    prompt = (
        f"{title}\n\n"
        f"【输入数据】\n{data_json}\n\n"
        f"【分析任务】\n{tasks_text}\n\n"
        f"【额外要求】\n{extra_text}\n"
    )
    return prompt


__all__ = [
    "EXCHANGE_TZ",
    "add_exchange_time_fields",
    "generate_deepseek_prompt",
]