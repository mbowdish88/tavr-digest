from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from urllib.parse import quote

import config

logger = logging.getLogger(__name__)

QUICKCHART_BASE = "https://quickchart.io/chart"


def _build_chart_url(all_histories: dict) -> str:
    """Build a QuickChart.io URL for a multi-line 6-month closing price chart."""
    colors = [
        "rgb(54, 162, 235)",   # blue
        "rgb(255, 99, 132)",   # red
        "rgb(75, 192, 192)",   # teal
        "rgb(255, 159, 64)",   # orange
        "rgb(153, 102, 255)",  # purple
    ]

    datasets = []
    labels = None

    for i, (ticker, data) in enumerate(all_histories.items()):
        dates = data["dates"]
        closes = data["closes"]

        if labels is None:
            labels = dates
        elif len(dates) > len(labels):
            labels = dates

        datasets.append({
            "label": f"{ticker} ({data['company']})",
            "data": closes,
            "borderColor": colors[i % len(colors)],
            "backgroundColor": "transparent",
            "borderWidth": 2,
            "pointRadius": 0,
            "tension": 0.3,
        })

    chart_config = {
        "type": "line",
        "data": {
            "labels": labels,
            "datasets": datasets,
        },
        "options": {
            "title": {
                "display": True,
                "text": "Valve Industry - 6 Month Closing Prices",
                "fontSize": 16,
            },
            "scales": {
                "xAxes": [{"ticks": {"maxTicksLimit": 8, "fontSize": 10}}],
                "yAxes": [{"ticks": {"fontSize": 10, "prefix": "$"}}],
            },
            "legend": {"position": "bottom", "labels": {"fontSize": 11}},
        },
    }

    config_json = json.dumps(chart_config, separators=(",", ":"))
    return f"{QUICKCHART_BASE}?c={quote(config_json)}&w=680&h=400&bkg=white"


def _build_individual_chart_url(ticker: str, company: str, dates: list, closes: list) -> str:
    """Build a QuickChart.io URL for an individual stock's 6-month chart."""
    # Determine color based on trend
    if len(closes) >= 2:
        color = "rgb(34, 139, 34)" if closes[-1] >= closes[0] else "rgb(220, 20, 60)"
    else:
        color = "rgb(54, 162, 235)"

    chart_config = {
        "type": "line",
        "data": {
            "labels": dates,
            "datasets": [{
                "label": f"{ticker}",
                "data": closes,
                "borderColor": color,
                "backgroundColor": "rgba(54, 162, 235, 0.1)",
                "borderWidth": 2,
                "pointRadius": 0,
                "fill": True,
                "tension": 0.3,
            }],
        },
        "options": {
            "title": {
                "display": True,
                "text": f"{company} ({ticker}) - 6 Month",
                "fontSize": 14,
            },
            "scales": {
                "xAxes": [{"ticks": {"maxTicksLimit": 6, "fontSize": 10}}],
                "yAxes": [{"ticks": {"fontSize": 10, "prefix": "$"}}],
            },
            "legend": {"display": False},
        },
    }

    config_json = json.dumps(chart_config, separators=(",", ":"))
    return f"{QUICKCHART_BASE}?c={quote(config_json)}&w=680&h=300&bkg=white"


