# sk-discount

追踪 **SK스퀘어(402340)** 相对其持有的 **SK하이닉스(000660)** 股权的折价。

回答一个问题:**买到 ₩1 的 SK 海力士资产,需要付出多少 SK Square 市值?**

```
  买 ₩1 的 SK 海力士资产,要花  ₩0.525
  折价 47.5%   放大 1.91×   口径 仅海力士

  你付出  ████████████████████████······················  ₩52.5
  你得到  ██████████████████████████████████████████████  ₩100.0
```

单文件、Python 3 标准库、零依赖。

## 安装

```sh
git clone <this repo> && cd SKtommy
chmod +x sk-discount
./sk-discount
```

放进 `PATH` 即可全局使用(例:`ln -s "$PWD/sk-discount" ~/.local/bin/sk-discount`)。

## 用法

```sh
sk-discount                                  # 当前折价(取实时行情)
sk-discount --precise                        # 计入非海力士资产,贴近官方口径
sk-discount --hynix 1857000 --skq 1079000    # 手动代入股价,离线可用
sk-discount --json                           # 机器可读输出

sk-discount history -p 3m                    # 近三个月序列 + 走势图
sk-discount history -p 1y --official         # 附官方日频 NAV 折价做对照
sk-discount history --csv > c.csv            # 导出 CSV

sk-discount calibrate                        # 校验内置持股数是否仍然成立
sk-discount params                           # 结构参数、公式、数据源

sk-discount serve                            # 本地实时服务,每次打开重新取数
sk-discount html                             # 生成静态快照网页
sk-discount ownership                        # 外资持股结构历年统计
```

区间可选 `3m` `6m` `1y` `2y` `5y`。

## 动态更新

**先说清楚一个硬约束:网页自己取不到韩股行情。** Yahoo、Naver(两个域)、
AlphaSquare 四个接口全部不返回 `Access-Control-Allow-Origin` 头,浏览器的跨域策略
会直接拦掉;本地 `file://`、GitHub Pages、claude.ai Artifact 都一样。Artifact 的
运行时能力里也没有「抓取任意外部接口」这一项(`mcp` 只能调用户已连接的 connector,
`sample` 是问模型——拿它取股价等于让模型编数字)。

所以取数必须发生在服务端。有两条路径:

### 1. 本地实时服务 —— 每次打开都重新取数

```sh
sk-discount serve                 # http://127.0.0.1:8765
sk-discount serve -p 9000 --cache 0 --source yahoo
```

打开页面即抓取当日最新价格重新渲染,底部固定条显示数据抓取于几秒前,可点「强制刷新」。
`--cache` 控制重复抓取的最小间隔(默认 60 秒,设 0 表示每次请求都抓)。
另有 `/api.json` 返回当前读数。默认只绑定 `127.0.0.1`,不对外网暴露。

### 2. GitHub Actions —— 每个交易日自动重建

`.github/workflows/refresh.yml` 在每个工作日 07:10 UTC(KRX 收盘 40 分钟后)运行,
重新生成 `docs/index.html` 与 `docs/ownership.html` 并提交。页面带构建时间戳,
工作流会先剔掉时间戳行再比对,**只有行情或 NAV 真的变化时才提交**,非交易日不产生噪音提交。
AlphaSquare 取数失败时自动退回 Yahoo。

要拿到一个长期有效的公开地址:仓库 Settings → Pages → Source 选 `main` 分支的
`/docs` 目录,之后 `https://<用户名>.github.io/SKtommy/` 就是始终最新的折价页。

### 3. 手动生成一份快照

```sh
sk-discount html                      # 写到 ./sk-discount.html
sk-discount html --source yahoo -o out.html
```

生成出来的页面是单文件,双击即可打开,不需要网络、不依赖任何 CDN。

**另一个关键约束:页面在完全不执行 JavaScript 的情况下也必须能读完。** 聊天软件的内置
预览、邮件客户端、部分沙箱 iframe 都不跑脚本,而这正是最常见的打开方式。所以:

- 折线图是**预渲染的静态 SVG**,直接写在 HTML 里,不是 JS 画的
- 3M / 6M / 1Y 切换用**纯 CSS**(单选按钮 + 兄弟选择器)实现,无脚本
- 窄屏/宽屏各预渲染一份 SVG,用媒体查询切换,保证两端字号都可读
- 300 行数据表、校验表的每一行都写在源码里
- JS 只剩计算器一项增强;脚本不跑时它显示当日收盘快照,数值仍然正确

内容包括:一年日频数据、「你付出 vs 你得到」对照条、简化法 c 与官方 NAV 折价双线
对照,以及「数据源校验」面板(列出行情源与官方 NAV 基准不一致的全部 10 天)。

行情来自 AlphaSquare(`api.alphasquare.co.kr/data/v3/prices/candles`,stock_id 1456 / 3493)。
静态生成的页面是快照;要始终看到当日最新值,用上面的 `serve` 或 Actions 两种方式。

