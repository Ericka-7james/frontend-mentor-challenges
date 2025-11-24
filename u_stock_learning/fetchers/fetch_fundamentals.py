"""
Fetch *slim* fundamentals, company profile, and institutional ownership
for a list of symbols using yahooquery.

This is a learning version of what your real u-stock data bot might do,
but with a much smaller, analysis-focused schema.
"""

import json
from pathlib import Path
from typing import Dict, Any, List

from yahooquery import Ticker


def pick_keys(source: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
    """
    Helper: return a new dict containing only the given keys from source.
    Missing keys are ignored.
    """
    return {k: source.get(k) for k in keys if k in source}


def fetch_company_fundamentals_slim(symbols: List[str]) -> Dict[str, Any]:
    """
    Fetch *slim* fundamentals & profile-like data for each symbol.

    For each symbol we keep:
      - company_profile: sector, industry, country, website, summary, employees
      - key_stats: beta, bookValue, priceToBook, 52WeekChange, heldPercentInstitutions, sharesOutstanding
      - financial_data: currentPrice, revenue, margins, leverage, free cash flow
      - institution_ownership: top 5 holders (organization, pctHeld, position, value)

    :param symbols: list of ticker strings, e.g. ["AAPL", "MSFT"]
    :return: dict mapping symbol -> fundamentals payload (nested dict)
    """
    results: Dict[str, Any] = {}

    for symbol in symbols:
        print(f"Fetching fundamentals for {symbol}...")

        t = Ticker(symbol)
        payload: Dict[str, Any] = {}

        # --- Company profile / "About" (slimmed) ---
        try:
            raw_profile = t.asset_profile.get(symbol, {})  # type: ignore[union-attr]
        except Exception as e:
            print(f"  Warning: error fetching asset_profile for {symbol}: {e}")
            raw_profile = {}

        payload["company_profile"] = pick_keys(
            raw_profile,
            [
                "sector",
                "industry",
                "country",
                "website",
                "longBusinessSummary",
                "fullTimeEmployees",
            ],
        )

        # --- Key statistics (slim) ---
        try:
            raw_key_stats = t.key_stats.get(symbol, {})  # type: ignore[union-attr]
        except Exception as e:
            print(f"  Warning: error fetching key_stats for {symbol}: {e}")
            raw_key_stats = {}

        payload["key_stats"] = pick_keys(
            raw_key_stats,
            [
                "beta",
                "bookValue",
                "priceToBook",
                "52WeekChange",
                "heldPercentInstitutions",
                "sharesOutstanding",
            ],
        )

        # --- Financial data (slim) ---
        try:
            raw_fin = t.financial_data.get(symbol, {})  # type: ignore[union-attr]
        except Exception as e:
            print(f"  Warning: error fetching financial_data for {symbol}: {e}")
            raw_fin = {}

        payload["financial_data"] = pick_keys(
            raw_fin,
            [
                "currentPrice",
                "totalRevenue",
                "revenueGrowth",
                "grossMargins",
                "operatingMargins",
                "profitMargins",
                "debtToEquity",
                "freeCashflow",
            ],
        )

        # --- Institutional ownership (top 5, slim) ---
        slim_inst_list: List[Dict[str, Any]] = []
        try:
            inst_own = t.institution_ownership
            if inst_own is not None:
                try:
                    records = inst_own.to_dict("records")  # DataFrame-like
                except AttributeError:
                    # Already dict-like (fallback)
                    records = inst_own  # type: ignore[assignment]

                # Keep top 5 entries and slim to key fields
                for row in records[:5]:
                    slim_inst_list.append(
                        pick_keys(
                            row,
                            ["organization", "pctHeld", "position", "value"],
                        )
                    )
        except Exception as e:
            print(f"  Warning: error fetching institution_ownership for {symbol}: {e}")

        payload["institution_ownership"] = slim_inst_list

        results[symbol] = payload

    return results


def save_fundamentals_to_json(data: Dict[str, Any], filename: str = "fundamentals-slim.json") -> Path:
    """
    Save fundamentals payload to a JSON file inside u_stock_learning/fetchers/data/.

    Final JSON structure:

    {
      "symbols": ["AAPL", "MSFT"],
      "data": {
        "AAPL": {
          "company_profile": { ... },
          "key_stats": { ... },
          "financial_data": { ... },
          "institution_ownership": [ ... ]
        },
        "MSFT": { ... }
      }
    }
    """
    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / "data"
    data_dir.mkdir(exist_ok=True)

    output_path = data_dir / filename

    wrapper = {
        "symbols": list(data.keys()),
        "data": data,
    }

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(wrapper, f, indent=2)

    print(f"\nSaved fundamentals snapshot to {output_path}")
    return output_path


def main() -> None:
    symbols = ["AAPL", "MSFT", "GOOG"]

    fundamentals = fetch_company_fundamentals_slim(symbols)

    save_fundamentals_to_json(fundamentals, "fundamentals-slim.json")


if __name__ == "__main__":
    main()
