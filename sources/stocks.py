from __future__ import annotations

import logging

import config

logger = logging.getLogger(__name__)


def fetch_stock_data() -> dict:
    """Fetch closing stock prices for TAVR industry companies using yfinance."""
    try:
        import yfinance as yf
    except ImportError:
        logger.error("yfinance not installed. Run: pip install yfinance")
        return {}

    results = {}

    for ticker, company in config.STOCK_TICKERS.items():
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")

            if hist.empty or len(hist) < 1:
                logger.warning(f"No data for {ticker}")
                continue

            # Latest closing price
            latest = hist.iloc[-1]
            close_price = latest["Close"]
            close_date = hist.index[-1].strftime("%Y-%m-%d")

            # Calculate daily change
            if len(hist) >= 2:
                prev_close = hist.iloc[-2]["Close"]
                change = close_price - prev_close
                change_pct = (change / prev_close) * 100
            else:
                change = 0.0
                change_pct = 0.0

            # 5-day high/low
            high_5d = hist["High"].max()
            low_5d = hist["Low"].min()
            volume = int(latest["Volume"])

            # Get analyst target price if available
            try:
                info = stock.info
                target_price = info.get("targetMeanPrice")
                target_low = info.get("targetLowPrice")
                target_high = info.get("targetHighPrice")
                recommendation = info.get("recommendationKey", "")
                num_analysts = info.get("numberOfAnalystOpinions", 0)
            except Exception:
                target_price = None
                target_low = None
                target_high = None
                recommendation = ""
                num_analysts = 0

            results[ticker] = {
                "company": company,
                "ticker": ticker,
                "close_price": round(close_price, 2),
                "close_date": close_date,
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "high_5d": round(high_5d, 2),
                "low_5d": round(low_5d, 2),
                "volume": volume,
                "target_price": round(target_price, 2) if target_price else None,
                "target_low": round(target_low, 2) if target_low else None,
                "target_high": round(target_high, 2) if target_high else None,
                "recommendation": recommendation,
                "num_analysts": num_analysts,
            }

            logger.info(f"{ticker} ({company}): ${close_price:.2f} ({change_pct:+.2f}%)")

        except Exception as e:
            logger.warning(f"Failed to fetch {ticker} ({company}): {e}")

    # Note private companies
    for company in config.PRIVATE_COMPANIES:
        logger.info(f"{company}: private company (no stock data)")

    return results
