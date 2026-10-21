import datetime
import os
import time
from pathlib import Path

import pytz
import yaml
from dotenv import load_dotenv
from smolagents import CodeAgent, HfApiModel, LiteLLMModel, tool

from tools.final_answer import FinalAnswerTool
from tools.market_data import get_asset_quote, get_market_snapshot
from tools.market_trend import assess_market_trend
from tools.news import get_financial_news
from tools.visit_webpage import VisitWebpageTool
from tools.weather import get_weather
from tools.web_search import DuckDuckGoSearchTool

PROMPTS_PATH = Path(__file__).parent / "prompts.yaml"

# En local las claves se leen de .env; en GitHub Actions y en el Space llegan como secretos
load_dotenv(Path(__file__).parent / ".env")


@tool
def get_current_time_in_timezone(timezone: str) -> str:
    """A tool that fetches the current local time in a specified timezone.
    Args:
        timezone: A string representing a valid timezone (e.g., 'Europe/Madrid', 'America/New_York').
    """
    try:
        tz = pytz.timezone(timezone)
        local_time = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        return f"The current local time in {timezone} is: {local_time}"
    except Exception as e:
        return f"Error fetching time for timezone '{timezone}': {str(e)}"


class RateLimitedLiteLLMModel(LiteLLMModel):
    """LiteLLMModel adaptado a los planes gratuitos (Groq: 30 peticiones y 8K tokens/minuto; Gemini: 5 peticiones/minuto).

    Cada paso del agente es una llamada al LLM, así que se espacian las llamadas según las peticiones y los tokens
    consumidos y, ante un 429 (cuota) o 503 (saturación), se reintenta solo esa llamada en lugar de relanzar el agente.
    """

    def __init__(self, *args, min_interval: float = 2.0, tokens_per_minute: int | None = None, max_retries: int = 4, **kwargs):
        super().__init__(*args, **kwargs)
        self.min_interval = min_interval
        self.tokens_per_minute = tokens_per_minute
        self.max_retries = max_retries
        self._last_call = 0.0
        self._last_tokens = 0

    def _required_gap(self) -> float:
        gap = self.min_interval
        if self.tokens_per_minute:
            # Los tokens de la llamada anterior tienen que "caber" en la ventana de un minuto
            gap = max(gap, self._last_tokens / self.tokens_per_minute * 60)
        return gap

    def __call__(self, *args, **kwargs):
        for attempt in range(self.max_retries + 1):
            wait = self._required_gap() - (time.monotonic() - self._last_call)
            if wait > 0:
                time.sleep(wait)
            self._last_call = time.monotonic()
            try:
                response = super().__call__(*args, **kwargs)
                self._last_tokens = (self.last_input_token_count or 0) + (self.last_output_token_count or 0)
                return response
            except Exception as e:
                retryable = any(code in str(e) for code in ("429", "503", "RateLimit", "UNAVAILABLE", "Timeout"))
                # Ni una cuota diaria agotada ni una petición demasiado grande se arreglan esperando
                daily_quota = "PerDay" in str(e) or "per day" in str(e)
                too_large = "Request too large" in str(e) or "413" in str(e)
                if not retryable or daily_quota or too_large or attempt == self.max_retries:
                    raise
                backoff = 30 * (attempt + 1)
                print(f"LLM no disponible ({type(e).__name__}: {str(e)[:200]}), reintento {attempt + 1}/{self.max_retries} en {backoff}s")
                time.sleep(backoff)


def build_model():
    """MODEL_PROVIDER=groq (por defecto), gemini o hf (Qwen2.5 vía HF Inference, el modelo del curso; requiere HF_TOKEN)."""
    provider = os.environ.get("MODEL_PROVIDER", "groq").lower()
    if provider == "groq":
        return RateLimitedLiteLLMModel(
            tokens_per_minute=int(os.environ.get("GROQ_TPM", "8000")),
            model_id=os.environ.get("GROQ_MODEL", "groq/qwen/qwen3.8-27b"),
            api_key=os.environ.get("GROQ_API_KEY"),
            temperature=0.5,
            timeout=120,  # segundos por llamada: evita que el agente se quede colgado
        )
    if provider == "gemini":
        return RateLimitedLiteLLMModel(
            min_interval=float(os.environ.get("GEMINI_MIN_INTERVAL", "13")),
            model_id=os.environ.get("GEMINI_MODEL", "gemini/gemini-3.8-flash"),
            api_key=os.environ.get("GEMINI_API_KEY"),
            temperature=0.5,
            timeout=120,
        )
    # Si el modelo está saturado, se puede usar el endpoint del curso que también sirve qwen2.5 coder:
    # HF_MODEL_ID='https://pflgm2locj2t89co.us-east-1.aws.endpoints.huggingface.cloud'
    return HfApiModel(
        max_tokens=2096,
        temperature=0.5,
        model_id=os.environ.get("HF_MODEL_ID", "Qwen/Qwen2.5-Coder-32B-Instruct"),
        custom_role_conversions=None,
    )


def build_agent() -> CodeAgent:
    with open(PROMPTS_PATH, "r", encoding="utf-8") as stream:
        prompt_templates = yaml.safe_load(stream)

    return CodeAgent(
        model=build_model(),
        tools=[
            get_market_snapshot,
            get_asset_quote,
            assess_market_trend,
            get_financial_news,
            get_weather,
            get_current_time_in_timezone,
            DuckDuckGoSearchTool(max_results=5),
            VisitWebpageTool(),
            FinalAnswerTool(),  # no quitar final answer
        ],
        max_steps=8,
        verbosity_level=1,
        grammar=None,
        planning_interval=None,
        name="cava_agent",
        description="Analista financiero con el estilo de José Luis Cava.",
        additional_authorized_imports=["datetime", "math", "statistics"],
        prompt_templates=prompt_templates,
    )
