"""
SK Square vs SK Hynix 折价动态可视化
持股关系: SK Square 持有 SK 海力士约 20.07% 股份
折价率 = 1 - SK Square市值 / (SK Hynix持仓市值 + SK Square其他净资产)

用法:
  python sk_discount_viz.py           # 自动获取实时数据（需 Yahoo Finance 访问权限）
  python sk_discount_viz.py --demo    # 使用演示数据（离线可用）
"""

import sys
import warnings
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

warnings.filterwarnings("ignore")

# ── 常量 ──────────────────────────────────────────────────────────────────────
SK_HYNIX_TICKER    = "000660.KS"
SK_SQUARE_TICKER   = "402340.KS"

SK_HYNIX_TOTAL_SHARES  = 728_002_365
SK_SQUARE_TOTAL_SHARES =  71_674_000
SK_SQUARE_HYNIX_STAKE  = 0.2007

SK_SQUARE_HYNIX_SHARES = int(SK_HYNIX_TOTAL_SHARES * SK_SQUARE_HYNIX_STAKE)
OTHER_NET_ASSETS_KRW   = 2_500_000_000_000   # SK Square 기타 순자산 추정 2.5조 원

PERIOD = "2y"


# ── 데이터 취득 ───────────────────────────────────────────────────────────────

def fetch_prices_yfinance() -> pd.DataFrame:
    import yfinance as yf
    print("正在从 Yahoo Finance 获取数据...")
    hynix  = yf.download(SK_HYNIX_TICKER,  period=PERIOD, progress=False, auto_adjust=True)["Close"]
    square = yf.download(SK_SQUARE_TICKER, period=PERIOD, progress=False, auto_adjust=True)["Close"]
    df = pd.DataFrame({"hynix": hynix.astype(float), "square": square.astype(float)}).dropna()
    df.index = pd.to_datetime(df.index)
    df.index.name = "date"
    return df


