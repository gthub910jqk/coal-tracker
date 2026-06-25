# 煤炭中观数据追踪系统

> 基于《表3：策略跟踪的煤炭中观数据库》构建的单文件 Web 应用，部署于 GitHub Pages，零服务器成本。

[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-部署中-green)](https://用户名.github.io/coal-tracker/)
![版本](https://img.shields.io/badge/版本-v3.0-orange)
![数据源](https://img.shields.io/badge/行情-东方财富API-blue)

---

## 功能概览

| 标签页 | 功能 |
|--------|------|
| 总览 | KPI卡片 + 供需简表 + 价格走势图 |
| 供给端 | 产量/进口/开工率完整表 |
| 需求端 | 日耗/高炉/发电量完整表 |
| 库存端 | 港口/电厂/钢厂库存 + 走势图 |
| **外生指标** | 火电/水泥/生铁/布伦特/海运费等（表3外生类） |
| 比价关系 | 焦炭焦煤比价、焦化利润、进口价差 |
| **期货行情** | ZC/J/JM实时行情（东方财富API） |
| **上市公司** | 8只煤炭A股实时行情 + 估值对比 |
| **数据录入** | 手动录入 + CSV批量导入 + 导出 |
| 投资信号 | 动态打分 + 综合研判 |

---

## 快速开始

### 方式一：直接使用（推荐）

访问 [GitHub Pages 链接](https://用户名.github.io/coal-tracker/) 即可，无需安装。

### 方式二：本地运行

```bash
git clone https://github.com/用户名/coal-tracker.git
cd coal-tracker
python3 -m http.server 8080
# 浏览器访问 http://localhost:8080
```

---

## 数据录入

### 手动录入

在「数据录入」标签页填入各指标数值，点击「保存数据」，存储于浏览器 IndexedDB。

### CSV 批量导入

1. 点击「下载CSV模板」获取模板文件
2. 填写数据（支持中英文列名）
3. 拖拽或选择 CSV 文件到导入区域
4. 确认预览后导入

**CSV 列名对照**：

| 英文列名 | 中文列名 | 说明 |
|----------|----------|------|
| `date` | `日期` | YYYY-MM-DD |
| `qhd_price` | `动力煤` | 秦皇岛港，元/吨 |
| `coking_price` | `炼焦煤` | 山西古交2#，元/吨 |
| `coke_price` | `焦炭` | 山西太原一级，元/吨 |
| `port_inventory` | `港口库存` | 秦皇岛，万吨 |
| `power_consumption` | `电厂日耗` | 六大电厂，万吨 |
| `raw_production` | `原煤产量` | 全国，万吨/月 |
| `coal_import` | `进口煤` | 总量，万吨/月 |
| `rebar_price` | `螺纹钢` | 元/吨 |

---

## 行情数据说明

- **来源**：东方财富 push2 接口（无需 API Key，浏览器直调）
- **频率**：启动时自动加载，每5分钟自动刷新
- **降级**：API 不可用时自动切换模拟数据，顶部徽章从「实时」变为「SAMPLE」
- **交易时间**：工作日 9:00-15:00，非交易时段显示上一交易日收盘价

---

## 部署到 GitHub Pages

```bash
# 1. Fork 本仓库，或创建新仓库并上传 index.html
# 2. 仓库 Settings → Pages
# 3. Source: Deploy from a branch
# 4. Branch: main / (root)
# 5. Save → 等待约1分钟部署完成
```

> **注意**：启用 GitHub Actions 自动数据更新需在 Settings → Actions → General → Workflow permissions 选择「Read and write permissions」

---

## 数据更新周期（自动化，Phase 2）

| 数据类型 | 更新时间 | Actions 工作流 |
|----------|----------|----------------|
| 期货/股票行情 | 工作日 9:30 | `daily_market.yml` |
| 周度指标（价格/库存）| 每周一 10:00 | `weekly_data.yml` |

---

## 技术栈

- **前端**：纯 HTML/CSS/JavaScript（单文件）
- **图表**：Chart.js 4.4.1
- **字体**：JetBrains Mono + Noto Sans SC
- **存储**：IndexedDB
- **行情**：东方财富 push2 API
- **数据管线**：AKShare（Python）+ GitHub Actions

---

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v3.0 | 2025-06 | 行情API接入、CSV批量导入、外生指标标签页、IndexedDB |
| v2.0 | 2025-05 | 9标签页原型、Chart.js图表、模拟数据 |

