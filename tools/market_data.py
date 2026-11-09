import pandas as pd
import yfinance as yf
from smolagents import tool

# Representative ETFs for the indices Cava Bot tracks
DEFAULT_ASSETS = {
    "MSCI World (iShares URTH)": "URTH",
    "Vanguard Emerging Markets": "VWO",
    "Bitcoin": "BTC-USD",
}


def _currency(asset) -> str:
    """Quote currency of the asset (e.g. 'USD'), so the LLM never has to guess it."""
    try:
        return " " + asset.fast_info["currency"]
    except Exception:
        return ""


def _quote_line(name: str, ticker: str, period: str = "5d") -> str:
    """Returns one line with the latest close and the change vs. the previous close."""
    try:
        asset = yf.Ticker(ticker)
        history = asset.history(period=period)
        if history.empty:
            return f"- {name} ({ticker}): no data. Is the ticker valid?"
        last_close = history["Close"].iloc[-1]
        price = f"{last_close:,.2f}{_currency(asset)}"
        if len(history) >= 2:
            prev_close = history["Close"].iloc[-2]
            change = ((last_close - prev_close) / prev_close) * 100
            line = f"- {name} ({ticker}): {price} ({change:+.2f}% vs. previous close)"
        else:
            # Only one session available (weekend/holiday)
            line = f"- {name} ({ticker}): {price} (market closed / no change)"
        if len(history) >= 3:
            first_close = history["Close"].iloc[0]
            period_change = ((last_close - first_close) / first_close) * 100
            line += f" | {period_change:+.2f}% over {period}"
        return line + f" | date: {history.index[-1].date()}"
    except Exception as e:
        return f"- {name} ({ticker}): error fetching data ({e})"


@tool
def get_asset_quote(ticker: str, period: str = "5d") -> str:
    """Gets the latest closing price of a stock, ETF, index or crypto from Yahoo Finance, its change vs. the previous close and its change over the requested period.
    Args:
        ticker: Yahoo Finance ticker symbol, e.g. 'AAPL', 'URTH', '^GSPC' (S&P 500), '^IBEX', 'BTC-USD', 'EURUSD=X'.
        period: History window to compute the period change: '5d', '1mo', '3mo', '6mo', '1y', 'ytd'. Defaults to '5d'.
    """
    return _quote_line(ticker, ticker, period)


def _snapshot_line(name: str, ticker: str) -> str:
    """One line with the latest close, the change vs. the previous close and the change vs. one week earlier."""
    try:
        asset = yf.Ticker(ticker)
        history = asset.history(period="1mo")
        if history.empty:
            return f"- {name} ({ticker}): no data"
        closes = history["Close"]
        last_close = closes.iloc[-1]
        line = f"- {name} ({ticker}): {last_close:,.2f}{_currency(asset)}"
        if len(closes) >= 2:
            day_change = (last_close / closes.iloc[-2] - 1) * 100
            line += f" | day: {day_change:+.2f}%"
        # Last close at least 7 calendar days before the latest one: a true week for ETFs and for 24/7 Bitcoin alike
        week_ago = closes[closes.index <= closes.index[-1] - pd.Timedelta(days=7)]
        if not week_ago.empty:
            week_change = (last_close / week_ago.iloc[-1] - 1) * 100
            line += f" | week: {week_change:+.2f}%"
        return line + f" | close date: {closes.index[-1].date()}"
    except Exception as e:
        return f"- {name} ({ticker}): error fetching data ({e})"


@tool
def get_market_snapshot() -> str:
    """Gets the latest close, the daily change and the 1-week change of Cava Bot's reference assets: MSCI World (URTH), Vanguard Emerging Markets (VWO) and Bitcoin (BTC-USD). Use it for the daily market report.
    """
    lines = [_snapshot_line(name, ticker) for name, ticker in DEFAULT_ASSETS.items()]
    return "📊 REAL MARKET DATA:\n" + "\n".join(lines)
