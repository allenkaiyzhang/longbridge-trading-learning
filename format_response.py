"""
Utility functions to retrieve and format security static information from LongPort.

This module wraps the LongPort QuoteContext API to fetch static information for
given symbols and convert it into a structured dictionary with Chinese keys.
It also includes a helper to coerce semi-structured API responses into proper
JSON by quoting keys and values where necessary.

Functions
---------
getBasicStatus(symbols)
    Fetch static information for a list of symbols using the LongPort API.

force_to_dict(text)
    Normalize a string representation of a Python dict/list into a proper
    JSON-compatible dictionary.

getStockDetails(resp)
    Convert a list of raw API responses into a list of dictionaries with
    translated keys.

translate_keys(data)
    Recursively translate English keys in dictionaries/lists to Chinese labels
    using the KEY_MAP mapping.
"""

from __future__ import annotations

import json
import re
from longport.openapi import QuoteContext, Config

# Mapping of English keys returned by the API to their Chinese descriptions
KEY_MAP = {
    "secu_static_info": "标的基础数据列表",
    "symbol": "标的代码",
    "name_cn": "中文简体标的名称",
    "name_en": "英文标的名称",
    "name_hk": "中文繁体标的名称",
    "exchange": "标的所属交易所",
    "currency": "交易币种",
    "lot_size": "每手股数",
    "total_shares": "总股本",
    "circulating_shares": "流通股本",
    "hk_shares": "港股股本 (仅港股)",
    "eps": "每股盈利",
    "eps_ttm": "每股盈利 (TTM)",
    "bps": "每股净资产",
    "dividend_yield": "股息",
    "stock_derivatives": "可提供的衍生品行情类型",
    "board": "标的所属板块",
}


def getBasicStatus(symbol: list[str]):
    """Fetch static information for the given symbols via LongPort."""
    config = Config.from_env()
    ctx = QuoteContext(config)
    resp = ctx.static_info(symbol)
    return resp


def force_to_dict(text: str):
    """
    Coerce a string representation of a dict or list into a JSON-compatible dict.

    The LongPort API may return responses that are not strictly JSON (e.g. keys
    without quotes). This helper attempts to convert such strings into a form
    that can be parsed by ``json.loads`` by quoting keys and list items.
    """
    s = text.strip()
    # 1) Replace escaped quotes
    s = s.replace(r'\"', '"')

    # 2) Quote bare keys (key: → "key":)
    s = re.sub(r'(\b\w+\b)\s*:', r'"\1":', s)

    # 3) Quote bare items in lists (e.g. [Warrant, ABC] → ["Warrant", "ABC"])
    def quote_list_items(m):
        inner = m.group(1)
        items = [x.strip() for x in inner.split(',') if x.strip() != '']
        fixed = []
        for x in items:
            # Already quoted, numeric, boolean, or null values are left as-is
            if re.fullmatch(r'"[^" ]*"', x) or re.fullmatch(r'[+-]?\d+(\.\d+)?([eE][+-]?\d+)?', x) \
               or x.lower() in ('true', 'false', 'null'):
                fixed.append(x)
            else:
                fixed.append(f'"{x}"')
        return ': [' + ', '.join(fixed) + ']'
    s = re.sub(r':\s*\[([^\]]*)\]', quote_list_items, s)

    # 4) Quote bare values following colons (avoid numbers/booleans/null/lists/dicts)
    s = re.sub(
        r':\s*(?!\[|\{|"|[+-]?\d|\btrue\b|\bfalse\b|\bnull\b)([A-Za-z_][A-Za-z0-9_.-]*)',
        r': "\1"', s
    )

    # 5) Parse as JSON
    return json.loads(s)


def getStockDetails(resp: list) -> list[dict]:
    """Convert a list of LongPort static info responses into formatted dictionaries."""
    temp = []
    for stock in resp:
        raw = str(stock).replace("SecurityStaticInfo ", "")
        resp_formated = force_to_dict(raw)
        formatted_data = translate_keys(resp_formated)
        temp.append(formatted_data)
    return temp


def translate_keys(data):
    """Recursively translate English keys in a dict/list to Chinese."""
    if isinstance(data, list):
        return [translate_keys(item) for item in data]
    elif isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            cn_key = KEY_MAP.get(k, k)
            if isinstance(v, (dict, list)):
                new_dict[cn_key] = translate_keys(v)
            else:
                new_dict[cn_key] = v
        return new_dict
    else:
        return data


__all__ = [
    "getBasicStatus",
    "force_to_dict",
    "getStockDetails",
    "translate_keys",
]