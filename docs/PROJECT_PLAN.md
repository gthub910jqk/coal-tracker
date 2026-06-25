# 煤炭中观数据追踪系统 · 项目规划文档

**文档版本**：v1.0  
**日期**：2025年6月

---

## 1. 项目文件结构

```
coal-tracker/                        ← GitHub 仓库根目录
│
├── index.html                       ← 主应用（单文件，即 coal_tracker_v3.html）
│
├── data/                            ← 静态数据目录（GitHub Actions 写入）
│   ├── futures.json                 ← 期货行情快照（AKShare 每日更新）
│   ├── stocks.json                  ← 煤炭股行情快照（AKShare 每日更新）
│   ├── weekly.json                  ← 周度指标（价格/库存，每周一）
│   └── monthly.json                 ← 月度指标（产量/进出口，每月20日）
│
├── scripts/                         ← 数据采集脚本（本地/CI运行）
│   ├── fetch_futures.py             ← AKShare 期货行情采集
│   ├── fetch_stocks.py              ← AKShare 股票行情采集
│   ├── fetch_weekly.py              ← 周度指标采集（资源网）
│   └── requirements.txt             ← Python 依赖（akshare, pandas）
│
├── .github/
│   └── workflows/
│       ├── daily_market.yml         ← 每日9:30拉取期货+股票行情
│       └── weekly_data.yml          ← 每周一8:00更新周度数据
│
├── templates/
│   └── coal_tracker_import.csv      ← 批量导入CSV模板（随仓库分发）
│
├── docs/
│   ├── PRD.md                       ← 产品需求文档（本文件夹同级）
│   ├── PROJECT_PLAN.md              ← 本文件
│   └── DATA_DICTIONARY.md           ← 数据字典
│
└── README.md                        ← 项目说明 + 部署指南
```

---

## 2. 开发阶段规划

### Phase 1 · 当前完成（v3.0）

- [x] 10标签页完整UI
- [x] 东方财富API接入（期货+股票，含fallback）
- [x] IndexedDB 本地存储
- [x] CSV 批量导入（拖拽+预览+确认）
- [x] CSV模板下载 + 全量导出
- [x] 外生指标标签页（表3完整覆盖）
- [x] 动态投资信号计算
- [x] GitHub Pages 就绪（单文件）

### Phase 2 · 数据管线（v3.1）— 下一步

目标：通过 GitHub Actions 每日自动运行 AKShare 脚本，将数据写入 `data/` 目录，前端读取 JSON 文件展示真实历史数据。

**子任务**：

| 任务 | 文件 | 说明 |
|------|------|------|
| 2.1 | `scripts/fetch_futures.py` | AKShare 获取 ZC/J/JM 主力行情，输出 `data/futures.json` |
| 2.2 | `scripts/fetch_stocks.py` | AKShare 获取8只煤炭股，输出 `data/stocks.json` |
| 2.3 | `.github/workflows/daily_market.yml` | 工作日9:30触发，commit并push |
| 2.4 | `index.html` 前端改造 | 优先读取 `data/futures.json`，失败降级到API，再降级到模拟数据 |

**AKShare 期货接口**：
```python
import akshare as ak
# 期货实时行情
df = ak.futures_zh_realtime(symbol="ZC")   # 动力煤
df = ak.futures_zh_realtime(symbol="J")    # 焦炭
df = ak.futures_zh_realtime(symbol="JM")   # 焦煤

# 期货历史数据
df = ak.futures_main_sina(symbol="ZC0", start_date="20240101")
```

**AKShare 股票接口**：
```python
import akshare as ak
# A股实时行情
df = ak.stock_zh_a_spot_em()   # 全市场，按代码筛选
```

**`data/futures.json` 数据结构**：
```json
{
  "updated_at": "2025-06-10T09:35:00+08:00",
  "source": "akshare",
  "contracts": [
    {
      "sym": "ZC2509",
      "name": "动力煤2509",
      "ex": "zce",
      "price": 786.0,
      "chg": 12.0,
      "pct": 1.55,
      "vol": 182400,
      "oi": 856000,
      "settle": 774.0
    }
  ]
}
```

**`data/stocks.json` 数据结构**：
```json
{
  "updated_at": "2025-06-10T15:05:00+08:00",
  "source": "akshare",
  "stocks": [
    {
      "code": "601088",
      "name": "中国神华",
      "price": 38.42,
      "chg": 0.52,
      "pct": 1.37,
      "volume": 1240000,
      "market_cap": 824000000000
    }
  ]
}
```

### Phase 3 · 手机端适配（v3.2）

| 任务 | 说明 |
|------|------|
| 3.1 | 响应式网格（`grid-template-columns` 在窄屏 < 768px 改为1列） |
| 3.2 | 导航标签横向滚动优化（已部分实现） |
| 3.3 | 图表在小屏的 `height` 自适应 |
| 3.4 | 录入表单在手机上的键盘类型（`inputmode="decimal"`） |

