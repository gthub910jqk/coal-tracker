"""
fetch_stocks.py — 煤炭股行情采集
主路径: 新浪 hq.sinajs.cn（轻量、海外友好）
备用:   AKShare stock_zh_a_spot_em（提供 PE/PB/市值）
输出:   data/stocks.json
"""
import json, os, re, traceback
from datetime import datetime, timezone, timedelta

import requests

try:
    import akshare as ak
    AK_AVAILABLE = True
    print(f"[INFO] akshare {getattr(ak, '__version__', '?')}")
except ImportError:
    AK_AVAILABLE = False
    print("[WARN] akshare not installed")

CST = timezone(timedelta(hours=8))
OUT = os.path.join(os.path.dirname(__file__), '..', 'data', 'stocks.json')

TARGETS = {
    '601088': {'name': '中国神华', 'sector': 'thermal', 'market': 'sh'},
    '601225': {'name': '陕西煤业', 'sector': 'thermal', 'market': 'sh'},
    '601898': {'name': '中煤能源', 'sector': 'mixed',   'market': 'sh'},
    '600546': {'name': '山煤国际', 'sector': 'thermal', 'market': 'sh'},
    '601666': {'name': '平煤股份', 'sector': 'coking',  'market': 'sh'},
    '600985': {'name': '淮北矿业', 'sector': 'coking',  'market': 'sh'},
    '600188': {'name': '兖矿能源', 'sector': 'mixed',   'market': 'sh'},
    '000937': {'name': '冀中能源', 'sector': 'coking',  'market': 'sz'},
}

FALLBACK_PRICES = {
    '601088': 38.42, '601225': 24.16, '601898': 11.28, '600546': 16.42,
    '601666': 9.84,  '600985': 22.56, '600188': 31.20, '000937': 8.62,
}

SINA_URL = "https://hq.sinajs.cn/list={symbols}"
SINA_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://finance.sina.com.cn",
}


def fetch_via_sina():
    """
    从新浪行情拉 8 只煤炭股。
    返回 list[dict]，失败返回 []。
    sina 不提供 PE/PB/市值，对应字段填 0。
    """
    symbols = ",".join(f"{info['market']}{code}" for code, info in TARGETS.items())
    url = SINA_URL.format(symbols=symbols)
    try:
        resp = requests.get(url, headers=SINA_HEADERS, timeout=10)
        resp.encoding = "gbk"
        text = resp.text
    except Exception as e:
        print(f"  ✗ sina request: {type(e).__name__}: {e}")
        return []

    results = []
    for code, info in TARGETS.items():
        symbol = f"{info['market']}{code}"
        m = re.search(rf'hq_str_{symbol}="([^"]*)"', text)
        if not m or not m.group(1):
            print(f"  ⚠ {symbol}: 无数据（停牌/退市/接口未返回）")
            continue
        parts = m.group(1).split(",")
        if len(parts) < 10:
            print(f"  ⚠ {symbol}: 字段数异常 ({len(parts)})")
            continue
        try:
            prev_close = float(parts[2])
            price = float(parts[3])
            volume = int(parts[8])           # 股
            amount = float(parts[9])          # 元
            chg = price - prev_close
            pct = (chg / prev_close * 100) if prev_close else 0.0
            results.append({
                'code': code,
                'name': info['name'],
                'sector': info['sector'],
                'market': info['market'],
                'price': price,
                'chg': round(chg, 4),
                'pct': round(pct, 4),
                'volume': volume,
                'amount': amount,
                # sina 轻量接口不提供，留 0 由前端兜底
                'market_cap': 0.0,
                'pe': 0.0,
                'pb': 0.0,
            })
            print(f"  ✓ {info['name']}: {price} ({pct:+.2f}%)")
        except (ValueError, IndexError) as e:
            print(f"  ✗ {symbol} 解析: {type(e).__name__}: {e}")
    return results


def fetch_via_akshare():
    """AKShare 全市场快照，过滤 8 只。GitHub 海外 runner 上历史失败，保留作本地/国内 runner 备用。"""
    if not AK_AVAILABLE:
        return []
    try:
        df = ak.stock_zh_a_spot_em()
        results = []
        for code, info in TARGETS.items():
            row = df[df['代码'] == code]
            if row.empty:
                continue
            r = row.iloc[0]
            results.append({
                'code': code,
                'name': info['name'],
                'sector': info['sector'],
                'market': info['market'],
                'price':  float(r.get('最新价', 0) or 0),
                'chg':    float(r.get('涨跌额', 0) or 0),
                'pct':    float(r.get('涨跌幅', 0) or 0),
                'volume': int(r.get('成交量', 0) or 0),
                'amount': float(r.get('成交额', 0) or 0),
                'market_cap': float(r.get('总市值', 0) or 0),
                'pe':     float(r.get('市盈率-动态', 0) or 0),
                'pb':     float(r.get('市净率', 0) or 0),
            })
            print(f"  ✓ {info['name']}: {r.get('最新价')}")
        return results
    except Exception as e:
        print(f"  ✗ akshare: {type(e).__name__}: {e}")
        traceback.print_exc()
        return []


def make_fallback():
    return [{
        'code': c, 'name': i['name'], 'sector': i['sector'], 'market': i['market'],
        'price': FALLBACK_PRICES.get(c, 20), 'chg': 0, 'pct': 0,
        'volume': 0, 'amount': 0, 'market_cap': 0, 'pe': 10.0, 'pb': 1.5,
    } for c, i in TARGETS.items()]


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)

    print("[1/2] 尝试新浪行情...")
    stocks = fetch_via_sina()
    source = 'sina'

    if not stocks:
        print("[2/2] 新浪失败，回退 AKShare...")
        stocks = fetch_via_akshare()
        source = 'akshare' if stocks else 'fallback'

    if not stocks:
        print("[fallback] 两路均失败，使用内置占位数据")
        stocks = make_fallback()

    result = {
        'updated_at': datetime.now(CST).isoformat(),
        'source': source,
        'stocks': stocks,
    }
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✓ 写入 {OUT} ({len(result['stocks'])} 只 source={source})")


if __name__ == '__main__':
    main()
