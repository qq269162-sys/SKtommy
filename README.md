# Nomura (ex-Delaware / Macquarie) Emerging Markets Fund — 19 年持仓档案

把 **Delaware Emerging Markets Fund → Macquarie Emerging Markets Fund → Nomura Emerging Markets Fund**
（SEC CIK `875610`，基金经理 Liu-Er Chen，2006 年 9 月至今）FY2007–FY2025 的逐年持仓，
从 SEC EDGAR 原始申报文件中解析出来，整理成可分析的数据集。

财年末为每年 **11 月 30 日**。

## 数据来源

| 期间 | 表单 | 说明 |
|---|---|---|
| FY2007–FY2018 | `N-CSR` | 年报中的 *Statement of net assets* / *Schedule of investments*（HTML 表格解析） |
| FY2019–FY2025 | `NPORT-P` | 结构化 XML 持仓明细，含 `pctVal` |

## 数据文件

| 文件 | 内容 |
|---|---|
| `data/top10_by_year.csv` | 每个财年的前十大持仓（发行人、占净资产、市值） |
| `data/holdings_all_years.csv` | 全部 2,500+ 条逐仓记录（申报原名、合并后发行人、股数、市值、占比、国别） |
| `data/country_weights.csv` | 逐年国别权重 |
| `data/fund_summary.csv` | 逐年净资产、发行人个数、前一/前五/前十集中度、HHI、韩台权重、中港权重、半导体权重 |

## 复现

```bash
python3 scripts/extract.py   # 解析 N-CSR HTML → ncsr_em.json
python3 scripts/build.py     # 合并 N-CSR + N-PORT，按发行人归一化 → all_rows.json
python3 scripts/final.py     # 输出 data/*.csv
python3 scripts/payload.py   # 输出报告页所需的 payload.json
```

脚本需要先把 EDGAR 申报文件下载到 `ncsr/` 与 `nport/` 目录下（见 `scripts/extract.py` 顶部说明）。

## 口径与校验

- **按发行人合并**：同一公司的普通股／优先股／ADR／GDR 合并为一个名字
  （如 Samsung Electronics 普通股 + 优先股，Reliance Industries 本地股 + GDR）。
  因此这里的数字可能高于年报中单行的数值。
- **已剔除**：证券出借抵押品、贴现票据、回购协议等非权益头寸，以及已归零的 Lehman LEPO 权证。
- **交叉校验**：FY2019 同时有 N-CSR 与 N-PORT 两个来源，解析结果的前十二大持仓逐项一致
  （5.79 / 5.61 / 5.07 / 4.78 / 4.47 / 3.76 / 3.67 / 3.49 / 3.05 / 2.91 / 2.48 / 2.32）。
  各年解析出的证券合计占净资产 96.7%–104.0%，与年报自报的 *Total Value of Securities* 吻合。
- **国别**沿用基金年报自己的 *country of risk* 分类。

## 报告页

`report/index.html` 是自带图表与演变分析的单页报告（集中度曲线、持仓迁移热力图、
国别堆叠面积图、半导体权重、逐年前十大持仓表）。
