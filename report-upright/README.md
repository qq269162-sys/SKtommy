# Upright Growth Fund (UPUPX) — 27 年持仓与规模档案

**Upright Growth Fund**（SEC CIK `1058587`，Upright Investments Trust 旗下，经理 David Y.S. Chiueh）
自 1999 年 1 月 21 日成立至 FY2025 的完整记录，全部解析自 SEC EDGAR 原始申报。

财年末为每年 **9 月 30 日**。

## 数据来源

| 内容 | 期间 | 表单 |
|---|---|---|
| 逐笔持仓 | FY2003–FY2025 | `N-CSR` 年报中的 Schedule of Investments / Statement of Investment in Securities（23 份） |
| 净资产、年度回报 | FY1999–FY2002 | FY2003 年报 Financial Highlights 的五年栏 |
| 交叉校验 | FY2021 / FY2023 / FY2024 | `NPORT-P` |

## 数据文件

| 文件 | 内容 |
|---|---|
| `data-upright/fund_summary.csv` | 逐年净资产、总回报、隐含净申赎、$10,000 成长值、个股/ETF/现金占比、持股只数、集中度 |
| `data-upright/top10_by_year.csv` | FY2003–FY2025 每年前十大个股 |
| `data-upright/holdings_all_years.csv` | 850+ 条逐笔持仓（申报原名、合并后名称、类型、行业、股数、市值、占比） |

## 复现

```bash
python3 scripts-upright/uextract.py   # 解析 N-CSR → up_ncsr.json
python3 scripts-upright/uperf.py      # 回报、现金比例、份额、NAV → up_perf.json
python3 scripts-upright/ubuild.py     # 合并全序列 → up_all.json
python3 scripts-upright/ufinal.py     # 输出 CSV 与报告页 payload
node    scripts-upright/render_pdf.mjs
```

脚本需先把 EDGAR 文件下载到 `ncsr/`、`nport/` 目录。

## 口径与校验

- **三只基金**：FY2018 起该信托旗下有 UPUPX、UPDDX、UPAAX 三只基金，年报合并报送。
  解析器按每份 Schedule 前的基金名归属，只统计 **Upright Growth Fund**。
- **净资产**以每份年报自报的 Net Assets 为准。FY2021 `$24,978,640`、FY2023 `$17,403,368`
  与 N-PORT 完全一致；FY2023 逐笔持仓也与同日 N-PORT 逐项吻合
  （Himax 24.87%、Apple 24.40%、TSMC 8.49%）。
- **回报率**取自各年报 Financial Highlights 的 Total Return 行；相邻年报重叠年份全部逐年对齐。
- **隐含净申赎**为推算值：`NA_t − NA_{t−1} × (1 + r_t)`，未考虑年内申赎时点。
- **合并**：同一公司不同写法合并为一个名称；持仓分为个股 / ETF / 现金与货币基金三类，
  集中度与前十大只计个股。

## 报告

`report-upright/index.html`（单页报告）与 `report-upright/upupx-1999-2025.pdf`（8 页 A4）。
