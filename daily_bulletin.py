"""Cava Bot daily bulletin: the agent researches the market with its tools, writes the report and sends it to Telegram.

Usage: python daily_bulletin.py   (DRY_RUN=1 prints it instead of sending it)
"""
import os
from datetime import date, datetime
from zoneinfo import ZoneInfo

from agent import build_agent
from telegram_client import send_telegram

# The bulletin is published in Spanish for a Spanish-speaking Telegram audience: the section titles below are part
# of the product, so they stay in Spanish while the instructions to the agent are in English.

# Shared by both tasks: how to gather the data and how to write it
_COMMON_RULES = """
Do NOT use web_search or visit_webpage unless get_financial_news returns an error: they waste steps on paywalled pages.

STEP 2 - Write the message and return it with final_answer. Do not gather more data, even if the news is weak:
work with what you have. Keep your Thought to one short line: your whole output (Thought + code + message) is hard-capped
at 1,000 tokens, and a message cut off by that cap breaks the run, so stay well under the length limit below.

RULES:
- Every number must come from the tool results. If a quote failed, omit that line; never estimate it.
- Every line must be useful to an investor in MSCI World, emerging markets and Bitcoin. Only report news that appears
  in the tool results and can move those assets; skip anything else. If no headline explains a big move, say so in one
  line instead of guessing the cause. Better a shorter message than filler.
- No generic filler ("los mercados estarán atentos", "volatilidad", "habrá que ver"), no investment disclaimer.
- Do not add any asset, index, currency or commodity other than the three in the snapshot.
- Telegram simple Markdown: *bold* only, no tables, no headings with #. Keep the whole message under 1,200 characters.
"""

# Monday to Friday: the markets are open, so the report covers what moved and why
WEEKDAY_BULLETIN_TASK = """
Write today's market report for your Telegram followers: retail investors who read it in 2 minutes before the open
and want to know what moved their assets, why, and what to watch. The report MUST be written in Spanish.

STEP 1 - Gather all the data in ONE single code block, printing every result:
- get_weather("Málaga")
- get_market_snapshot()
- assess_market_trend("URTH")
- get_financial_news(query='bolsa OR "Wall Street" OR BCE OR "Reserva Federal" OR inflación OR bitcoin', language="es")
- get_financial_news(query='stocks OR "Federal Reserve" OR ECB OR "emerging markets" OR bitcoin', language="en")
""" + _COMMON_RULES + """
MANDATORY MESSAGE STRUCTURE:

☀️ El tiempo en Málaga: one short line with the real temperature and sky.

🎯 *La clave del día*: 1-2 sentences with THE main driver of the markets in the last 24h and how it hits the 3 assets.

📊 *Cartera Cava* (exactly 3 lines, "• Name: price | día: X% | semana: Y%", 📈 if the day change is positive,
   📉 if negative): MSCI World, Vanguard Emerging Markets, Bitcoin. Use the "day" and "week" values of get_market_snapshot.

📰 *Resumen de las últimas 24h*: up to 3 news items that move these assets. Each bullet: the fact in one short line,
   then "→" with the affected asset (MSCI World / emergentes / Bitcoin) and the direction of the impact.

😈 *Las Maldades del Mercado*: 1-2 sentences on the worst of the day using your signature term ("maldades").
   If the day was outstandingly good, say clearly "hoy nos hemos librado de sus maldades".

🔮 *Tendencia y qué vigilar*:
   - 🐂 Bull Market or 🐻 Bear Market (or mixed trend) of the MSCI World according to assess_market_trend, in one line
     with its key data: price vs. SMA50/SMA200 and distance from the 52-week high.
   - 👀 Qué vigilar: 1-2 upcoming catalysts (central bank meetings, CPI/jobs data, earnings) ONLY if they appear in the news.

Return the whole message as a single string with final_answer.
"""

# Saturday and Sunday: stock markets are closed, so the report looks ahead to Monday's open
WEEKEND_BULLETIN_TASK = """
Today is the weekend and stock markets are closed. Write a short report for your Telegram followers: retail investors
who want to know which of this weekend's news can move their assets when the markets open on Monday.
The report MUST be written in Spanish.

STEP 1 - Gather all the data in ONE single code block, printing every result:
- get_weather("Málaga")
- get_market_snapshot()
- get_financial_news(query='Fed OR BCE OR aranceles OR China OR geopolítica OR petróleo OR resultados OR bitcoin', language="es")
- get_financial_news(query='"Federal Reserve" OR ECB OR tariffs OR China OR geopolitics OR "oil prices" OR earnings OR bitcoin', language="en")
""" + _COMMON_RULES + """
- The ETFs (MSCI World, Vanguard Emerging Markets) show Friday's close: present them as the weekly balance, not as
  today's move. Bitcoin trades 24/7, so its day change is real.

MANDATORY MESSAGE STRUCTURE:

☀️ El tiempo en Málaga: one short line with the real temperature and sky.

🗓️ *Lo que puede mover la bolsa el lunes*: up to 3 news items from the weekend that can move Monday's open. Each bullet:
   the fact in one short line, then "→" with the affected asset (MSCI World / emergentes / Bitcoin) and the likely
   direction. If nothing relevant happened, say so in one line: a calm weekend is useful information too.

📊 *Balance de la semana* (exactly 3 lines): "• MSCI World: price | semana: Y%", "• Vanguard Emerging Markets:
   price | semana: Y%" (Friday's close), and "• Bitcoin: price | día: X% | semana: Y%". 📈 if the week change is
   positive, 📉 if negative.

😈 *Las Maldades del Mercado*: 1 sentence on the main risk for Monday using your signature term ("maldades").
   If there is no clear threat, say "este fin de semana nos hemos librado de sus maldades".

👀 *Qué vigilar esta semana*: 1-2 catalysts of the coming week (central bank meetings, CPI/jobs data, earnings)
   ONLY if they appear in the news; otherwise omit this section.

Return the whole message as a single string with final_answer.
"""


def bulletin_task(today: date) -> str:
    """Weekday market report from Monday to Friday, a look-ahead to Monday's open on Saturday and Sunday."""
    return WEEKEND_BULLETIN_TASK if today.weekday() >= 5 else WEEKDAY_BULLETIN_TASK


def main():
    print("\n--- Starting Cava Agent ---")
    # Retries on 429/503 are handled by the model wrapper (agent.RateLimitedLiteLLMModel)
    # The bulletin is read in Spain, so its day of the week decides the kind of report
    task = bulletin_task(datetime.now(ZoneInfo("Europe/Madrid")).date())
    bulletin = str(build_agent().run(task))
    # When the agent runs out of steps and the fallback LLM call also fails, smolagents returns the error as the answer
    if bulletin.startswith("Error in generating final LLM output"):
        raise RuntimeError(bulletin)
    if os.environ.get("DRY_RUN") == "1":
        print(bulletin)
    else:
        send_telegram(bulletin)
    print("--- Done ---\n")


if __name__ == "__main__":
    main()