def fetch_prices_krx() -> pd.DataFrame:
    """KRX(한국거래소) 공식 API 시도"""
    import requests, json
    from datetime import datetime, timedelta

    end   = datetime.today()
    start = end - timedelta(days=730)

    results = {}
    for name, isin in [("hynix", "KR7000660001"), ("square", "KR7402340001")]:
        url = "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
        payload = {
            "bld": "dbms/MDC/STAT/standard/MDCSTAT01701",
            "isuCd": isin,
            "strtDd": start.strftime("%Y%m%d"),
            "endDd":  end.strftime("%Y%m%d"),
            "adjStkPrc_check": "Y",
        }
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "http://data.krx.co.kr/",
        }
        r = requests.post(url, data=payload, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()["output"]
        series = {
            pd.Timestamp(row["TRD_DD"].replace("/", "-")): int(row["TDD_CLSPRC"].replace(",", ""))
            for row in data
        }
        results[name] = pd.Series(series)

    df = pd.DataFrame(results).sort_index().dropna()
    df.index.name = "date"
    return df


def make_demo_prices() -> pd.DataFrame:
    """
    演示价格数据（2024-01 → 2026-05-20），关键锚点来自用户提供的实际市价：
      2026-05-20: SK海力士 ~1,750,000 KRW  /  SK Square ~1,020,000 KRW

    历史轨迹估算（AI/HBM 内存超级周期驱动的大牛市）:
      SK海力士: 2024年约133k→230k，2025年随AI算力需求持续飙升，2026年初达175万
      SK Square: 跟随上涨但涨幅较小，折价率在70-84%区间波动
    """
    print("⚠  网络受限，使用演示数据（锚点: 海力士175万 / Square102万，数据至2026-05-20）")
    rng = np.random.default_rng(42)

    dates = pd.bdate_range(start="2024-01-02", end="2026-05-20")
    n = len(dates)
    t = np.linspace(0, 1, n)

    # ── SK 해力士 关键节点 ──────────────────────────────────────────────────
    # t=0.00  2024-01  133,000  (已知)
    # t=0.29  2024-07  238,000  (已知高峰)
    # t=0.50  2024-12  172,000  (已知回调)
    # t=0.63  2025-04  350,000  (AI算力需求持续爆发)
    # t=0.75  2025-08  750,000  (HBM超级周期)
    # t=0.88  2025-12 1,400,000 (年末高峰)
    # t=1.00  2026-05 1,750,000 (用户提供当前价)
    hynix_t = np.array([0.00, 0.29, 0.50, 0.63, 0.75, 0.88, 1.00])
    hynix_v = np.array([133_000, 238_000, 172_000, 350_000, 750_000, 1_400_000, 1_750_000],
                       dtype=float)
    hynix_trend = np.interp(t, hynix_t, hynix_v)

    # GBM 噪声（日波动率 ≈ 2%）
    daily_ret = rng.normal(0, 0.020, n)
    gbm = np.exp(np.cumsum(daily_ret) - 0.5 * 0.020**2 * np.arange(n))
    # 趋势主导，叠加少量随机游走
    hynix_raw = 0.78 * hynix_trend + 0.22 * hynix_trend * gbm / gbm.mean()
    hynix = np.clip(hynix_raw, 100_000, 2_500_000)
    hynix = (hynix / 1_000).round() * 1_000  # 1,000원 단위

    # ── SK Square 关键节点 ─────────────────────────────────────────────────
    # Square 与海力士相关（β≈0.45），但绝对价格始终远低于海力士
    # t=0.00  2024-01   65,000
    # t=0.29  2024-07   80,000  (跟随海力士小幅上涨)
    # t=0.50  2024-12   62,000  (回调更深)
    # t=0.63  2025-04  130,000
    # t=0.75  2025-08  380,000
    # t=0.88  2025-12  820,000
    # t=1.00  2026-05 1,020,000 (用户提供当前价)
    sq_t = np.array([0.00, 0.29, 0.50, 0.63, 0.75, 0.88, 1.00])
    sq_v = np.array([65_000, 80_000, 62_000, 130_000, 380_000, 820_000, 1_020_000],
                    dtype=float)
    sq_trend = np.interp(t, sq_t, sq_v)

    # 与海力士相关，但波动率稍低（1.8%）
    rho = 0.60
    sq_ind_ret = rng.normal(0, 0.018, n)
    sq_ret = rho * daily_ret + np.sqrt(1 - rho**2) * sq_ind_ret
    sq_gbm = np.exp(np.cumsum(sq_ret) - 0.5 * 0.018**2 * np.arange(n))
    sq_raw = 0.78 * sq_trend + 0.22 * sq_trend * sq_gbm / sq_gbm.mean()
    square = np.clip(sq_raw, 40_000, 1_500_000)
    square = (square / 1_000).round() * 1_000

    df = pd.DataFrame({"hynix": hynix, "square": square}, index=dates)
    df.index.name = "date"

    # 最后一个交易日强制对齐用户提供的实际市价（2026-05-20）
    df.iloc[-1, df.columns.get_loc("hynix")]  = 1_750_000
    df.iloc[-1, df.columns.get_loc("square")] = 1_020_000
    return df


def fetch_prices(force_demo: bool = False) -> pd.DataFrame:
    if force_demo:
        return make_demo_prices()
    for fetcher, label in [(fetch_prices_yfinance, "Yahoo Finance"),
                           (fetch_prices_krx,     "KRX"),
                           (make_demo_prices,      "演示数据")]:
        try:
            df = fetcher()
            if len(df) > 10:
                print(f"数据来源: {label}  ({len(df)} 个交易日)")
                return df
        except Exception as e:
            print(f"{label} 获取失败: {e}")
    raise RuntimeError("所有数据源均不可用")


# ── 计算折价率 ─────────────────────────────────────────────────────────────────

def calc_nav_discount(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["nav_total"]     = SK_SQUARE_HYNIX_SHARES * df["hynix"] + OTHER_NET_ASSETS_KRW
    df["nav_per_share"] = df["nav_total"] / SK_SQUARE_TOTAL_SHARES
    df["discount_pct"]  = (1 - df["square"] / df["nav_per_share"]) * 100
    df["sq_mktcap_t"]   = df["square"] * SK_SQUARE_TOTAL_SHARES / 1e12
    df["nav_total_t"]   = df["nav_total"] / 1e12
    return df


# ── 可视化 ─────────────────────────────────────────────────────────────────────

def build_figure(df: pd.DataFrame, is_demo: bool) -> go.Figure:
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        row_heights=[0.34, 0.34, 0.32],
        vertical_spacing=0.07,
        subplot_titles=(
            "SK海力士 & SK Square 日收盘价 (KRW)",
            "SK Square 市值 vs NAV (兆韩元)",
            "SK Square 对NAV折价率 (%)",
        ),
    )

    # 面板1: 收盘价（对数刻度，便于展示大幅涨跌）
    fig.add_trace(go.Scatter(
        x=df.index, y=df["hynix"],
        name="SK海力士 (000660.KS)",
        line=dict(color="#E63946", width=2),
        hovertemplate="%{x|%Y-%m-%d}<br>海力士: ₩%{y:,.0f}<extra></extra>",
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=df.index, y=df["square"],
        name="SK Square (402340.KS)",
        line=dict(color="#457B9D", width=2),
        hovertemplate="%{x|%Y-%m-%d}<br>Square: ₩%{y:,.0f}<extra></extra>",
    ), row=1, col=1)

    # 面板2: 市值 vs NAV
    fig.add_trace(go.Scatter(
        x=df.index, y=df["nav_total_t"],
        name="NAV (兆₩)",
        line=dict(color="#2A9D8F", width=1.8, dash="dot"),
        hovertemplate="%{x|%Y-%m-%d}<br>NAV: ₩%{y:.2f}兆<extra></extra>",
    ), row=2, col=1)

    fig.add_trace(go.Scatter(
        x=df.index, y=df["sq_mktcap_t"],
        name="SK Square 市值 (兆₩)",
        line=dict(color="#457B9D", width=1.8),
        fill="tonexty",
        fillcolor="rgba(69,123,157,0.14)",
        hovertemplate="%{x|%Y-%m-%d}<br>市值: ₩%{y:.2f}兆<extra></extra>",
    ), row=2, col=1)

    # 面板3: 折价率
    discount_vals = df["discount_pct"].values
    bar_colors = ["#E63946" if v >= 0 else "#2A9D8F" for v in discount_vals]

    fig.add_trace(go.Bar(
        x=df.index, y=discount_vals,
        name="折价率 (%)",
        marker_color=bar_colors,
        opacity=0.75,
        hovertemplate="%{x|%Y-%m-%d}<br>折价率: %{y:.1f}%<extra></extra>",
    ), row=3, col=1)

    ma20 = df["discount_pct"].rolling(20).mean()
    ma60 = df["discount_pct"].rolling(60).mean()
    fig.add_trace(go.Scatter(
        x=df.index, y=ma20,
        name="20日均线",
        line=dict(color="#F4A261", width=2),
        hovertemplate="20MA: %{y:.1f}%<extra></extra>",
    ), row=3, col=1)
    fig.add_trace(go.Scatter(
        x=df.index, y=ma60,
        name="60日均线",
        line=dict(color="#6A0572", width=1.8, dash="dash"),
        hovertemplate="60MA: %{y:.1f}%<extra></extra>",
    ), row=3, col=1)

    # 参考线
    hist_avg = df["discount_pct"].mean()
    for y_val, color, dash, width, label in [
        (0,        "#333",    "solid", 1.4, None),
        (hist_avg, "#888",    "dash",  1.2, f"历史均值 {hist_avg:.1f}%"),
        (70,       "#bbb",    "dot",   1.0, "70%"),
        (80,       "#bbb",    "dot",   1.0, "80%"),
    ]:
        fig.add_hline(y=y_val, line_color=color, line_dash=dash,
                      line_width=width,
                      annotation_text=label or "",
                      annotation_position="right",
                      row=3, col=1)

    # 布局
    latest     = df.iloc[-1]
    latest_dt  = df.index[-1].strftime("%Y-%m-%d")
    demo_flag  = "  <i>(演示数据)</i>" if is_demo else ""

    fig.update_layout(
        title=dict(
            text=(
                f"SK Square 持有 SK海力士 ({SK_SQUARE_HYNIX_STAKE*100:.2f}%) 折价动态{demo_flag}<br>"
                f"<sup>最新折价率 <b style='color:#E63946'>{latest['discount_pct']:.1f}%</b>  |  "
                f"SK海力士 ₩{latest['hynix']:,.0f}  |  "
                f"SK Square ₩{latest['square']:,.0f}  |  "
                f"NAV/股 ₩{latest['nav_per_share']:,.0f}  |  {latest_dt}</sup>"
            ),
            font=dict(size=17),
            x=0.5,
        ),
        template="plotly_white",
        hovermode="x unified",
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
            bgcolor="rgba(255,255,255,0.8)", bordercolor="#ddd", borderwidth=1,
        ),
        height=900,
        margin=dict(t=130, b=80, l=80, r=60),
        font=dict(family="Arial, sans-serif", size=12),
        plot_bgcolor="#FAFAFA",
        paper_bgcolor="#FFFFFF",
    )

    fig.update_yaxes(title_text="价格 (KRW, 对数)", type="log",
                     tickformat=",.0f", gridcolor="#E8E8E8", row=1, col=1)
    fig.update_yaxes(title_text="兆韩元 (₩T)",
                     gridcolor="#E8E8E8", row=2, col=1)
    fig.update_yaxes(title_text="折价率 (%)",  ticksuffix="%",
                     gridcolor="#E8E8E8", row=3, col=1)
    fig.update_xaxes(gridcolor="#E8E8E8")
    fig.update_xaxes(
        rangeslider=dict(visible=True, thickness=0.045),
        rangeselector=dict(
            buttons=[
                dict(count=3,  label="3M",  step="month", stepmode="backward"),
                dict(count=6,  label="6M",  step="month", stepmode="backward"),
                dict(count=12, label="1Y",  step="month", stepmode="backward"),
                dict(step="all", label="ALL"),
            ],
            bgcolor="#F0F0F0",
        ),
        row=3, col=1,
    )

    return fig


