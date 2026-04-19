# -*- coding: utf-8 -*-
"""
===================================
美股指数与股票代码工具
===================================

提供：
1. 美股指数代码映射（如 SPX -> ^GSPC）
2. 美股股票代码识别（AAPL、TSLA 等）

美股指数在 Yahoo Finance 中需使用 ^ 前缀，与股票代码不同。
"""

import re

# 美股代码正则：1-5 个大写字母，可选 .X 后缀（如 BRK.B）
_US_STOCK_PATTERN = re.compile(r'^[A-Z]{1,5}(\.[A-Z])?$')


# 用户输入 -> (Yahoo Finance 符号, 中文名称)
US_INDEX_MAPPING = {
    # 标普 500
    'SPX': ('^GSPC', '标普500指数'),
    '^GSPC': ('^GSPC', '标普500指数'),
    'GSPC': ('^GSPC', '标普500指数'),
    # 道琼斯工业平均指数
    'DJI': ('^DJI', '道琼斯工业指数'),
    '^DJI': ('^DJI', '道琼斯工业指数'),
    'DJIA': ('^DJI', '道琼斯工业指数'),
    # 纳斯达克综合指数
    'IXIC': ('^IXIC', '纳斯达克综合指数'),
    '^IXIC': ('^IXIC', '纳斯达克综合指数'),
    'NASDAQ': ('^IXIC', '纳斯达克综合指数'),
    # 纳斯达克 100
    'NDX': ('^NDX', '纳斯达克100指数'),
    '^NDX': ('^NDX', '纳斯达克100指数'),
    # VIX 波动率指数
    'VIX': ('^VIX', 'VIX恐慌指数'),
    '^VIX': ('^VIX', 'VIX恐慌指数'),
    # 罗素 2000
    'RUT': ('^RUT', '罗素2000指数'),
    '^RUT': ('^RUT', '罗素2000指数'),
}


def is_us_index_code(code: str) -> bool:
    """判断代码是否为美股指数符号（SPX, DJI 等）。"""
    return (code or '').strip().upper() in US_INDEX_MAPPING


def is_us_stock_code(code: str) -> bool:
    """
    判断代码是否为美股股票符号（排除美股指数）。

    美股股票代码为 1-5 个大写字母，可选 .X 后缀如 BRK.B。
    """
    normalized = (code or '').strip().upper()
    if normalized in US_INDEX_MAPPING:
        return False
    return bool(_US_STOCK_PATTERN.match(normalized))


def get_us_index_yf_symbol(code: str) -> tuple:
    """
    获取美股指数的 Yahoo Finance 符号与中文名称。

    Returns:
        (yf_symbol, chinese_name) 元组，未找到时返回 (None, None)。
    """
    normalized = (code or '').strip().upper()
    return US_INDEX_MAPPING.get(normalized, (None, None))
