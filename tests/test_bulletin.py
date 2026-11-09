from datetime import date

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
    assert fake_agent.tasks[0] in (daily_bulletin.WEEKDAY_BULLETIN_TASK, daily_bulletin.WEEKEND_BULLETIN_TASK)


def test_sends_bulletin_to_telegram(monkeypatch, fake_agent):
    monkeypatch.setenv("DRY_RUN", "0")
    sent = []
    monkeypatch.setattr(daily_bulletin, "send_telegram", sent.append)

    daily_bulletin.main()

    assert sent == ["☀️ Test bulletin"]


def test_does_not_send_llm_errors_as_bulletin(monkeypatch, fake_agent):
    monkeypatch.setenv("DRY_RUN", "0")
    monkeypatch.setattr(fake_agent, "run", lambda task: "Error in generating final LLM output:\n429 Too Many Requests")
    monkeypatch.setattr(daily_bulletin, "send_telegram", lambda msg: pytest.fail("must not send an LLM error"))

    with pytest.raises(RuntimeError, match="429"):
        daily_bulletin.main()


def test_weekdays_get_the_market_report_and_weekends_the_monday_preview():
    # 2026-11-09 is a Monday
    for day in range(9, 14):
        assert daily_bulletin.bulletin_task(date(2026, 11, day)) is daily_bulletin.WEEKDAY_BULLETIN_TASK
    for day in (14, 15):
        assert daily_bulletin.bulletin_task(date(2026, 11, day)) is daily_bulletin.WEEKEND_BULLETIN_TASK


def test_bulletin_tasks_keep_spanish_sections():
    # The bulletin is published in Spanish: its section titles are part of the product
    for section in (
        "El tiempo en Málaga",
        "La clave del día",
        "Cartera Cava",
        "Resumen de las últimas 24h",
        "Las Maldades",
        "Tendencia y qué vigilar",
    ):
        assert section in daily_bulletin.WEEKDAY_BULLETIN_TASK
    for section in (
        "El tiempo en Málaga",
        "Lo que puede mover la bolsa el lunes",
        "Balance de la semana",
        "Las Maldades",
    ):
        assert section in daily_bulletin.WEEKEND_BULLETIN_TASK


def test_bulletin_tasks_only_quote_the_three_reference_assets():
    for task in (daily_bulletin.WEEKDAY_BULLETIN_TASK, daily_bulletin.WEEKEND_BULLETIN_TASK):
        assert "get_market_snapshot()" in task
        assert "get_asset_quote" not in task


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
