"""
Random-but-plausible demo data for freshly created traders.

Auto-fills the Trader's own JSON fields — top_traded, portfolio_breakdown,
frequently_traded — with a handful of realistic entries, plus fills in any
Trader-level summary stat still at its default (0) so the profile doesn't
look empty. Everything created here lives directly on the Trader row
afterwards: editable exactly like data an admin typed in by hand (these are
plain JSON fields matching orchard_capitals' Trader model, not separate
relational tables).

Data sources:
- Top Traded: live quotes from the FMP API (real symbol, name, % change)
  when reachable, falling back to the local JSON pool otherwise.
- Portfolio Breakdown / Frequently Traded: drawn from a JSON pool of
  realistic instruments (dashboard/trader_seed_data.json) rather than fully
  arbitrary numbers, so combinations look like real market data and differ
  from trader to trader.
"""

import random
import time
import json
from pathlib import Path

import requests

_DATA_PATH = Path(__file__).resolve().parent / "trader_seed_data.json"
_data_cache = None


def _seed_data() -> dict:
    """Load+cache the JSON pool of realistic instruments/labels used for seeding."""
    global _data_cache
    if _data_cache is None:
        with open(_DATA_PATH, encoding="utf-8") as f:
            _data_cache = json.load(f)
    return _data_cache


# ─────────────────────────────────────────────────────────────────────────────
# Top Traded — live FMP quotes, falling back to the JSON pool
# ─────────────────────────────────────────────────────────────────────────────

# Deliberately wide candidate pools — every trader picks a random handful out
# of ~75 symbols here (plus another ~75 in the JSON fallback pool below), so
# Top Traded actually differs trader to trader instead of converging on the
# same handful of big names.
_FMP_CRYPTO_SYMBOLS = [
    "BTCUSD", "ETHUSD", "SOLUSD", "BNBUSD", "XRPUSD", "ADAUSD", "DOGEUSD", "DOTUSD",
    "AVAXUSD", "MATICUSD", "LTCUSD", "LINKUSD", "UNIUSD", "ATOMUSD", "TRXUSD",
    "NEARUSD", "APTUSD", "ARBUSD", "SHIBUSD", "XLMUSD", "ETCUSD", "FILUSD",
]
_FMP_STOCK_SYMBOLS = [
    # Tech
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "NFLX", "AMD", "INTC",
    "ORCL", "CRM", "ADBE", "CSCO", "IBM", "QCOM", "TXN", "NOW", "SHOP", "UBER",
    # Finance
    "JPM", "BAC", "WFC", "GS", "MS", "V", "MA", "AXP", "C", "BLK", "COIN", "PYPL",
    # Healthcare
    "JNJ", "PFE", "UNH", "ABBV", "MRK", "LLY", "TMO", "ABT",
    # Consumer
    "WMT", "PG", "KO", "PEP", "MCD", "NKE", "SBUX", "DIS", "HD", "COST",
    # Energy / Industrial
    "XOM", "CVX", "BA", "CAT", "GE", "HON",
    # ETFs / Indices
    "SPY", "QQQ", "DIA", "IWM",
]


def _fmp_asset_row(quote: dict) -> dict | None:
    """orchard_capitals' top_traded item shape: {name, ticker, avg_profit, avg_loss, profitable_pct}."""
    change = quote.get("changePercentage")
    symbol = quote.get("symbol")
    if change is None or not symbol:
        return None
    change = round(float(change), 2)
    ticker = symbol[:-3] if symbol.endswith("USD") and symbol not in ("EURUSD", "GBPUSD", "USDJPY") else symbol
    return {
        "name":           quote.get("name") or ticker,
        "ticker":         ticker,
        "avg_profit":     abs(change) if change >= 0 else round(abs(change) * random.uniform(0.6, 1.2), 2),
        "avg_loss":       -round(abs(change) * random.uniform(0.6, 2.0) + random.uniform(0.5, 3), 2),
        "profitable_pct": round(min(97, max(42, 68 + change * 2.2)), 2),
    }


