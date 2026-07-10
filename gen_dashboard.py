#!/usr/bin/env python3
"""生成投资看板 dashboard.html（含持仓明细、回撤、交易明细）"""

import json

with open("/workspace/daily_result.json", "r") as f:
    d = json.load(f)

rate = d["usd_cny_rate"]
date_str = d["date"]
holdings = d["holdings"]
summary = d["summary"]
cash = d["cash"]
fire_data = d["fire"]
principal = d["principal"]
drawdown = d["drawdown"]
transactions = d.get("transactions", [])
principal_records = d.get("principal_records", [])
accounts = d.get("accounts", {})

# ── 持仓明细行 ────────────────────────────────────────────────
rows_html = ""
for r in holdings:
    symbol = r["symbol"]
    shares = r["shares"]
    cost = r["cost_basis"]
    price = r["price"]
    mv = r["market_value"]
    pnl = r["unrealized_pnl"]
    pnl_pct = r["pnl_pct"]
    color = "#e74c3c" if pnl < 0 else "#27ae60"
    dcolor = "#e74c3c" if r["daily_change"] < 0 else "#27ae60"
    rows_html += f"""
    <tr>
      <td><strong>{symbol}</strong></td>
      <td>{shares}</td>
      <td>${cost:,.2f}</td>
      <td>${price:,.2f}</td>
      <td>${mv:,.2f}</td>
      <td style="color:{color}">${pnl:,.2f}</td>
      <td style="color:{color}">{pnl_pct:+.2f}%</td>
      <td style="color:{dcolor}">{r['daily_change']:+,.2f}</td>
    </tr>"""

total_color = "#e74c3c" if summary["unrealized_pnl"] < 0 else "#27ae60"

# ── 回撤卡片 ──────────────────────────────────────────────────
dd_pct = drawdown["current_pct"]
dd_color = "#27ae60" if dd_pct <= 0 else "#e74c3c"
dd_badge = "创新高 🚀" if drawdown["is_new_high"] else f"峰值 ${drawdown['peak_usd']:,.2f} @ {drawdown['peak_date']}"
dd_note = "历史序列自今日起建立，后续每日累积" if drawdown["history_points"] <= 1 else f"已记录 {drawdown['history_points']} 个交易日"

# ── 交易明细 ──────────────────────────────────────────────────
tx_rows = ""
if principal_records:
    for p in principal_records:
        amt = p.get("amount", 0)
        cur = p.get("currency", "USD")
        note = p.get("note", "")
        tx_rows += f"""
    <tr>
      <td>{p.get('date','')}</td>
      <td><span class="badge badge-principal">本金注入</span></td>
      <td>{p.get('symbol','—')}</td>
      <td>{p.get('shares','—')}</td>
      <td style="color:#6ee7b7">+${amt:,.2f} {cur}</td>
      <td style="color:#94a3b8">{note}</td>
    </tr>"""

if transactions:
    for t in transactions:
        ttype = t.get("type", "BUY")
        sym = t.get("symbol", "—")
        sh = t.get("shares", "—")
        amt = t.get("amount", 0)
        note = t.get("note", "")
        if ttype == "BUY":
            badge = "badge-buy"; label = "买入"; acolor = "#fcd34d"; aval = f"-${abs(amt):,.2f}"
        elif ttype == "SELL":
            badge = "badge-sell"; label = "卖出"; acolor = "#6ee7b7"; aval = f"+${amt:,.2f}"
        elif ttype == "DIVIDEND":
            badge = "badge-div"; label = "分红"; acolor = "#6ee7b7"; aval = f"+${amt:,.2f}"
        else:
            badge = "badge-info"; label = ttype; acolor = "#e2e8f0"; aval = f"${amt:,.2f}"
        tx_rows += f"""
    <tr>
      <td>{t.get('date','')}</td>
      <td><span class="badge {badge}">{label}</span></td>
      <td>{sym}</td>
      <td>{sh}</td>
      <td style="color:{acolor}">{aval}</td>
      <td style="color:#94a3b8">{note}</td>
    </tr>"""

if not tx_rows:
    tx_rows = """
    <tr><td colspan="6" style="text-align:center;color:#64748b;padding:18px;">今日无交易记录</td></tr>"""

