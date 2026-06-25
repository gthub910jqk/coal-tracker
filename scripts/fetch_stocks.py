"""
fetch_stocks.py — AKShare 煤炭股行情采集
输出: data/stocks.json
"""
import json, os, traceback
from datetime import datetime, timezone, timedelta

try:
    import akshare as ak
    AK_AVAILABLE = True
    print(f"[INFO] akshare {getattr(ak, '__version__', '?')}")
except ImportError:
    AK_AVAILABLE = False
    print("[WARN] akshare not installed, using fallback")

CST = timezone(timedelta(hours=8))
OUT = os.path.join(os.path.dirname(__file__), '..', 'data', 'stocks.json')

TARGETS = {
    '601088':{'name':'中国神华','sector':'thermal','market':'sh'},
    '601225':{'name':'陕西煤业','sector':'thermal','market':'sh'},
    '601898':{'name':'中煤能源','sector':'mixed',  'market':'sh'},
    '600546':{'name':'山煤国际','sector':'thermal','market':'sh'},
    '601666':{'name':'平煤股份','sector':'coking', 'market':'sh'},
    '600985':{'name':'淮北矿业','sector':'coking', 'market':'sh'},
    '600188':{'name':'兖矿能源','sector':'mixed',  'market':'sh'},
    '000937':{'name':'冀中能源','sector':'coking', 'market':'sz'},
}

FALLBACK_PRICES = {
    '601088':38.42,'601225':24.16,'601898':11.28,'600546':16.42,
    '601666':9.84, '600985':22.56,'600188':31.20,'000937':8.62,
}

def fetch():
    try:
        df = ak.stock_zh_a_spot_em()
        results = []
        for code, info in TARGETS.items():
            row = df[df['代码'] == code]
            if row.empty: continue
            r = row.iloc[0]
            results.append({
                'code':   code,
                'name':   info['name'],
                'sector': info['sector'],
                'market': info['market'],
                'price':  float(r.get('最新价', 0)),
                'chg':    float(r.get('涨跌额', 0)),
                'pct':    float(r.get('涨跌幅', 0)),
                'volume': int(r.get('成交量', 0)),
                'amount': float(r.get('成交额', 0)),
                'market_cap': float(r.get('总市值', 0)),
                'pe':     float(r.get('市盈率-动态', 0)),
                'pb':     float(r.get('市净率', 0)),
            })
            print(f"  ✓ {info['name']}: {r.get('最新价')}")
        return results
    except Exception as e:
        print(f"  ✗ {type(e).__name__}: {e}")
        traceback.print_exc()
        return []

def make_fallback():
    return [{'code':c,'name':i['name'],'sector':i['sector'],'market':i['market'],
             'price':FALLBACK_PRICES.get(c,20),'chg':0,'pct':0,'volume':0,'amount':0,
             'market_cap':0,'pe':10.0,'pb':1.5} for c,i in TARGETS.items()]

def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    stocks = fetch() if AK_AVAILABLE else []
    result = {
        'updated_at': datetime.now(CST).isoformat(),
        'source': 'akshare' if stocks else 'fallback',
        'stocks': stocks if stocks else make_fallback(),
    }
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✓ 写入 {OUT} ({len(result['stocks'])} 只)")

if __name__ == '__main__':
    main()
