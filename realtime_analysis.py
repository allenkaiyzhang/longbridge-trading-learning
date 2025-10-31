import os
import csv
import argparse
from pathlib import Path
from datetime import datetime
from longport.openapi import Config, QuoteContext
from deepseek_analysis import analyze_quote
from utils_symbols import read_symbols
from format_response import getBasicStatus,getDetails
from exchange_time_utils import add_exchange_time_fields,generate_prompt_with_time
import json

def main():
    """
    Fetch real-time quotes via LongPort, run DeepSeek analysis with suggestions,
    and save results to a text file while updating an index CSV.

    Symbols are read from a CSV file (config/symbols.csv by default). You can override the path with the --symbols-csv argument.

    The DeepSeek API key and optional base URL should be set via environment variables
    (DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL). The output directory can be set with OUTPUT_DIR;
    defaults to the current directory. An optional extra prompt for the DeepSeek model can be set
    via DEEPSEEK_EXTRA_PROMPT.
    """
    # Fetch quotes
    symbol=getSymbols("./symbol.txt")
    response=getBasicStatus(symbol)
    details=getDetails(response)
    prompt=generate_prompt_with_time(details)
    deepseek_analysis=analyze_quote(prompt)
    writePromptAndOutput(symbol,prompt,deepseek_analysis)
    

def writePromptAndOutput(symbol,prompt,results):
    # Write full analyses to a timestamped text file
    out_dir = os.environ.get("OUTPUT_DIR", ".")
    os.makedirs(out_dir, exist_ok=True)
    txt_filename = os.path.join(
        out_dir, f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    )
    with open(txt_filename, "w", encoding="utf-8") as txt_file:
        txt_file.write("Prompt:\n")
        txt_file.write(prompt+"\n")
        txt_file.write("Analysis & Suggestions:\n")
        txt_file.write(results)
        txt_file.write("\n\n")


def getSymbols(filepath="./symbol.txt"):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]  # 去掉空行和换行符
        print(f"读取到 {len(lines)} 条记录。")
    return lines


if __name__ == "__main__":
    main()
