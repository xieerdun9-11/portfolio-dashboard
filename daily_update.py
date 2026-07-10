#!/usr/bin/env python3
"""投资账户每日更新脚本 — 读取 portfolio_input.json，计算持仓盈亏，生成 daily_result.json

计算约定（关键，避免重复计算）：
  - accounts.IB.balance / accounts.YL.balance 为「账户总市值」，已包含 现金 + 持仓市值
  - 因此 总资产 = IB余额 + YL余额（不可再额外叠加持仓市值）
  - 现金 = 总资产 − 持仓市值（由行情反向推导）
  - 仓位比例 = 持仓市值 / 总资产
"""

import json
import os
from datetime import datetime

WS = "/workspace"

with open(os.path.join(WS, "portfolio_input.json"), "r") as f:
    data = json.load(f)

rate = data["usd_cny_rate"]
date_str = data["date"]
holdings = data["holdings"]
principal_total = data["principal"]["total"]
accounts = data["accounts"]
realized_pnl = float(data.get("realized_pnl", 0.0))
transactions = data.get("transactions", [])
principal_records = data.get("principal_records", [])

# ── 计算持仓 ──────────────────────────────────────────────────
rows = []
total_market_value = 0.0
total_cost = 0.0
total_unrealized_pnl = 0.0

for h in holdings:
    symbol = h["symbol"]
    shares = h["shares"]
    cost = h["cost_basis"]
    price = h["price"]
    prev_price = h.get("prev_price", price)

    market_value = shares * price
    cost_total_holding = shares * cost
    unrealized_pnl = market_value - cost_total_holding
    pnl_pct = (unrealized_pnl / cost_total_holding * 100) if cost_total_holding > 0 else 0
    daily_change = (price - prev_price) * shares

    total_market_value += market_value
    total_cost += cost_total_holding
    total_unrealized_pnl += unrealized_pnl

    rows.append({
        "symbol": symbol,
        "shares": shares,
        "cost_basis": round(cost, 2),
        "price": round(price, 2),
        "market_value": round(market_value, 2),
        "unrealized_pnl": round(unrealized_pnl, 2),
        "pnl_pct": round(pnl_pct, 2),
        "daily_change": round(daily_change, 2),
        "prev_price": round(prev_price, 2)
    })

# ── 账户余额（已含现金 + 持仓市值）────────────────────────────
ib_balance = accounts["IB"]["balance"]
yl_balance = accounts["YL"]["balance"]

# 关键修正：余额本身就是账户总市值，总资产直接为两者之和，不再叠加持仓
total_assets_usd = ib_balance + yl_balance
total_cash = total_assets_usd - total_market_value   # 现金由总资产反向推导
total_assets_cny = total_assets_usd * rate

# ── 盈亏 ──────────────────────────────────────────────────────
total_pnl = total_unrealized_pnl + realized_pnl
total_return_pct = (total_pnl / principal_total * 100) if principal_total > 0 else 0

# ── 仓位比例 ──────────────────────────────────────────────────
position_pct = (total_market_value / total_assets_usd * 100) if total_assets_usd > 0 else 0

# ── 日变动 ────────────────────────────────────────────────────
total_daily_change = sum(r["daily_change"] for r in rows)

# ── 历史序列 & 回撤 ───────────────────────────────────────────
hist_path = os.path.join(WS, "history.json")
history = {}
if os.path.exists(hist_path):
    try:
        with open(hist_path, "r") as f:
            history = json.load(f)
    except Exception:
        history = {}
history[date_str] = round(total_assets_usd, 2)
with open(hist_path, "w") as f:
    json.dump(history, f, indent=2, ensure_ascii=False)

peak = max(history.values()) if history else total_assets_usd
peak_date = max(history, key=history.get) if history else date_str
drawdown_pct = ((peak - total_assets_usd) / peak * 100) if peak > 0 else 0.0
is_new_high = abs(total_assets_usd - peak) < 1e-6

# ── FIRE 计算 ─────────────────────────────────────────────────
fire_target = 350000.0
fire_target_cny = fire_target * rate
gap_usd = fire_target - total_assets_usd
gap_cny = gap_usd * rate
years_remaining = 8.7
annual_addition = 7000.0
future_principal = years_remaining * annual_addition
earnings_gap_cny = (fire_target - total_assets_usd - future_principal) * rate
total_target_cny = fire_target * rate
progress_pct = (total_assets_cny / total_target_cny * 100) if total_target_cny > 0 else 0

