"""
Compute simple day-trading indicators from your daily prices JSON
and fundamentals JSON.

Outputs a signals JSON with:
  - close_return_1d
  - gap_pct
  - day_range_pct
  - volume_ratio
  - vol_10d (10-day volatility of returns)
  - in_play_score (naive combined score)
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
import math
import statistics


# ---------- Helpers to load JSON ----------

def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_repo_root() -> Path:
    # Adjust if you ever move this file
    return Path(__file__).resolve().parents[2]


# ---------- Core indicator logic ----------

def compute_daily_returns(prices: List[Dict[str, Any]]) -> List[float]:
    """
    Compute simple daily returns from a list of OHLCV rows.
    Assumes rows are in chronological order (oldest -> newest).
    return_t = (close_t / close_{t-1}) - 1
    """
    closes = [row["close"] for row in prices]
    returns: List[float] = []
    for i in range(1, len(closes)):
        prev = closes[i - 1]
        curr = closes[i]
        if prev is None or prev == 0:
            continue
        returns.append((curr / prev) - 1.0)
    return returns


def compute_indicators_for_symbol(
    symbol: str,
    daily_prices: List[Dict[str, Any]],
    fundamentals: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Compute derived indicators for one symbol combining:
      - daily prices (for returns, volatility)
      - fundamentals["trading_snapshot"] (for volume & today's context)
    """
    if len(daily_prices) < 2:
        return {}

    # Ensure prices are sorted by date (just in case)
    daily_prices_sorted = sorted(daily_prices, key=lambda row: row["date"])

    last = daily_prices_sorted[-1]
    prev = daily_prices_sorted[-2]

    last_close = last["close"]
    prev_close = prev["close"]

    # 1-day close-to-close return
    close_return_1d: Optional[float] = None
    if prev_close:
        close_return_1d = (last_close / prev_close) - 1.0

    # Pull trading snapshot from fundamentals (may be missing some fields)
    trading_snapshot = fundamentals.get("trading_snapshot", {})
    today_open = trading_snapshot.get("regularMarketOpen")
    today_high = trading_snapshot.get("regularMarketDayHigh")
    today_low = trading_snapshot.get("regularMarketDayLow")
    today_volume = trading_snapshot.get("regularMarketVolume")
    avg_vol_10d = trading_snapshot.get("averageDailyVolume10Day")
    prev_close_ref = trading_snapshot.get("regularMarketPreviousClose")

    # Gap %: using snapshot prev close & today open if available, else fall back
    gap_pct: Optional[float] = None
    base_prev_close = prev_close_ref or prev_close
    if base_prev_close and today_open:
        gap_pct = (today_open / base_prev_close) - 1.0

    # Day range % = (high - low) / open
    day_range_pct: Optional[float] = None
    if today_open and today_high and today_low:
        if today_open != 0:
            day_range_pct = (today_high - today_low) / today_open

    # Volume ratio = today volume / avg 10-day volume
    volume_ratio: Optional[float] = None
    if today_volume and avg_vol_10d:
        if avg_vol_10d != 0:
            volume_ratio = today_volume / avg_vol_10d

    # 10-day volatility of daily returns
    returns = compute_daily_returns(daily_prices_sorted)
    vol_10d: Optional[float] = None
    if len(returns) >= 2:
        # Use last up-to-10 returns
        window = returns[-10:]
        if len(window) >= 2:
            vol_10d = statistics.stdev(window)

    # Simple "in play" score (completely naive but useful for ranking):
    # - bigger gap, bigger range, higher volume_ratio -> higher score
    # - scale things so they don't explode
    in_play_score = 0.0

    if gap_pct is not None:
        in_play_score += min(abs(gap_pct) * 100, 50)   # cap contribution

    if day_range_pct is not None:
        in_play_score += min(day_range_pct * 100, 30)

    if volume_ratio is not None:
        in_play_score += min(max(volume_ratio - 1.0, 0.0) * 10, 40)

    # tiny bonus for higher 10d vol (spicier stock)
    if vol_10d is not None:
        in_play_score += min(vol_10d * 100, 30)

    return {
        "symbol": symbol,
        "close_return_1d": close_return_1d,
        "gap_pct": gap_pct,
        "day_range_pct": day_range_pct,
        "volume_ratio": volume_ratio,
        "vol_10d": vol_10d,
        "in_play_score": in_play_score,
    }


def main() -> None:
    root = get_repo_root()

    prices_path = root / "u_stock_learning" / "fetchers" / "data" / "prices-sample.json"
    fundamentals_path = root / "u_stock_learning" / "fetchers" / "data" / "fundamentals-slim.json"

    prices_json = load_json(prices_path)
    fundamentals_json = load_json(fundamentals_path)

    prices_by_symbol: Dict[str, List[Dict[str, Any]]] = prices_json["prices"]
    fundamentals_by_symbol: Dict[str, Dict[str, Any]] = fundamentals_json["data"]

    signals: Dict[str, Any] = {}

    for symbol, price_rows in prices_by_symbol.items():
        fund = fundamentals_by_symbol.get(symbol, {})
        indicators = compute_indicators_for_symbol(symbol, price_rows, fund)
        if indicators:
            signals[symbol] = indicators

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "symbols": list(signals.keys()),
        "signals": signals,
    }

    out_path = root / "u_stock_learning" / "fetchers" / "data" / "signals-today.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"Saved signals to {out_path}")


if __name__ == "__main__":
    main()
