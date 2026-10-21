from tools import market_data, market_trend


def test_asset_quote_reports_close_and_daily_change(fake_ticker):
    fake_ticker(market_data, [100.0, 102.0, 101.0, 104.0, 105.0])

    result = market_data.get_asset_quote(ticker="URTH", period="5d")

    assert "105.00" in result
    assert "+0.96% vs. previous close" in result  # 105 vs 104
    assert "+5.00% over 5d" in result  # 105 vs 100
    assert "date: 2026-10-20" in result


def test_asset_quote_handles_unknown_ticker(fake_ticker):
    fake_ticker(market_data, [])

    assert "no data" in market_data.get_asset_quote(ticker="NOTATICKER")


def test_asset_quote_single_session_has_no_change(fake_ticker):
    fake_ticker(market_data, [50.0])

    assert "market closed / no change" in market_data.get_asset_quote(ticker="BTC-USD")


def test_market_snapshot_includes_reference_assets(fake_ticker):
    fake_ticker(market_data, [10.0, 9.0])

    result = market_data.get_market_snapshot()

    for ticker in ("URTH", "VWO", "BTC-USD"):
        assert ticker in result
    assert "-10.00%" in result


def test_trend_detects_bull_market(fake_ticker):
    fake_ticker(market_trend, [100 + i * 0.5 for i in range(250)])  # steady rise

    result = market_trend.assess_market_trend(ticker="URTH")

    assert "BULL MARKET" in result
    assert "golden cross" in result


def test_trend_detects_bear_market(fake_ticker):
    fake_ticker(market_trend, [300 - i * 0.5 for i in range(250)])  # steady decline

    result = market_trend.assess_market_trend(ticker="URTH")

    assert "BEAR MARKET" in result
    assert "death cross" in result


def test_trend_mixed_when_deep_drawdown_above_sma200(fake_ticker):
    # Strong rally followed by a >20% drop that stays above the SMA200: not considered bull
    closes = [100 + i for i in range(220)] + [319 - i * 4 for i in range(30)]
    fake_ticker(market_trend, closes)

    assert "MIXED" in market_trend.assess_market_trend(ticker="X")


def test_trend_requires_200_sessions(fake_ticker):
    fake_ticker(market_trend, [100.0] * 50)

    assert "Not enough history" in market_trend.assess_market_trend(ticker="X")


def test_asset_quote_includes_quote_currency(monkeypatch):
    from conftest import FakeTicker

    class TickerWithCurrency(FakeTicker):
        fast_info = {"currency": "USD"}

    monkeypatch.setattr(market_data.yf, "Ticker", lambda ticker: TickerWithCurrency([80000.0, 81000.0]))

    assert "81,000.00 USD" in market_data.get_asset_quote(ticker="BTC-USD")