print(f"\n{'='*60}")
print(f"  投资账户每日更新 — {date_str}")
print(f"{'='*60}")
print(f"\n  USD/CNY 汇率: {rate:.4f}")
print(f"\n  📊 持仓明细:")
print(f"  {'标的':<6} {'股数':>6} {'成本':>10} {'现价':>10} {'市值':>12} {'盈亏':>12} {'盈亏%':>8} {'日变动':>10}")
print(f"  {'-'*72}")
for r in rows:
    print(f"  {r['symbol']:<6} {r['shares']:>6} ${r['cost_basis']:>8.2f} ${r['price']:>8.2f} ${r['market_value']:>10.2f} ${r['unrealized_pnl']:>10.2f} {r['pnl_pct']:>7.2f}% ${r['daily_change']:>8.2f}")

print(f"\n  💰 账户汇总:")
print(f"  IB 账户总值:     ${ib_balance:>12,.2f}  (¥{ib_balance * rate:>12,.2f})")
print(f"  YL 账户总值:     ${yl_balance:>12,.2f}  (¥{yl_balance * rate:>12,.2f})")
print(f"  总资产:          ${total_assets_usd:>12,.2f}  (¥{total_assets_cny:>12,.2f})")
print(f"  持仓市值:        ${total_market_value:>12,.2f}  (¥{total_market_value * rate:>12,.2f})")
print(f"  现金(推导):      ${total_cash:>12,.2f}  (¥{total_cash * rate:>12,.2f})")
print(f"\n  📈 盈亏概况:")
print(f"  浮盈:            ${total_unrealized_pnl:>12,.2f}")
print(f"  已实现盈亏:      ${realized_pnl:>12,.2f}")
print(f"  总盈亏:          ${total_pnl:>12,.2f}")
print(f"  累计收益率:      {total_return_pct:>11.2f}%")
print(f"  日变动:          ${total_daily_change:>12,.2f}")
print(f"  仓位比例:        {position_pct:>11.1f}%")
print(f"  回撤(自峰值):    {drawdown_pct:>11.2f}%  (峰值 ${peak:,.2f} @ {peak_date}{' · 创新高' if is_new_high else ''})")
print(f"\n  🎯 FIRE 目标 ($350K):")
print(f"  当前差距:        ${gap_usd:>12,.2f}  (¥{gap_cny:>12,.2f})")
print(f"  剩余年限:        {years_remaining:>11.1f}年")
print(f"  进度:            {progress_pct:>11.1f}%")
print(f"{'='*60}\n")

# ── 保存计算结果 ──────────────────────────────────────────────
result = {
    "date": date_str,
    "usd_cny_rate": rate,
    "principal": principal_total,
    "realized_pnl": round(realized_pnl, 2),
    "accounts": {
        "ib": round(ib_balance, 2),
        "yl": round(yl_balance, 2)
    },
    "holdings": rows,
    "transactions": transactions,
    "principal_records": principal_records,
    "cash": {
        "ib": round(ib_balance, 2),
        "yl": round(yl_balance, 2),
        "total": round(total_cash, 2),
        "is_derived": True
    },
    "summary": {
        "market_value": round(total_market_value, 2),
        "total_assets_usd": round(total_assets_usd, 2),
        "total_assets_cny": round(total_assets_cny, 2),
        "total_cost": round(total_cost, 2),
        "unrealized_pnl": round(total_unrealized_pnl, 2),
        "realized_pnl": round(realized_pnl, 2),
        "total_pnl": round(total_pnl, 2),
        "total_return_pct": round(total_return_pct, 2),
        "daily_change": round(total_daily_change, 2),
        "position_pct": round(position_pct, 1),
        "cash_derived": round(total_cash, 2)
    },
    "drawdown": {
        "current_pct": round(drawdown_pct, 2),
        "peak_usd": round(peak, 2),
        "peak_date": peak_date,
        "is_new_high": is_new_high,
        "history_points": len(history)
    },
    "fire": {
        "target": fire_target,
        "target_cny": round(fire_target_cny, 2),
        "gap_usd": round(gap_usd, 2),
        "gap_cny": round(gap_cny, 2),
        "years_remaining": round(years_remaining, 1),
        "annual_addition": annual_addition,
        "progress_pct": round(progress_pct, 1)
    }
}

with open(os.path.join(WS, "daily_result.json"), "w") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print("✅ 计算结果已保存到 /workspace/daily_result.json")
