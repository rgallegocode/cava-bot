import yfinance as yf
from smolagents import tool


@tool
def assess_market_trend(ticker: str = "URTH") -> str:
    """Classifies an asset as Bull or Bear market using technical data: last close vs. its 50-day and 200-day simple moving averages, golden/death cross and distance from the 52-week high.
    Args:
        ticker: Yahoo Finance ticker symbol to analyse, e.g. 'URTH' (MSCI World), '^GSPC' (S&P 500), 'BTC-USD'. Defaults to 'URTH'.
    """
    try:
        close = yf.Ticker(ticker).history(period="1y")["Close"]
    except Exception as e:
        return f"Error fetching price history for {ticker}: {e}"
    if len(close) < 200:
        return f"Not enough history for {ticker} ({len(close)} sessions) to compute the SMA200."

    last = close.iloc[-1]
    sma50 = close.rolling(50).mean().iloc[-1]
    sma200 = close.rolling(200).mean().iloc[-1]
    high_52w = close.max()
    drawdown = (last - high_52w) / high_52w * 100

    # Bull: price and SMA50 above the SMA200, and not down 20% or more from the 52-week high
    if last > sma200 and sma50 > sma200 and drawdown > -20:
        regime = "🐂 BULL MARKET"
    elif last < sma200 and sma50 < sma200:
        regime = "🐻 BEAR MARKET"
    else:
        regime = "⚖️ MIXED / SIDEWAYS TREND"

    cross = "golden cross (SMA50 > SMA200)" if sma50 > sma200 else "death cross (SMA50 < SMA200)"
    return (
        f"{ticker}: {regime}. Close {last:,.2f} | SMA50 {sma50:,.2f} | SMA200 {sma200:,.2f} | {cross} | "
        f"{drawdown:+.2f}% from the 52-week high ({high_52w:,.2f})."
    )
