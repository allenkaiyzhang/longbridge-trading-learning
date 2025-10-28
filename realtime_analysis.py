import os
import csv
from datetime import datetime
from longport.openapi import Config, QuoteContext
from deepseek_analysis import analyze_quote


def main():
    """
    Fetch real-time quotes via LongPort, run DeepSeek analysis with suggestions,
    and save results to a text file while updating an index CSV.

    Symbols are read from the SYMBOLS environment variable (comma-separated).
    The DeepSeek API key and optional base URL should be set via environment variables
    (DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL). The output directory can be set with OUTPUT_DIR;
    defaults to the current directory. An optional extra prompt for the DeepSeek model can be set
    via DEEPSEEK_EXTRA_PROMPT.
    """
    # Load LongPort configuration and create a quote context
    cfg = Config.from_env()
    ctx = QuoteContext(cfg)

    # Parse symbols from environment
    symbols_env = os.environ.get("SYMBOLS", "")
    symbols = [s.strip().upper() for s in symbols_env.split(",") if s.strip()]
    if not symbols:
        raise RuntimeError(
            "No symbols specified in SYMBOLS environment variable. Example: '700.HK,AAPL.US'"
        )

    # Fetch quotes
    quotes = ctx.quote(symbols)

    # Output directory and extra prompt
    out_dir = os.environ.get("OUTPUT_DIR", ".")
    os.makedirs(out_dir, exist_ok=True)
    extra_prompt = os.environ.get(
        "DEEPSEEK_EXTRA_PROMPT",
        "Additionally, provide actionable suggestions for this situation.",
    )

    # Collect results to avoid multiple API calls per symbol
    results = []
    for q in quotes:
        price = getattr(q, "last_done", None)
        try:
            price_float = float(price) if price is not None else 0.0
        except Exception:
            price_float = 0.0
        analysis = analyze_quote(q.symbol, price_float, extra_prompt)
        results.append({
            "symbol": q.symbol,
            "price": price,
            "analysis": analysis,
        })

    # Timestamp for the index file
    timestamp = datetime.now().isoformat()

    # Write full analyses to a timestamped text file
    txt_filename = os.path.join(
        out_dir, f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    )
    with open(txt_filename, "w", encoding="utf-8") as txt_file:
        for item in results:
            txt_file.write(f"Symbol: {item['symbol']}\n")
            txt_file.write(f"Price: {item['price']}\n")
            txt_file.write("Analysis & Suggestions:\n")
            txt_file.write(item["analysis"].strip())
            txt_file.write("\n\n")

    # Append summaries to index.csv (create header if file doesn't exist)
    index_path = os.path.join(out_dir, "index.csv")
    file_exists = os.path.exists(index_path)
    with open(index_path, "a", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        if not file_exists:
            writer.writerow(["datetime", "symbol", "summary"])
        for item in results:
            summary = item["analysis"].strip().replace("\n", " ")
            summary_short = summary[:200]
            writer.writerow([timestamp, item["symbol"], summary_short])

    # Print to console
    for item in results:
        print(f"{item['symbol']}: price={item['price']}")
        print(item["analysis"])
        print("-" * 40)

if __name__ == "__main__":
    main()