## 外资持股结构统计

`sk-discount ownership` 输出 SK 海力士与 SK Square 的外国人持股比率逐年统计
(海力士可回溯至 1996-12-26 上市首日,共 31 个年度):

```sh
sk-discount ownership                      # 终端表格
sk-discount ownership --csv > own.csv      # 导出 CSV
sk-discount ownership --html own.html      # 独立网页(含折线图,零 JS 可读)
```

字段:年末外资持股率、同比变化(pp)、年内高/低、年末收盘价,并对关键年份标注公司事件。
同时给出最近 60 个交易日的外资 / 机构 / 个人净买超。

数据取自 Naver 证券日线接口的 `foreignRetentionRate` 字段,当前值经 AlphaSquare 与
WiseReport 三源交叉验证一致。

**口径限制**:逐年的「外资 / 投信 / 自营」分项买卖超无法取得 —— 韩国交易所数据系统
(data.krx.co.kr)现要求登录账号,Naver 旧版投资者动向页已下线、新版接口忽略翻页
参数且最多返回 60 个交易日。故分项净买超仅覆盖最近 60 日。

## 计算方法

每股 SK Square 背后压着固定数量的海力士股票,这个比值就是系数 `k`:

```
k = SK Q 持有的海力士股数 / SK Q 自身总股本
  = 146,128,233 / 131,923,998
  = 1.107670
```

于是成本系数 `c` 只需要两个实时股价:

```
c = P_SKQ / (k × P_HYNIX)              简化口径,只算海力士
c = P_SKQ / (k × P_HYNIX + 其他资产/总股本)   --precise,全资产口径
传统折价率 = 1 − c
```

`k` 只由两个**绝对股数**决定,不含任何百分比,因此海力士自身的回购注销
(改变海力士总股本)不会影响它。

## 参数出处

| 参数 | 取值 | 来源 |
|---|---|---|
| SK Q 持有海力士股数 | 146,128,233 | DART/KRX 披露(「SK스퀘어 외 9인」,占海力士总发行股数 730,492,365 股的 20.00%) |
| SK Q 自身总股本 | 131,923,998 | SK Square IR「Number of Stocks Issued」 |
| 非海力士资产 | ₩4.86 万亿 | SK Square IR NAV 构成(TMAP / SK shieldus / SK planet / wavve / 其他 / 净现金);`--precise` 时实时抓取 |

持股数无法从公开渠道直接查到,但可以反解验证:官网公布了日频 NAV 折价,
结合当日两只股票的收盘价即可倒推出隐含持股数。`calibrate` 子命令做的就是这件事:

```
  用官方日频 NAV 折价反解 SK Q 持有的海力士股数
  125 个交易日 · 2026-03-18 → 2026-09-17

  反解中位数              146,191,441
  程序内置常数            146,128,233
  偏离                        0.043%
```

125 个交易日内海力士股价振幅超过 50%,反解值始终锁定在同一水平,
与 DART 披露值差 0.04% —— 交叉验证成立。

## 数据源

- **行情**:Yahoo Finance chart API(`000660.KS` / `402340.KS`),取 KRX 正规盘收盘价
- **NAV 与官方日频折价**:<https://www.sksquare.com/eng/ir/nav.do>

> 关于行情源的一个坑:Naver 的日线接口(`api.stock.naver.com/chart/domestic/...`)
> 在最近数个交易日上会给出与正规盘收盘价不一致的数值(实测 9/17 海力士报
> 1,766,000,而正规盘收盘为 1,745,000)。SK Square 官网 NAV 用的是正规盘收盘价,
> Yahoo 与之一致,故本程序采用 Yahoo。

## 已知口径问题

- **简化口径系统性高估 `c` 约 0.01。** 忽略了那 ₩4.86 万亿非海力士资产(占总 NAV 约 1.9%)。
  实测近三个月与官方口径的偏差稳定在 +0.0095 ~ +0.0102,近乎常数。要贴近官方数字请加 `--precise`。
- **`k` 需要按季复核。** SK Square 每年回购注销自家股票,分母缓慢变小、`k` 缓慢变大。
  每季 DART 季报后跑一次 `calibrate`,偏离超过 0.5% 会给出提示。
- **2026 年 11 月前后有一次口径变动。** 海力士 2026-08-19 董事会决议的 40 万亿回购
  (约 2,407 万股,占总股本 3.3%)在收购期结束后全部注销。注销**不影响 `k`**,
  但会让 SK Square 的**持股比例**从 20.00% 被动升至约 20.7%,涉及百分比的分析需同步更新。
- **这是估值观察工具,不是交易建议。** 控股公司折价长期存在(官网数据显示 2022–2023 年
  常年在 65–75%),收窄与否取决于治理、分红、分拆等公司行为。

## License

MIT,见 [LICENSE](LICENSE)。
