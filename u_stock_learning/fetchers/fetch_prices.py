from yahooquery import Ticker
from datetime import datetime, timezone
from pathlib import Path
import json
from typing import Dict, Any, List


def fetch_prices(symbols: List[str]):
    """
    Fetch daily OHLCV price data for a list of symbols using the Yahoo Finance
    API via yahooquery (stable JSON API).

    :param symbols: List of ticker strings, e.g., ["AAPL", "MSFT"]
    :return: Dictionary mapping each symbol to a DataFrame of historical prices.
    """
    data = {}  # Will hold symbol -> DataFrame mappings

    for symbol in symbols:
        print(f"Fetching {symbol}...")

        # Create a Ticker object for the symbol.
        # yahooquery makes a real JSON API call to Yahoo (no scraping).
        t = Ticker(symbol)

        try:
            # Fetch daily historical price data for ~1 month.
            df = t.history(period="1mo", interval="1d")

        except Exception as e:
            print(f"  ERROR fetching {symbol}: {e}")
            continue

        # If yahooquery returns nothing (empty DataFrame)
        if df is None or len(df) == 0:
            print(f"  Warning: no data for {symbol}")
            continue

        # yahooquery sometimes returns a multi-index (symbol, date).
        # Reset index so the DataFrame uses normal integer rows and has "date" as a column.
        df = df.reset_index()

        # Store DataFrame under the symbol key
        data[symbol] = df

    return data


def prices_to_json_ready(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert the raw {symbol -> DataFrame} mapping into a JSON-friendly structure
    with only the core fields we care about.

    Output shape:

    {
      "generated_at": "...",
      "symbols": ["AAPL", "MSFT", ...],
      "prices": {
        "AAPL": [
          {
            "date": "...",
            "open": ...,
            "high": ...,
            "low": ...,
            "close": ...,
            "volume": ...,
            "adjclose": ...
          },
          ...
        ],
        "MSFT": [ ... ]
      }
    }
    """
    prices: Dict[str, Any] = {}

    for symbol, df in data.items():
        # Keep only the columns we care about.
        # Some symbols might not have adjclose; use .get with fallback.
        cols = [c for c in df.columns if c in ("date", "open", "high", "low", "close", "volume", "adjclose")]

        subset = df[cols].copy()

        # Convert DataFrame -> list of dict rows
        records = []
        for row in subset.to_dict(orient="records"):
            # Convert datetime/Timestamp to ISO string
            if isinstance(row.get("date"), (str,)):
                pass
            else:
                row["date"] = str(row["date"])
            records.append(row)

        prices[symbol] = records


    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "symbols": list(data.keys()),
        "prices": prices,
    }


def save_prices_json(json_obj: Dict[str, Any], filename: str = "prices-sample.json") -> Path:
    """
    Save the given JSON-serializable object into u_stock_learning/data/<filename>.

    Creates the data/ directory if it does not exist.
    """
    # Directory of this file (u_stock_learning/)
    base_dir = Path(__file__).resolve().parent

    # data/ folder inside u_stock_learning
    data_dir = base_dir / "data"
    data_dir.mkdir(exist_ok=True)

    output_path = data_dir / filename

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(json_obj, f, indent=2)

    print(f"\nSaved price snapshot to {output_path}")
    return output_path


def main():
    symbols = ["AAPL", "MSFT", "GOOG"]

    # Fetch price data for each ticker.
    prices = fetch_prices(symbols)

    print("\n=== SUMMARY ===")
    for symbol, df in prices.items():
        # First (oldest) and last (most recent) rows of the price DataFrame
        first = df.iloc[0]
        last = df.iloc[-1]

        # Print a readable summary for each symbol
        print(
            f"{symbol}: {len(df)} rows "
            f"from {first['date']} → {last['date']} "
            f"(open={first['open']:.2f}, close={last['close']:.2f})"
        )

    # Optional preview of AAPL’s first few rows
    if "AAPL" in prices:
        print("\nAAPL head():")
        print(prices["AAPL"].head())

    # Turn prices into a compact JSON structure and save it
    json_obj = prices_to_json_ready(prices)
    save_prices_json(json_obj, "prices-sample.json")


if __name__ == "__main__":
    # Run main() only when executed directly.
    main()
