import pytest
from conftest import FakeResponse

import daily_bulletin
import telegram_client


class FakeAgent:
    def __init__(self):
        self.tasks = []

    def run(self, task):
        self.tasks.append(task)
        return "☀️ Test bulletin"


@pytest.fixture
def fake_agent(monkeypatch):
    fake = FakeAgent()
    monkeypatch.setattr(daily_bulletin, "build_agent", lambda: fake)
    return fake


def test_dry_run_prints_without_sending(monkeypatch, capsys, fake_agent):
    monkeypatch.setenv("DRY_RUN", "1")
    monkeypatch.setattr(daily_bulletin, "send_telegram", lambda msg: pytest.fail("must not send in DRY_RUN mode"))

    daily_bulletin.main()

    assert "Test bulletin" in capsys.readouterr().out
    assert fake_agent.tasks == [daily_bulletin.DAILY_BULLETIN_TASK]


def test_sends_bulletin_to_telegram(monkeypatch, fake_agent):
    monkeypatch.setenv("DRY_RUN", "0")
    sent = []
    monkeypatch.setattr(daily_bulletin, "send_telegram", sent.append)

    daily_bulletin.main()

    assert sent == ["☀️ Test bulletin"]


def test_bulletin_task_keeps_spanish_sections():
    # The bulletin is published in Spanish: its section titles are part of the product
    for section in ("El tiempo en Málaga", "Resumen de las últimas 24h", "Las Maldades", "Previsión y Cierre"):
        assert section in daily_bulletin.DAILY_BULLETIN_TASK


def test_telegram_falls_back_to_plain_text_on_bad_markdown(monkeypatch):
    monkeypatch.setenv("TELEGRAM_TOKEN", "token")
    monkeypatch.setenv("CHAT_ID", "42")
    payloads = []

    def fake_post(url, data, timeout):
        payloads.append(dict(data))
        return FakeResponse(ok="parse_mode" not in data, status_code=400)

    monkeypatch.setattr(telegram_client.requests, "post", fake_post)

    telegram_client.send_telegram("*unclosed markdown")

    assert payloads[0]["parse_mode"] == "Markdown"
    assert "parse_mode" not in payloads[1]
    assert payloads[1]["chat_id"] == "42"
