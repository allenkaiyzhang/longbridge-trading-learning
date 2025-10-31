# 获取标的基础信息以及标准化
# https://open.longportapp.com/docs/quote/pull/static
# 运行前请访问“开发者中心”确保账户有正确的行情权限。
# 如没有开通行情权限，可以通过“LongPort”手机客户端，并进入“我的 - 我的行情 - 行情商城”购买开通行情权限。
from longport.openapi import QuoteContext, Config
import json,re

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
    "board": "标的所属板块"
}


#获取response
def getBasicStatus(symbol):
    config = Config.from_env()
    ctx = QuoteContext(config)
    resp = ctx.static_info(symbol)
    return resp

#强制转换各个response内容为dict类型
def force_to_dict(text: str):
    s = text.strip()
    # 1) 去掉 \" 转义
    s = s.replace(r'\"', '"')

    # 2) 给 key 补引号：key: → "key":
    s = re.sub(r'(\b\w+\b)\s*:', r'"\1":', s)

    # 3) 处理方括号中的裸标识符（如 [Warrant, ABC] → ["Warrant", "ABC"]）
    def quote_list_items(m):
        inner = m.group(1)
        items = [x.strip() for x in inner.split(',') if x.strip() != '']
        fixed = []
        for x in items:
            # 已带引号/数字/布尔/空 直接保留，否则补引号
            if re.fullmatch(r'"[^"]*"', x) or re.fullmatch(r'[+-]?\d+(\.\d+)?([eE][+-]?\d+)?', x) \
               or x.lower() in ('true','false','null'):
                fixed.append(x)
            else:
                fixed.append(f'"{x}"')
        return ': [' + ', '.join(fixed) + ']'
    s = re.sub(r':\s*\[([^\]]*)\]', quote_list_items, s)

    # 4) 给冒号后的“裸标识符值”补引号（避免影响数字/布尔/空/null/已加引号/数组/对象）
    s = re.sub(
        r':\s*(?!\[|\{|"|[+-]?\d|\btrue\b|\bfalse\b|\bnull\b)([A-Za-z_][A-Za-z0-9_.-]*)',
        r': "\1"', s
    )

    # 5) 现在应是合法 JSON，解析
    return json.loads(s)


def getStockDetails(resp:list):
    temp=[]
    for stock in resp:
        raw=str(stock).replace("SecurityStaticInfo ","")
        resp_formated=force_to_dict(raw)
        formattedData=translate_keys(resp_formated)
        temp.append(formattedData)
    return temp

def translate_keys(data):
    """将dict或list[dict]的英文键替换为中文描述"""
    if isinstance(data, list):
        return [translate_keys(item) for item in data]
    elif isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            cn_key = KEY_MAP.get(k, k)  # 若未匹配到保持原样
            if isinstance(v, dict) or isinstance(v, list):
                new_dict[cn_key] = translate_keys(v)
            else:
                new_dict[cn_key] = v
        return new_dict
    else:
        return data

def getPrompt(symbol):
    response=getBasicStatus(savedList)
    details=getStockDetails(response)
    return details


# 验证 & 漂亮打印（避免中文变 \uXXXX）
response=getBasicStatus(["US.HSBC"])

