import sys
from pathlib import Path

import pandas as pd
import pytest

# Make agent, tools, etc. importable from the repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class FakeTicker:
    """Stands in for yfinance.Ticker, returning a fixed close-price history."""

    def __init__(self, closes):
        self.closes = closes

    def history(self, period="5d"):
        index = pd.date_range(end="2026-10-20", periods=len(self.closes), freq="B")
        return pd.DataFrame({"Close": self.closes}, index=index)


@pytest.fixture
def fake_ticker(monkeypatch):
    """Usage: fake_ticker(module, closes) patches module.yf.Ticker to return those closes."""

    def _apply(module, closes):
        monkeypatch.setattr(module.yf, "Ticker", lambda ticker: FakeTicker(closes))

    return _apply


class FakeResponse:
    def __init__(self, payload=None, ok=True, status_code=200):
        self._payload = payload or {}
        self.ok = ok
        self.status_code = status_code

    def json(self):
        return self._payload

    def raise_for_status(self):
        if not self.ok:
            raise RuntimeError(f"HTTP {self.status_code}")
