import os
import time
from longport.openapi import Config, QuoteContext, SubType


def main():
    """Subscribe to real-time quotes for symbols specified in the SYMBOLS environment variable."""
    # Load credentials from environment
    app_key = os.environ.get("LONGPORT_APP_KEY")
    app_secret = os.environ.get("LONGPORT_APP_SECRET")
    access_token = os.environ.get("LONGPORT_ACCESS_TOKEN")
    if not all([app_key, app_secret, access_token]):
        raise RuntimeError("LONGPORT_APP_KEY, LONGPORT_APP_SECRET and LONGPORT_ACCESS_TOKEN must be set in the environment")

    symbols_env = os.environ.get("SYMBOLS", "")
    symbols = [s.strip().upper() for s in symbols_env.split(",") if s.strip()]
    if not symbols:
        raise RuntimeError("Specify one or more symbols in the SYMBOLS environment variable, e.g. '700.HK,AAPL.US'")

    # Optional endpoints for test environments
    http_url = os.environ.get("LONGPORT_HTTP_URL")
    quote_ws_url = os.environ.get("LONGPORT_QUOTE_WS_URL")

    # Initialize SDK config from environment
    cfg = Config.from_env()
    # Override endpoints if provided
    if http_url:
        cfg.http_url = http_url
    if quote_ws_url:
        cfg.quote_ws_url = quote_ws_url

    # Create quote context
    ctx = QuoteContext(cfg)

    # Subscribe to real-time quotes (SubType.Quote) and receive initial snapshot
    ctx.subscribe(symbols, SubType.Quote, is_first_push=True)

    @ctx.set_on_quote
    def handle_quote(symbol: str, quote):
        # Print simple real-time quote info; you can extend this to log or persist data as needed
        last_price = getattr(quote, "last_price", None)
        timestamp = getattr(quote, "timestamp", None)
        print(f"{symbol}: last_price={last_price}, timestamp={timestamp}")

    try:
        # Keep the event loop running to receive quote updates
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping subscription...")
    finally:
        ctx.close()


if __name__ == "__main__":
    main()
