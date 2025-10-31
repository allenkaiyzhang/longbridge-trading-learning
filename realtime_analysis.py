import os
import argparse
from pathlib import Path
from datetime import datetime

from utils_symbols import read_symbols
from format_response import getBasicStatus, getStockDetails
from exchange_time_utils import add_exchange_time_fields, generate_deepseek_prompt
from deepseek_analysis import analyze_quote


def main():
    """
    Fetch real-time static data via LongPort, generate DeepSeek analysis, and save results.
    Symbols are read from a CSV file (config/symbols.csv by default).
    An optional extra prompt can be provided via CLI or environment variable.
    """
    parser = argparse.ArgumentParser(description="Generate DeepSeek analysis for real-time market data.")
    parser.add_argument("--symbols-csv", default="config/symbols.csv", help="CSV file containing symbols (header 'symbol').")
    parser.add_argument("--output-dir", default=os.environ.get("OUTPUT_DIR", "."), help="Directory to save analysis files.")
    parser.add_argument("--extra-prompt", default=os.environ.get("DEEPSEEK_EXTRA_PROMPT", ""), help="Additional instructions for DeepSeek.")
    args = parser.parse_args()

    # Load and normalize symbols
    symbols = read_symbols(Path(args.symbols_csv))

    # Fetch basic status and convert to details
    resp = getBasicStatus(symbols)
    details = getStockDetails(resp)

    # Enrich details with local and UTC time based on exchange
    enriched_records = add_exchange_time_fields(details)

    # Generate the prompt for DeepSeek
    prompt = generate_deepseek_prompt(enriched_records)
    if args.extra_prompt:
        prompt = f"{prompt}\n\n{args.extra_prompt}"

    # DeepSeek analysis
    analysis = analyze_quote([prompt])

    # Write to file
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = out_dir / f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("Prompt:\n")
        f.write(prompt + "\n\n")
        f.write("Analysis & Suggestions:\n")
        f.write(analysis + "\n")

    print(f"Analysis written to {filename}")


if __name__ == "__main__":
    main()
