import datetime
import os
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


def build_model():
    """MODEL_PROVIDER=gemini (por defecto) o hf (Qwen2.5 vía HF Inference, el modelo del curso; requiere HF_TOKEN)."""
    provider = os.environ.get("MODEL_PROVIDER", "gemini").lower()
    if provider == "gemini":
        return LiteLLMModel(
            model_id=os.environ.get("GEMINI_MODEL", "gemini/gemini-2.5-flash"),
            api_key=os.environ.get("GEMINI_API_KEY"),
            temperature=0.5,
            num_retries=3,  # reintentos de LiteLLM ante errores 503/429 puntuales
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
            DuckDuckGoSearchTool(),
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