def _fetch_fmp_top_traded(n: int, time_budget: float = 6.0) -> list[dict]:
    """Best-effort: fetch up to `n` real quotes from FMP one symbol at a time
    (the current plan doesn't support batched multi-symbol quotes). Returns
    fewer than `n` — or an empty list — if FMP is slow/unreachable/rate-limited;
    the caller tops up any shortfall from the local JSON pool."""
    from core.fmp_client import get_stock_quotes

    candidates = _FMP_CRYPTO_SYMBOLS + _FMP_STOCK_SYMBOLS
    random.shuffle(candidates)

    rows, start = [], time.monotonic()
    for symbol in candidates:
        if len(rows) >= n or (time.monotonic() - start) > time_budget:
            break
        try:
            quotes = get_stock_quotes([symbol])
            if isinstance(quotes, list) and quotes:
                row = _fmp_asset_row(quotes[0])
                if row:
                    rows.append(row)
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 429:
                break  # plan/rate limit hit — stop hammering it, fall back for the rest
            continue   # one bad symbol shouldn't sink the whole batch
        except Exception:
            continue   # network hiccup/timeout on this symbol — try the next one
    return rows


def _top_traded(n: int) -> list[dict]:
    rows = []
    try:
        rows = _fetch_fmp_top_traded(n)
    except Exception:
        rows = []

    if len(rows) < n:
        used = {r["ticker"] for r in rows}
        pool = [a for a in _seed_data()["asset_pool"] if a["ticker"] not in used]
        random.shuffle(pool)
        for a in pool[: n - len(rows)]:
            rows.append({
                "name": a["name"], "ticker": a["ticker"],
                "avg_profit":     round(random.uniform(5, 45), 2),
                "avg_loss":       -round(random.uniform(1, 15), 2),
                "profitable_pct": round(random.uniform(45, 96), 2),
            })
    return rows[:n]


# ─────────────────────────────────────────────────────────────────────────────
# Percentage split helper (Portfolio Breakdown always sums to 100)
# ─────────────────────────────────────────────────────────────────────────────

def _split_percentages(n: int, total: int = 100) -> list[int]:
    if n <= 1:
        return [total]
    cuts = sorted(random.sample(range(1, total), n - 1))
    return [cuts[0]] + [cuts[i] - cuts[i - 1] for i in range(1, len(cuts))] + [total - cuts[-1]]


def random_portfolio_breakdown_rows(n: int = 4) -> list[dict]:
    """Public helper — orchard_capitals' portfolio_breakdown item shape: {name, percentage}."""
    pool  = _seed_data()["allocation_pool"]
    picks = random.sample(pool, min(n, len(pool)))
    pcts  = _split_percentages(len(picks))
    return [{"name": p["label"], "percentage": pct} for p, pct in zip(picks, pcts)]


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def seed_trader_demo_data(trader, rows: int = 6) -> None:
    """Fill top_traded / portfolio_breakdown / frequently_traded with `rows`
    random entries each, plus any Trader-level summary stat still at its
    default (0) — only touches fields the admin left untouched."""
    data = _seed_data()

    updates = {}
    if not trader.top_traded:
        updates["top_traded"] = _top_traded(rows)
    if not trader.portfolio_breakdown:
        updates["portfolio_breakdown"] = random_portfolio_breakdown_rows(min(rows, 4))
    if not trader.frequently_traded:
        pool = random.sample(data["asset_pool"], min(rows, len(data["asset_pool"])))
        updates["frequently_traded"] = [a["ticker"] for a in pool]

    if trader.gain == 0:                  updates["gain"]                  = round(random.uniform(5, 65), 2)
    if trader.total_wins == 0 and trader.total_losses == 0:
        wins   = random.randint(400, 1100)
        losses = random.randint(40, 220)
        updates["total_wins"]   = wins
        updates["total_losses"] = losses
    if trader.copiers == 0:               updates["copiers"]               = random.randint(20, 600)
    if trader.followers == 0:             updates["followers"]             = random.randint(50, 800)
    if trader.min_account_threshold == 0: updates["min_account_threshold"] = random.choice([50000, 75000, 100000, 150000])
    if trader.trading_days == 0:          updates["trading_days"]          = random.randint(500, 2600)
    if trader.max_drawdown == 0:          updates["max_drawdown"]          = round(random.uniform(3, 10), 2)
    if trader.cumulative_earnings_copiers == 0:
        updates["cumulative_earnings_copiers"] = round(random.uniform(10_000_000, 40_000_000), 2)
    if trader.cumulative_copiers == 0:    updates["cumulative_copiers"]    = random.randint(280, 650)
    if trader.trades == 0:                updates["trades"]                = random.randint(700, 1300)
    if trader.avg_profit_percent == 0:    updates["avg_profit_percent"]    = round(random.uniform(20, 40), 2)
    if trader.avg_loss_percent == 0:      updates["avg_loss_percent"]      = round(random.uniform(3, 7), 2)

    if updates:
        for field, value in updates.items():
            setattr(trader, field, value)
        trader.save(update_fields=list(updates.keys()))
