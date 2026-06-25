"""
fetch_weekly.py — 周度/月度外生指标采集
输出: data/weekly.json

字段对齐 PRD「外生关键指标」（表3）+ PROJECT_PLAN 数据字典。
设计原则：每个真实数据源的抓取都包在独立 try/except 中，
拿到真实值就用，拿不到自动回退到 FALLBACK 占位 —— 保证 CI 永远产出合法 JSON。
资源网/华通人/Clarkson 无公开 API，目前为 fallback；
布伦特原油尝试通过 AKShare 拉取真实现货价。
"""
import json, os
from datetime import datetime, timezone, timedelta

try:
    import akshare as ak
    AK_AVAILABLE = True
except ImportError:
    AK_AVAILABLE = False
    print("[WARN] akshare not installed, using fallback")

CST = timezone(timedelta(hours=8))
OUT = os.path.join(os.path.dirname(__file__), '..', 'data', 'weekly.json')

# 外生指标定义：(id, 中文名, 单位, 来源, 频度, fallback值, fallback变动)
EXO_FIELDS = [
    ('thermal_power_yoy', '火电生产同比增速',   '%',      '中电联',    '月(20日)',  3.5,    0.8),
    ('cement_yoy',        '水泥产量增速',       '%',      '华通人',    '月(20日)', -2.1,   -0.3),
    ('pig_iron_yoy',      '生铁产量增速',       '%',      '华通人',    '月(20日)',  1.8,    0.5),
    ('coke_export_yoy',   '焦炭出口量增速',     '%',      '华通人',    '月(20日)', -15.2,  -3.1),
    ('ammonia_yoy',       '合成氨产量增速',     '%',      '华通人',    '月(20日)',  4.2,    1.0),
    ('aus_bj_coal',       '澳大利亚BJ煤现货价',  'USD/吨', '资源网',    '月(20日)',  128.5,  2.3),
    ('brent_crude',       '布伦特原油现货价',    'USD/桶', 'Bloomberg', '周',        82.6,   1.4),
    ('qld_japan_freight', '昆士兰-日本海运费',   'USD/吨', 'Clarkson',  '周',        9.2,   -0.3),
    ('bdi',               '波罗的海干散货指数',  '点',     'Bloomberg', '周',        1842,   56),
]


def fetch_brent():
    """布伦特原油现货价：尝试 AKShare 英国布伦特原油历史行情。失败返回 None。"""
    try:
        df = ak.energy_oil_hist()  # 含布伦特/WTI 等原油历史价
        if df is None or df.empty:
            return None
        # 取最近两行计算最新价与变动
        col = [c for c in df.columns if '布伦特' in str(c) or 'brent' in str(c).lower()]
        if not col:
            return None
        s = df[col[0]].dropna()
        if len(s) < 2:
            return None
        latest, prev = float(s.iloc[-1]), float(s.iloc[-2])
        return round(latest, 2), round(latest - prev, 2)
    except Exception as e:
        print(f"  ✗ brent: {e}")
        return None


# 真实数据源接入点：id -> 抓取函数（返回 (value, change) 或 None）
REAL_SOURCES = {
    'brent_crude': fetch_brent,
    # TODO: 接入资源网（aus_bj_coal/价格类）、Clarkson（qld_japan_freight）、
    #       华通人（各产量增速）。无公开 API 时保持 fallback。
}


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    indicators = []
    got_real = False
    for fid, name, unit, source, freq, fb_val, fb_chg in EXO_FIELDS:
        value, change = fb_val, fb_chg
        if AK_AVAILABLE and fid in REAL_SOURCES:
            res = REAL_SOURCES[fid]()
            if res is not None:
                value, change = res
                got_real = True
                print(f"  ✓ {fid}: {value} ({change:+})")
        indicators.append({
            'id': fid, 'name': name, 'unit': unit,
            'src': source, 'freq': freq,
            'value': value, 'change': change,
        })
    result = {
        'updated_at': datetime.now(CST).isoformat(),
        'source': 'mixed' if got_real else 'fallback',
        'indicators': indicators,
    }
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✓ 写入 {OUT} ({len(indicators)} 项外生指标, source={result['source']})")


if __name__ == '__main__':
    main()