### Phase 4 · 多品种扩展（v4.0）

- 铁矿石（I）、螺纹钢（RB）、甲醇（MA）标签页
- 跨品种比价（黑色系产业链利润）
- 数据框架泛化（品种配置化）

---

## 3. GitHub Actions 工作流设计

### `daily_market.yml`

```yaml
name: Daily Market Data

on:
  schedule:
    - cron: '30 1 * * 1-5'   # 北京时间 9:30（UTC+8 = UTC 01:30）
  workflow_dispatch:           # 手动触发

jobs:
  fetch:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          
      - run: pip install -r scripts/requirements.txt
      
      - name: Fetch futures
        run: python scripts/fetch_futures.py
        
      - name: Fetch stocks
        run: python scripts/fetch_stocks.py
        
      - name: Commit data
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add data/
          git diff --staged --quiet || git commit -m "data: auto-update $(date -u +%Y-%m-%dT%H:%M:%SZ)"
          git push
```

### `weekly_data.yml`

```yaml
name: Weekly Indicator Data

on:
  schedule:
    - cron: '0 2 * * 1'      # 每周一北京时间 10:00
  workflow_dispatch:

jobs:
  fetch:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r scripts/requirements.txt
      - run: python scripts/fetch_weekly.py
      - name: Commit weekly data
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add data/weekly.json
          git diff --staged --quiet || git commit -m "data: weekly update $(date -u +%Y-%m-%dT%H:%M:%SZ)"
          git push
```

---

## 4. 前端数据加载策略（三级降级）

```
1. 优先：读取 /data/futures.json（GitHub Actions 写入，最新收盘数据）
      ↓ 失败（文件不存在 / 超时）
2. 降级：调用 push2.eastmoney.com 实时行情 API
      ↓ 失败（API限流 / CORS / 非交易时段）
3. 兜底：内置模拟数据（上一已知行情）
```

---

## 5. 数据字典（核心字段）

| 字段 | 中文 | 类型 | 单位 | 来源 | 频度 |
|------|------|------|------|------|------|
| qhd_price | 秦皇岛港混煤平仓价 | float | 元/吨 | 资源网 | 周 |
| coking_price | 山西古交2#焦煤 | float | 元/吨 | 资源网 | 周 |
| coke_price | 山西太原一级焦炭 | float | 元/吨 | 资源网 | 周 |
| port_inventory | 秦皇岛港口库存 | float | 万吨 | 资源网 | 周 |
| power_consumption | 六大电厂日耗 | float | 万吨 | 煤炭网 | 日 |
| raw_production | 全国原煤产量 | float | 万吨 | 煤炭网 | 月 |
| coal_import | 进口煤总量 | float | 万吨 | 海关总署 | 月 |
| rebar_price | 螺纹钢价格 | float | 元/吨 | 市场 | 周 |
| thermal_power_yoy | 火电产量同比增速 | float | % | 华通人 | 月 |
| cement_yoy | 水泥产量增速 | float | % | 华通人 | 月 |
| pig_iron_yoy | 生铁产量增速 | float | % | 华通人 | 月 |
| coke_export_yoy | 焦炭出口量增速 | float | % | 华通人 | 月 |
| ammonia_yoy | 合成氨产量增速 | float | % | 华通人 | 月 |
| aus_bj_coal | 澳煤BJ现货价 | float | USD/吨 | 资源网/Bloomberg | 周 |
| brent_crude | 布伦特原油 | float | USD/桶 | 资源网 | 周 |
| qld_japan_freight | 昆士兰-日本海运费 | float | USD/吨 | Clarkson | 周 |
| bdi | 波罗的海干散货指数 | int | 点 | Bloomberg | 周 |

---

## 6. 部署检查清单

```
GitHub Pages 部署前检查：

□ index.html 为完整独立文件（无外部本地依赖）
□ CDN 资源均使用 https://
□ 不含任何 API 密钥或敏感信息
□ data/ 目录存在（即使为空）
□ README.md 包含数据更新说明
□ GitHub Actions 权限：Settings → Actions → Read and write permissions ✓
□ Pages 设置：Settings → Pages → Source: Deploy from branch → main → / (root)
```

---

## 7. 本地开发环境

```bash
# 克隆仓库
git clone https://github.com/用户名/coal-tracker.git
cd coal-tracker

# 本地预览（避免 file:// 协议 CORS 问题）
python3 -m http.server 8080
# 浏览器访问 http://localhost:8080

# Python 数据脚本依赖
pip install akshare pandas requests

# 手动运行数据更新
python scripts/fetch_futures.py
python scripts/fetch_stocks.py
```

