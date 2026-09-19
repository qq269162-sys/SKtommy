"""
本地运行专用 — 从 alphasquare.co.kr 获取实时价格，从 sksquare.com 获取 NAV

用法:
  pip install requests beautifulsoup4 playwright
  playwright install chromium        # alphasquare 是 SPA，需要浏览器渲染
  python fetch_live_prices.py
"""

import json
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
    "Referer": "https://alphasquare.co.kr/",
}


# ── 1. alphasquare.co.kr ──────────────────────────────────────────────────────

def fetch_alphasquare_api(code: str) -> dict | None:
    """
    alphasquare 内部 API（通过浏览器 Network 面板发现的端点，可能随版本变化）
    备用: 直接抓 HTML
    """
    # 常见端点格式，实际端点需用浏览器 Network 面板确认
    candidates = [
        f"https://alphasquare.co.kr/api/v1/stock/{code}",
        f"https://alphasquare.co.kr/api/stock/summary?code={code}",
        f"https://alphasquare.co.kr/home/stock-summary?code={code}",  # SPA 页面
    ]
    for url in candidates:
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            if r.status_code == 200 and r.content:
                try:
                    return {"url": url, "json": r.json()}
                except Exception:
                    return {"url": url, "html_len": len(r.text), "preview": r.text[:300]}
        except Exception as e:
            print(f"  ✗ {url}: {e}")
    return None


def fetch_alphasquare_playwright(code: str) -> dict | None:
    """
    alphasquare 是 React SPA，需要 Playwright 渲染后抓取价格
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  playwright 未安装: pip install playwright && playwright install chromium")
        return None

    url = f"https://alphasquare.co.kr/home/stock-summary?code={code}"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle", timeout=30_000)

        # 等待价格元素出现（selector 需根据实际页面结构调整）
        try:
            page.wait_for_selector("[class*='price'], [class*='Price']", timeout=10_000)
        except Exception:
            pass

        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, "html.parser")

    # 尝试从 <script> 里找 JSON 数据（SPA 常把初始数据放在 window.__DATA__ 等变量里）
    for script in soup.find_all("script"):
        text = script.string or ""
        if "currentPrice" in text or "closePrice" in text or "종가" in text:
            print("  발견된 script 데이터 (부분):", text[:500])

    # 直接找数字元素
    result = {}
    for tag in soup.find_all(True):
        cls = " ".join(tag.get("class", []))
        if any(k in cls.lower() for k in ["price", "close", "current"]):
            txt = tag.get_text(strip=True)
            if txt and any(c.isdigit() for c in txt):
                result[cls] = txt

    return result or None


# ── 2. SK Square 官网 NAV ─────────────────────────────────────────────────────

def fetch_sksquare_nav() -> dict | None:
    """
    SK Square IR 页面 NAV 数据
    官网: https://www.sksquare.com/en/ir/nav  (영어)
          https://www.sksquare.com/ko/ir/nav  (한국어)
    """
    for lang, url in [("en", "https://www.sksquare.com/en/ir/nav"),
                      ("ko", "https://www.sksquare.com/ko/ir/nav")]:
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                print(f"  {lang}: HTTP {r.status_code}")
                continue

            soup = BeautifulSoup(r.text, "html.parser")

            # 找表格或数字
            tables = soup.find_all("table")
            result = {"url": url, "tables": []}
            for tbl in tables:
                rows = []
                for tr in tbl.find_all("tr"):
                    cells = [td.get_text(strip=True) for td in tr.find_all(["th", "td"])]
                    if cells:
                        rows.append(cells)
                if rows:
                    result["tables"].append(rows)

            # 找含 NAV / 주당 / per share 的文本
            nav_hints = []
            for tag in soup.find_all(string=True):
                t = tag.strip()
                if any(k in t.lower() for k in ["nav", "net asset", "주당", "hynix", "하이닉스"]):
                    nav_hints.append(t)
            result["nav_hints"] = nav_hints[:20]

            return result
        except Exception as e:
            print(f"  {lang}: {e}")
    return None


# ── 3. 韩国투자증권 Open API（需要申请 API Key）──────────────────────────────

def fetch_korea_investment_api(code: str, app_key: str, app_secret: str) -> dict | None:
    """
    한국투자증권 OpenAPI — 실시간 시세 (약 15분 지연 없음)
    신청: https://apiportal.koreainvestment.com/
    무료 사용 가능
    """
    # 1) 토큰 발급
    token_url = "https://openapi.koreainvestment.com:9443/oauth2/tokenP"
    token_res = requests.post(token_url, json={
        "grant_type": "client_credentials",
        "appkey": app_key,
        "appsecret": app_secret,
    }, timeout=10)
    token = token_res.json().get("access_token")
    if not token:
        print("  토큰 발급 실패:", token_res.text[:200])
        return None

    # 2) 현재가 조회
    price_url = "https://openapi.koreainvestment.com:9443/uapi/domestic-stock/v1/quotations/inquire-price"
    res = requests.get(price_url, headers={
        "Content-Type": "application/json",
        "authorization": f"Bearer {token}",
        "appkey": app_key,
        "appsecret": app_secret,
        "tr_id": "FHKST01010100",
    }, params={
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": code,
    }, timeout=10)
    return res.json()


# ── main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("1. alphasquare.co.kr — SK海力士 (000660)")
    print("=" * 60)

    # 先试 REST API
    result = fetch_alphasquare_api("000660")
    if result:
        print("API 결과:", json.dumps(result, ensure_ascii=False, indent=2)[:800])
    else:
        # 退而求其次用 Playwright
        print("API 不可用，尝试 Playwright 渲染...")
        result = fetch_alphasquare_playwright("000660")
        print("Playwright 结果:", result)

    print()
    print("=" * 60)
    print("2. sksquare.com — SK Square NAV 데이터")
    print("=" * 60)
    nav = fetch_sksquare_nav()
    if nav:
        print("NAV 페이지 tables:")
        for tbl in nav.get("tables", [])[:3]:
            for row in tbl[:5]:
                print("  ", row)
        print("NAV 관련 텍스트:")
        for h in nav.get("nav_hints", []):
            print("  >>", h)
    else:
        print("NAV 데이터 취득 실패")

    print()
    print("=" * 60)
    print("3. 한국투자증권 OpenAPI (需填入自己的 Key)")
    print("=" * 60)
    print("  请先到 https://apiportal.koreainvestment.com/ 申请免费 API Key")
    print("  然后取消注释下面的代码:")
    print("  # result = fetch_korea_investment_api('000660', 'YOUR_APP_KEY', 'YOUR_APP_SECRET')")