# ── 摘要输出 ───────────────────────────────────────────────────────────────────

def print_summary(df: pd.DataFrame) -> None:
    l = df.iloc[-1]
    print("\n" + "═" * 58)
    print("  SK Square / SK海力士 折价分析摘要")
    print("═" * 58)
    print(f"  最新 SK海力士 收盘价  : ₩{l['hynix']:>12,.0f}")
    print(f"  最新 SK Square 收盘价 : ₩{l['square']:>12,.0f}")
    print(f"  最新 NAV/股           : ₩{l['nav_per_share']:>12,.0f}")
    print(f"  最新折价率            :  {l['discount_pct']:>10.1f}%")
    print("─" * 58)
    print(f"  历史平均折价率        :  {df['discount_pct'].mean():>10.1f}%")
    print(f"  历史最小折价率        :  {df['discount_pct'].min():>10.1f}%")
    print(f"  历史最大折价率        :  {df['discount_pct'].max():>10.1f}%")
    print(f"  数据区间              :  {df.index[0].date()} → {df.index[-1].date()}")
    print("═" * 58)


# ── 主程序 ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    demo_mode = "--demo" in sys.argv

    df      = fetch_prices(force_demo=demo_mode)
    df      = calc_nav_discount(df)
    is_demo = "演示" in (df.index.name or "") or demo_mode or len(df) < 20

    # 检查是否为演示数据（通过判断数据来源）
    is_demo = demo_mode or not any(
        abs(df["hynix"].iloc[0] - v) < 50_000
        for v in [130_000, 150_000, 170_000, 190_000, 210_000]
    )

    print_summary(df)

    fig = build_figure(df, is_demo=demo_mode)

    out_html = "/home/user/SKtommy/sk_discount_visualization.html"
    fig.write_html(out_html, include_plotlyjs="cdn")
    print(f"\n交互式图表已保存: {out_html}")

    try:
        out_png = "/home/user/SKtommy/sk_discount_visualization.png"
        fig.write_image(out_png, width=1400, height=900, scale=2)
        print(f"静态图片已保存: {out_png}")
    except Exception:
        print("(静态图片导出需要 kaleido，已跳过)")