def fetch_stock_data() -> dict:
    """Fetch detailed stock data with 6-month history, earnings, and events."""
    try:
        import yfinance as yf
    except ImportError:
        logger.error("yfinance not installed. Run: pip install yfinance")
        return {}

    results = {}
    all_histories = {}

    for ticker, company in config.STOCK_TICKERS.items():
        try:
            stock = yf.Ticker(ticker)

            # 6-month history for charts
            hist_6m = stock.history(period="6mo")
            if hist_6m.empty or len(hist_6m) < 1:
                logger.warning(f"No data for {ticker}")
                continue

            # Latest data from 6-month history
            hist_5d = hist_6m.tail(5)
            latest = hist_6m.iloc[-1]
            close_price = latest["Close"]
            close_date = hist_6m.index[-1].strftime("%Y-%m-%d")

            # Daily change
            if len(hist_6m) >= 2:
                prev_close = hist_6m.iloc[-2]["Close"]
                change = close_price - prev_close
                change_pct = (change / prev_close) * 100
            else:
                change = 0.0
                change_pct = 0.0

            # 5-day and 6-month high/low
            high_5d = hist_5d["High"].max()
            low_5d = hist_5d["Low"].min()
            high_6m = hist_6m["High"].max()
            low_6m = hist_6m["Low"].min()
            volume = int(latest["Volume"])

            # 6-month performance
            first_close = hist_6m.iloc[0]["Close"]
            change_6m = close_price - first_close
            change_6m_pct = (change_6m / first_close) * 100

            # Store history for combined chart
            # Sample every few days to keep URL manageable
            step = max(1, len(hist_6m) // 60)
            sampled = hist_6m.iloc[::step]
            # Always include the last data point
            if hist_6m.index[-1] not in sampled.index:
                sampled = hist_6m.iloc[list(range(0, len(hist_6m), step)) + [-1]]

            dates = [d.strftime("%b %d") for d in sampled.index]
            closes = [round(c, 2) for c in sampled["Close"]]

            all_histories[ticker] = {
                "company": company,
                "dates": dates,
                "closes": closes,
            }

            # Analyst data
            try:
                info = stock.info
                target_price = info.get("targetMeanPrice")
                target_low = info.get("targetLowPrice")
                target_high = info.get("targetHighPrice")
                recommendation = info.get("recommendationKey", "")
                num_analysts = info.get("numberOfAnalystOpinions", 0)
                market_cap = info.get("marketCap")
                pe_ratio = info.get("trailingPE")
                forward_pe = info.get("forwardPE")
                beta = info.get("beta")
                fifty_two_high = info.get("fiftyTwoWeekHigh")
                fifty_two_low = info.get("fiftyTwoWeekLow")
            except Exception:
                target_price = target_low = target_high = None
                recommendation = ""
                num_analysts = 0
                market_cap = pe_ratio = forward_pe = beta = None
                fifty_two_high = fifty_two_low = None

            # Earnings calendar
            next_earnings_date = None
            earnings_estimate = None
            revenue_estimate = None
            try:
                cal = stock.calendar
                if cal and isinstance(cal, dict):
                    earnings_dates = cal.get("Earnings Date", [])
                    if earnings_dates:
                        next_earnings_date = str(earnings_dates[0])
                    earnings_estimate = cal.get("Earnings Average")
                    revenue_estimate = cal.get("Revenue Average")
            except Exception:
                pass

            # Recent company-specific news / events
            stock_events = []
            try:
                news_items = getattr(stock, "news", None)
                if news_items:
                    for item in news_items[:5]:
                        title = item.get("title", "")
                        link = item.get("link", "")
                        publisher = item.get("publisher", "")
                        pub_ts = item.get("providerPublishTime")
                        pub_date = ""
                        if pub_ts:
                            pub_date = datetime.fromtimestamp(pub_ts, tz=timezone.utc).strftime("%Y-%m-%d")
                        if title:
                            stock_events.append({
                                "title": title,
                                "url": link,
                                "source": publisher,
                                "date": pub_date,
                            })
            except Exception:
                pass

            # Individual chart URL
            individual_chart_url = _build_individual_chart_url(ticker, company, dates, closes)

            results[ticker] = {
                "company": company,
                "ticker": ticker,
                "close_price": round(close_price, 2),
                "close_date": close_date,
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "high_5d": round(high_5d, 2),
                "low_5d": round(low_5d, 2),
                "high_6m": round(high_6m, 2),
                "low_6m": round(low_6m, 2),
                "change_6m": round(change_6m, 2),
                "change_6m_pct": round(change_6m_pct, 2),
                "volume": volume,
                "market_cap": market_cap,
                "pe_ratio": round(pe_ratio, 2) if pe_ratio else None,
                "forward_pe": round(forward_pe, 2) if forward_pe else None,
                "beta": round(beta, 2) if beta else None,
                "fifty_two_high": round(fifty_two_high, 2) if fifty_two_high else None,
                "fifty_two_low": round(fifty_two_low, 2) if fifty_two_low else None,
                "target_price": round(target_price, 2) if target_price else None,
                "target_low": round(target_low, 2) if target_low else None,
                "target_high": round(target_high, 2) if target_high else None,
                "recommendation": recommendation,
                "num_analysts": num_analysts,
                "next_earnings_date": next_earnings_date,
                "earnings_estimate": round(earnings_estimate, 2) if earnings_estimate else None,
                "revenue_estimate": revenue_estimate,
                "events": stock_events,
                "chart_url": individual_chart_url,
            }

            logger.info(
                f"{ticker} ({company}): ${close_price:.2f} ({change_pct:+.2f}%) | "
                f"6M: {change_6m_pct:+.1f}% | "
                f"Earnings: {next_earnings_date or 'N/A'}"
            )

        except Exception as e:
            logger.warning(f"Failed to fetch {ticker} ({company}): {e}")

    # Build combined chart URL
    if all_histories:
        combined_chart_url = _build_chart_url(all_histories)
        # Store it in a special key
        results["_combined_chart_url"] = combined_chart_url
        logger.info("Generated combined 6-month stock chart URL")

    # Note private companies
    for company in config.PRIVATE_COMPANIES:
        logger.info(f"{company}: private company (no stock data)")

    return results
