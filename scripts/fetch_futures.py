"""
fetch_futures.py — AKShare 期货行情采集
输出: data/futures.json
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
OUT = os.path.join(os.path.dirname(__file__), '..', 'data', 'futures.json')

VARIETIES = [
    ('ZC', '动力煤', 'zce'),
    ('J',  '焦炭',   'dce'),
    ('JM', '焦煤',   'dce'),
]

def fetch():
    results = []
    for sym, cn_name, ex in VARIETIES:
        try:
            df = ak.futures_zh_realtime(symbol=cn_name)
            if df is None or df.empty:
                print(f"  ⚠ {sym} ({cn_name}): empty result")
                continue
            main = df.sort_values('position', ascending=False).iloc[0]
            trade = float(main.get('trade', 0) or 0)
            prev  = float(main.get('prevsettlement', 0) or 0)
            results.append({
                'sym':    str(main.get('symbol', sym)),
                'name':   f'{cn_name}主力',
                'ex':     ex,
                'price':  trade,
                'chg':    trade - prev,
                'pct':    float(main.get('changepercent', 0) or 0),
                'vol':    int(main.get('volume', 0) or 0),
                'oi':     int(main.get('position', 0) or 0),
                'settle': float(main.get('settlement', 0) or 0),
            })
            print(f"  ✓ {sym}: {trade}")
        except Exception as e:
            print(f"  ✗ {sym} ({cn_name}): {type(e).__name__}: {e}")
            traceback.print_exc()
    return results

FALLBACK = [
    {'sym':'ZC2509','name':'动力煤2509','ex':'zce','price':786,'chg':12,'pct':1.55,'vol':182400,'oi':856000,'settle':774},
    {'sym':'ZC2511','name':'动力煤2511','ex':'zce','price':778,'chg':8,'pct':1.04,'vol':42100,'oi':210000,'settle':770},
    {'sym':'J2509', 'name':'焦炭2509',  'ex':'dce','price':1816,'chg':-28,'pct':-1.52,'vol':224000,'oi':1020000,'settle':1844},
    {'sym':'J2511', 'name':'焦炭2511',  'ex':'dce','price':1798,'chg':-18,'pct':-0.99,'vol':68000,'oi':380000,'settle':1816},
    {'sym':'JM2509','name':'焦煤2509',  'ex':'dce','price':1294,'chg':-14,'pct':-1.07,'vol':196000,'oi':880000,'settle':1308},
    {'sym':'JM2511','name':'焦煤2511',  'ex':'dce','price':1280,'chg':-8,'pct':-0.62,'vol':54000,'oi':320000,'settle':1288},
]

def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    contracts = fetch() if AK_AVAILABLE else []
    result = {
        'updated_at': datetime.now(CST).isoformat(),
        'source': 'akshare' if contracts else 'fallback',
        'contracts': contracts if contracts else FALLBACK,
    }
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✓ 写入 {OUT} ({len(result['contracts'])} 合约)")

if __name__ == '__main__':
    main()
