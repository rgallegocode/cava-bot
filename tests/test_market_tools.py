from tools import market_data, market_trend


def test_asset_quote_reports_close_and_daily_change(fake_ticker):
    fake_ticker(market_data, [100.0, 102.0, 101.0, 104.0, 105.0])

    result = market_data.get_asset_quote(ticker="URTH", period="5d")

    assert "105.00" in result
    assert "+0.96% vs. cierre anterior" in result  # 105 vs 104
    assert "+5.00% en el periodo 5d" in result  # 105 vs 100
    assert "fecha: 2026-10-20" in result


def test_asset_quote_handles_unknown_ticker(fake_ticker):
    fake_ticker(market_data, [])

    assert "sin datos" in market_data.get_asset_quote(ticker="NOEXISTE")


def test_asset_quote_single_session_has_no_change(fake_ticker):
    fake_ticker(market_data, [50.0])

    assert "Mercado cerrado/Sin variación" in market_data.get_asset_quote(ticker="BTC-USD")


def test_market_snapshot_includes_reference_assets(fake_ticker):
    fake_ticker(market_data, [10.0, 9.0])

    result = market_data.get_market_snapshot()

    for ticker in ("URTH", "VWO", "BTC-USD"):
        assert ticker in result
    assert "-10.00%" in result


def test_trend_detects_bull_market(fake_ticker):
    fake_ticker(market_trend, [100 + i * 0.5 for i in range(250)])  # subida sostenida

    result = market_trend.assess_market_trend(ticker="URTH")

    assert "BULL MARKET" in result
    assert "golden cross" in result


def test_trend_detects_bear_market(fake_ticker):
    fake_ticker(market_trend, [300 - i * 0.5 for i in range(250)])  # caída sostenida

    result = market_trend.assess_market_trend(ticker="URTH")

    assert "BEAR MARKET" in result
    assert "death cross" in result


def test_trend_mixed_when_deep_drawdown_above_sma200(fake_ticker):
    # Sube mucho y luego cae >20 % pero sigue por encima de la SMA200: no se considera bull
    closes = [100 + i for i in range(220)] + [319 - i * 4 for i in range(30)]
    fake_ticker(market_trend, closes)

    assert "MIXTA" in market_trend.assess_market_trend(ticker="X")


def test_trend_requires_200_sessions(fake_ticker):
    fake_ticker(market_trend, [100.0] * 50)

    assert "No hay suficiente histórico" in market_trend.assess_market_trend(ticker="X")
