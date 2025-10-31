import os
from openai import OpenAI
import argparse

# Base URL for the DeepSeek API. Can be overridden by setting DEEPSEEK_BASE_URL.
BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
API_KEY = os.getenv("DEEPSEEK_API_KEY")


def analyze_quote(symbol: str, price: float, extra_prompt: str | None = None) -> str:
    """
    Analyze a real-time quote using DeepSeek API.

    Parameters:
        symbol: stock symbol such as "700.HK" or "AAPL.US".
        price: latest price as a float.
        extra_prompt: optional additional instructions to be appended to the prompt.

    Returns:
        A string containing the analysis returned by the model.
    """
    if not API_KEY:
        raise ValueError("DEEPSEEK_API_KEY is not set in environment variables")

    # Initialize OpenAI client pointing to the DeepSeek endpoint.
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    # Construct the user message for analysis.
    prompt_parts = [
        f"You are a professional stock analyst. Provide a concise analysis of the current market condition for {symbol} at price {price}.",
    ]
    if extra_prompt:
        prompt_parts.append(extra_prompt)
    user_message = "\n".join(prompt_parts)

    messages = [
        {"role": "user", "content": user_message}
    ]

    # Call the DeepSeek reasoning model (deepseek-reasoner) via OpenAI SDK.
    response = client.chat.completions.create(
        model="deepseek-reasoner",
        messages=messages,
        stream=False,
    )

    # Extract the content from the response. The reasoning model may include reasoning_content; we return only the final content.
    result = ""
    if response and response.choices:
        msg = response.choices[0].message
        # 'message' may have attributes like 'reasoning_content' in the SDK; use getattr to safely access.
        content = getattr(msg, "content", None)
        if content:
            result = content

    return result


if __name__ == "__main__":
    """
    Minimal CLI: accept symbol and price from command-line arguments or environment variables and print analysis.

    Usage:
        python deepseek_analysis.py SYMBOL PRICE
    Example:
        python deepseek_analysis.py 700.HK 50.0
    """
    parser = argparse.ArgumentParser(description="DeepSeek quote analysis")
    parser.add_argument("symbol", nargs="?", default=os.getenv("QUOTE_SYMBOL", "700.HK"), help="Stock symbol")
    parser.add_argument("price", nargs="?", type=float, default=float(os.getenv("QUOTE_PRICE", "0.0")), help="Latest price")
    # Add optional parameters for future prompt support
    parser.add_argument("--prompt-module", dest="prompt_module", default=None, help="Prompt module name (optional)")
    parser.add_argument("--scenario", dest="scenario", default=None, help="Scenario name (optional)")
    args = parser.parse_args()

    symbol = args.symbol
    price = args.price
    # Note: prompt_module and scenario are parsed but not used in this script
    analysis = analyze_quote(symbol, price)
    print(analysis)