import yfinance as yf
from smolagents import tool

# ETFs representativos de los índices que sigue Cava Bot
DEFAULT_ASSETS = {
    "MSCI World (iShares URTH)": "URTH",
    "Vanguard Emerging Markets": "VWO",
    "Bitcoin": "BTC-USD",
}


def _quote_line(name: str, ticker: str, period: str = "5d") -> str:
    """Devuelve una línea con el último cierre y la variación respecto al cierre anterior."""
    try:
        history = yf.Ticker(ticker).history(period=period)
        if history.empty:
            return f"- {name} ({ticker}): sin datos. ¿Ticker válido?"
        last_close = history["Close"].iloc[-1]
        if len(history) >= 2:
            prev_close = history["Close"].iloc[-2]
            change = ((last_close - prev_close) / prev_close) * 100
            line = f"- {name} ({ticker}): {last_close:,.2f} ({change:+.2f}% vs. cierre anterior)"
        else:
            # Solo 1 sesión disponible (fin de semana/festivo)
            line = f"- {name} ({ticker}): {last_close:,.2f} (Mercado cerrado/Sin variación)"
        if len(history) >= 3:
            first_close = history["Close"].iloc[0]
            period_change = ((last_close - first_close) / first_close) * 100
            line += f" | {period_change:+.2f}% en el periodo {period}"
        return line + f" | fecha: {history.index[-1].date()}"
    except Exception as e:
        return f"- {name} ({ticker}): error al obtener datos ({e})"


@tool
def get_asset_quote(ticker: str, period: str = "5d") -> str:
    """Gets the latest closing price of a stock, ETF, index or crypto from Yahoo Finance, its change vs. the previous close and its change over the requested period.
    Args:
        ticker: Yahoo Finance ticker symbol, e.g. 'AAPL', 'URTH', '^GSPC' (S&P 500), '^IBEX', 'BTC-USD', 'EURUSD=X'.
        period: History window to compute the period change: '5d', '1mo', '3mo', '6mo', '1y', 'ytd'. Defaults to '5d'.
    """
    return _quote_line(ticker, ticker, period)


@tool
def get_market_snapshot() -> str:
    """Gets today's closing price and daily change for Cava Bot's reference assets: MSCI World (URTH), Vanguard Emerging Markets (VWO) and Bitcoin (BTC-USD). Use it for the daily market report.
    """
    lines = [_quote_line(name, ticker) for name, ticker in DEFAULT_ASSETS.items()]
    return "📊 DATOS REALES DEL MERCADO:\n" + "\n".join(lines)