accounts_sub = f"IB ${accounts.get('ib',0):,.0f} · YL ${accounts.get('yl',0):,.0f}（账户总值，含现金+持仓）"

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>投资看板 · Portfolio Dashboard</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: #0f172a;
      color: #e2e8f0;
      padding: 20px;
      max-width: 1200px;
      margin: 0 auto;
    }}
    h1 {{ text-align: center; font-size: 1.8em; margin-bottom: 5px; color: #f1f5f9; }}
    .subtitle {{ text-align: center; color: #94a3b8; font-size: 0.9em; margin-bottom: 30px; }}
    .subtitle span {{ margin: 0 10px; }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }}
    .card {{
      background: #1e293b; border-radius: 12px; padding: 18px; border: 1px solid #334155;
    }}
    .card .label {{
      font-size: 0.8em; color: #94a3b8; text-transform: uppercase;
      letter-spacing: 0.05em; margin-bottom: 6px;
    }}
    .card .value {{ font-size: 1.45em; font-weight: 700; color: #f1f5f9; }}
    .card .sub {{ font-size: 0.82em; color: #64748b; margin-top: 4px; }}
    .card .value.green {{ color: #27ae60; }}
    .card .value.red {{ color: #e74c3c; }}
    .card .value.blue {{ color: #3b82f6; }}
    .section-title {{
      font-size: 1.1em; font-weight: 600; color: #cbd5e1;
      margin: 24px 0 12px; border-bottom: 2px solid #334155; padding-bottom: 6px;
    }}
    table {{
      width: 100%; border-collapse: collapse; margin-bottom: 24px;
      background: #1e293b; border-radius: 12px; overflow: hidden;
    }}
    th {{
      background: #334155; color: #94a3b8; font-size: 0.78em; text-transform: uppercase;
      letter-spacing: 0.05em; padding: 12px 14px; text-align: right;
    }}
    th:first-child {{ text-align: left; }}
    td {{ padding: 10px 14px; text-align: right; border-bottom: 1px solid #1e293b; font-size: 0.92em; }}
    td:first-child {{ text-align: left; }}
    tr:hover {{ background: #263348; }}
    .footer {{ text-align: center; color: #475569; font-size: 0.8em; margin-top: 30px; padding-top: 16px; border-top: 1px solid #1e293b; }}
    .badge {{
      display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 0.78em; font-weight: 600;
    }}
    .badge-safe {{ background: #064e3b; color: #6ee7b7; }}
    .badge-warn {{ background: #78350f; color: #fcd34d; }}
    .badge-buy {{ background: #78350f; color: #fcd34d; }}
    .badge-sell {{ background: #064e3b; color: #6ee7b7; }}
    .badge-div {{ background: #1e3a5f; color: #93c5fd; }}
    .badge-principal {{ background: #312e81; color: #c7d2fe; }}
    .badge-info {{ background: #334155; color: #cbd5e1; }}
    .progress-bar {{ background: #334155; border-radius: 10px; height: 10px; margin-top: 8px; overflow: hidden; }}
    .progress-fill {{ background: linear-gradient(90deg, #3b82f6, #6366f1); height: 100%; border-radius: 10px; }}
    @media (max-width: 768px) {{ .cards {{ grid-template-columns: repeat(2, 1fr); }} body {{ padding: 10px; }} }}
  </style>
</head>
<body>

<h1>投资看板</h1>
<p class="subtitle">
  截至 <strong>{date_str}</strong>
  <span>|</span> USD/CNY <strong>{rate:.4f}</strong>
  <span>|</span> 本金 <strong>${principal:,.0f}</strong>
</p>

<div class="cards">
  <div class="card">
    <div class="label">总资产</div>
    <div class="value">${summary["total_assets_usd"]:,.2f}</div>
    <div class="sub">¥{summary["total_assets_cny"]:,.2f}</div>
  </div>
  <div class="card">
    <div class="label">总盈亏</div>
    <div class="value {"green" if summary["total_pnl"] >= 0 else "red"}">${summary["total_pnl"]:+,.2f}</div>
    <div class="sub">浮盈 ${summary["unrealized_pnl"]:,.2f} · 已实现 ${summary["realized_pnl"]:,.2f}</div>
  </div>
  <div class="card">
    <div class="label">累计收益率</div>
    <div class="value {"green" if summary["total_return_pct"] >= 0 else "red"}">{summary["total_return_pct"]:+.2f}%</div>
    <div class="sub">本金 ${principal:,.0f}</div>
  </div>
  <div class="card">
    <div class="label">持仓市值</div>
    <div class="value">${summary["market_value"]:,.2f}</div>
    <div class="sub">成本基础 ${summary["total_cost"]:,.2f}</div>
  </div>
  <div class="card">
    <div class="label">现金 Cash（推导）</div>
    <div class="value blue">${cash["total"]:,.2f}</div>
    <div class="sub">¥{cash["total"] * rate:,.2f} · 总资产−持仓市值</div>
  </div>
  <div class="card">
    <div class="label">仓位比例 Position</div>
    <div class="value">{summary["position_pct"]:.1f}%</div>
    <div class="sub">
      <span class="badge {"badge-safe" if summary["position_pct"] <= 55 else "badge-warn"}">{"偏低 · 可加仓" if summary["position_pct"] <= 55 else ("适中" if summary["position_pct"] <= 75 else "偏高 · 谨慎")}</span>
    </div>
  </div>
  <div class="card">
    <div class="label">账户回撤 Drawdown</div>
    <div class="value {dd_color}">{dd_pct:+.2f}%</div>
    <div class="sub">{dd_badge}</div>
    <div class="sub">{dd_note}</div>
  </div>
</div>

<div class="section-title">🎯 FIRE 目标 · $350K</div>
<div class="cards">
  <div class="card">
    <div class="label">FIRE 目标</div>
    <div class="value">${fire_data["target"]:,.0f}</div>
    <div class="sub">10年计划 · 至2035-03</div>
  </div>
  <div class="card">
    <div class="label">当前差距</div>
    <div class="value red">${fire_data["gap_usd"]:,.2f}</div>
    <div class="sub">¥{fire_data["gap_cny"]:,.2f}</div>
  </div>
  <div class="card">
    <div class="label">剩余年限</div>
    <div class="value">{fire_data["years_remaining"]}年</div>
    <div class="sub">含复利滚动</div>
  </div>
  <div class="card">
    <div class="label">进度</div>
    <div class="value">{fire_data["progress_pct"]:.1f}%</div>
    <div class="progress-bar"><div class="progress-fill" style="width:{min(fire_data['progress_pct'], 100)}%"></div></div>
    <div class="sub">当前 ¥{summary["total_assets_cny"]:,.0f} / 目标 ¥{fire_data["target_cny"]:,.0f}</div>
  </div>
</div>

<div class="section-title">📊 持仓明细 · Holdings</div>
<table>
  <thead>
    <tr>
      <th>标的</th><th>持仓</th><th>摊薄成本</th><th>现价</th><th>市值</th><th>盈亏</th><th>盈亏%</th><th>日变动</th>
    </tr>
  </thead>
  <tbody>
    {rows_html}
    <tr style="font-weight:700; background:#263348;">
      <td><strong>合计</strong></td>
      <td>—</td><td>—</td><td>—</td>
      <td>${summary["market_value"]:,.2f}</td>
      <td style="color:{total_color}">${summary["unrealized_pnl"]:+,.2f}</td>
      <td style="color:{total_color}">{summary["unrealized_pnl"] / summary["total_cost"] * 100 if summary["total_cost"] > 0 else 0:+.2f}%</td>
      <td style="color:{total_color}">${summary["daily_change"]:+,.2f}</td>
    </tr>
  </tbody>
</table>

<div class="section-title">💸 账户总览 · Accounts</div>
<table>
  <thead><tr><th>账户</th><th>账户总值(含现金+持仓)</th><th>折合 RMB</th></tr></thead>
  <tbody>
    <tr><td><strong>IB</strong></td><td>${accounts.get('ib',0):,.2f}</td><td>¥{accounts.get('ib',0)*rate:,.2f}</td></tr>
    <tr><td><strong>YL</strong></td><td>${accounts.get('yl',0):,.2f}</td><td>¥{accounts.get('yl',0)*rate:,.2f}</td></tr>
    <tr style="font-weight:700; background:#263348;"><td><strong>合计</strong></td><td>${summary['total_assets_usd']:,.2f}</td><td>¥{summary['total_assets_cny']:,.2f}</td></tr>
  </tbody>
</table>

<div class="section-title">🧾 交易明细 · Transactions</div>
<table>
  <thead>
    <tr><th>日期</th><th>类型</th><th>标的</th><th>股数</th><th>金额</th><th>备注</th></tr>
  </thead>
  <tbody>
    {tx_rows}
  </tbody>
</table>

<div class="footer">
  更新于 {date_str} · USD/CNY {rate:.4f} · 数据来源 Yahoo Finance · <a href="https://github.com/xieerdun9-11/portfolio-dashboard" style="color:#64748b;">GitHub</a>
</div>

</body>
</html>"""

with open("/workspace/dashboard.html", "w") as f:
    f.write(html)

print("✅ dashboard.html 已生成")
