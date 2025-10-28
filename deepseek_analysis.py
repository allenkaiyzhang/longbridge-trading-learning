import os
from openai import OpenAI

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
    import sys

    symbol = sys.argv[1] if len(sys.argv) > 1 else os.getenv("QUOTE_SYMBOL", "700.HK")
    price_str = sys.argv[2] if len(sys.argv) > 2 else os.getenv("QUOTE_PRICE", "0.0")
    try:
        price = float(price_str)
    except ValueError:
        price = 0.0

    analysis = analyze_quote(symbol, price)
    print(analysis)
