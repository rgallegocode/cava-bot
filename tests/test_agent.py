import pytest
from smolagents import ChatMessage, CodeAgent, HfApiModel, LiteLLMModel

import agent

EXPECTED_TOOLS = {
    "get_market_snapshot",
    "get_asset_quote",
    "assess_market_trend",
    "get_financial_news",
    "get_weather",
    "get_current_time_in_timezone",
    "web_search",
    "visit_webpage",
    "final_answer",
}


@pytest.mark.parametrize(
    ("provider", "model_cls", "model_id"),
    [
        ("groq", agent.RateLimitedLiteLLMModel, "groq/qwen/qwen3.8-27b"),
        ("gemini", agent.RateLimitedLiteLLMModel, "gemini/gemini-3.8-flash"),
        ("hf", HfApiModel, "Qwen/Qwen2.5-Coder-32B-Instruct"),
    ],
)
def test_build_model_by_provider(monkeypatch, provider, model_cls, model_id):
    monkeypatch.setenv("MODEL_PROVIDER", provider)
    for var in ("GROQ_MODEL", "GEMINI_MODEL", "HF_MODEL_ID"):
        monkeypatch.delenv(var, raising=False)

    model = agent.build_model()

    assert isinstance(model, model_cls)
    assert model.model_id == model_id


def test_build_agent_registers_all_tools(monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "groq")

    cava = agent.build_agent()

    assert isinstance(cava, CodeAgent)
    assert set(cava.tools) == EXPECTED_TOOLS
    assert "Cava Bot" in cava.prompt_templates["system_prompt"]


def test_agent_answers_when_max_steps_is_reached(monkeypatch):
    # Daily bulletin #87 crashed with KeyError: 'final_answer' when the agent ran out of steps
    monkeypatch.setenv("MODEL_PROVIDER", "groq")
    cava = agent.build_agent()
    cava.model = lambda messages, **kwargs: ChatMessage(role="assistant", content="Boletín de emergencia")

    assert cava.provide_final_answer("Escribe el boletín", images=None) == "Boletín de emergencia"


def test_timezone_tool():
    assert "Europe/Madrid" in agent.get_current_time_in_timezone(timezone="Europe/Madrid")
    assert "Error" in agent.get_current_time_in_timezone(timezone="Mars/Olympus")


class TestRateLimitedModel:
    @pytest.fixture
    def model(self, monkeypatch):
        sleeps = []
        monkeypatch.setattr(agent.time, "sleep", sleeps.append)
        model = agent.RateLimitedLiteLLMModel(model_id="groq/test", api_key="x", min_interval=0, tokens_per_minute=8000)
        model.sleeps = sleeps
        return model

    def _fake_llm(self, monkeypatch, outcomes):
        """Makes the LLM call return/raise the items of outcomes, in order."""
        outcomes = list(outcomes)

        def fake_call(self, *args, **kwargs):
            outcome = outcomes.pop(0)
            if isinstance(outcome, Exception):
                raise outcome
            self.last_input_token_count, self.last_output_token_count = 5000, 1000
            return outcome

        monkeypatch.setattr(LiteLLMModel, "__call__", fake_call)

    def test_gap_scales_with_tokens_per_minute(self, model):
        model._last_tokens = 6000

        assert model._required_gap() == pytest.approx(45.0)  # 6000 / 8000 tokens/min

    def test_gap_scales_with_output_tokens_per_minute(self, model):
        model.output_tokens_per_minute = 1000
        model._last_tokens, model._last_output_tokens = 2000, 900

        assert model._required_gap() == pytest.approx(54.0)  # 900 / 1000 output tokens/min

    def test_retries_on_rate_limit_then_succeeds(self, model, monkeypatch):
        self._fake_llm(monkeypatch, [Exception("RateLimitError 429 tokens per minute"), "ok"])

        assert model([]) == "ok"
        assert 30 in model.sleeps  # first retry backoff
        assert model._last_tokens == 6000

    @pytest.mark.parametrize(
        "error",
        [
            "429 GenerateRequestsPerDayPerProjectPerModel-FreeTier",  # daily quota
            "413 Request too large for model",  # oversized request
            "400 invalid_request_error",  # non-recoverable error
        ],
    )
    def test_fails_fast_on_non_recoverable_errors(self, model, monkeypatch, error):
        self._fake_llm(monkeypatch, [Exception(error), "never reached"])

        with pytest.raises(Exception, match=error.split()[0]):
            model([])
        assert 30 not in model.sleeps

    def test_gives_up_after_max_retries(self, model, monkeypatch):
        model.max_retries = 2
        self._fake_llm(monkeypatch, [Exception("503 UNAVAILABLE")] * 3)

        with pytest.raises(Exception, match="503"):
            model([])
