"""Cava Bot daily bulletin: the agent researches the market with its tools, writes the report and sends it to Telegram.

Usage: python daily_bulletin.py   (DRY_RUN=1 prints it instead of sending it)
"""
import os

from agent import build_agent
from telegram_client import send_telegram

# The bulletin is published in Spanish for a Spanish-speaking Telegram audience: the section titles below are part
# of the product, so they stay in Spanish while the instructions to the agent are in English.
DAILY_BULLETIN_TASK = """
Write today's market report for your Telegram followers: retail investors who read it in 2 minutes before the open
and want to know what moved, why, and what to watch. The report MUST be written in Spanish.

STEP 1 - Gather all the data in ONE single code block, printing every result:
- get_weather("Málaga")
- get_market_snapshot()
- for each ticker in ["^GSPC", "^IXIC", "^STOXX50E", "^IBEX", "^VIX", "^TNX", "EURUSD=X", "GC=F", "BZ=F"]:
  print(get_asset_quote(ticker))
- assess_market_trend("URTH")
- get_financial_news(query="economía OR bolsa OR mercados OR inflación OR BCE OR Fed OR aranceles OR petróleo", language="es")
Do NOT use web_search or visit_webpage unless get_financial_news returns an error: they waste steps on paywalled pages.

STEP 2 - Write the message and return it with final_answer. Do not gather more data.

RULES:
- Every number must come from the tool results. If a quote failed, omit that line; never estimate it.
- ^TNX is the US 10-year Treasury yield in % (show it as "4,25%", not as a price). ^VIX is in points.
- Only report news that appears in the tool results and actually moves markets; skip anything else.
- Explain the "why": connect each move to its cause when the news supports it. No generic filler
  ("los mercados estarán atentos", "volatilidad"), no investment disclaimer at the end.
- Telegram simple Markdown: *bold* only, no tables, no headings with #. Keep the whole message under 2,500 characters.

MANDATORY MESSAGE STRUCTURE:

☀️ El tiempo en Málaga: one line with the real temperature and sky.

🎯 *La clave del día*: 1-2 sentences with THE main driver of the markets in the last 24h and why it matters to an investor.

📊 *Cuadro de mercado* (one line per asset: "• Name: price (day %) | 5d %", 📈 if the day change is positive, 📉 if negative):
   - Bolsas: S&P 500, Nasdaq, Euro Stoxx 50, IBEX 35
   - Riesgo: VIX (add "miedo" if above 20), bono EE.UU. 10 años
   - Divisas y materias primas: EUR/USD, oro, Brent
   - Cartera Cava: MSCI World, Vanguard Emerging Markets, Bitcoin

📰 *Resumen de las últimas 24h*: the 3-5 news items that move markets. Each bullet: the fact in one line, then
   "→" with the affected asset/sector and the direction of the impact.

😈 *Las Maldades del Mercado*: a short paragraph on the worst of the day using your signature term ("maldades").
   If the day was outstandingly good, say clearly "hoy nos hemos librado de sus maldades".

🔮 *Previsión y Cierre de Mercado*:
   - 🐂 Bull Market or 🐻 Bear Market (or mixed trend) according to assess_market_trend, justified with its data:
     price vs. SMA50/SMA200 and distance from the 52-week high. Mention the SMA50 and SMA200 as the levels to watch.
   - 👀 Qué vigilar: 1-2 upcoming catalysts (central bank meetings, CPI/jobs data, earnings) ONLY if they appear in the news.

Return the whole message as a single string with final_answer.
"""


def main():
    print("\n--- Starting Cava Agent ---")
    # Retries on 429/503 are handled by the model wrapper (agent.RateLimitedLiteLLMModel)
    bulletin = str(build_agent().run(DAILY_BULLETIN_TASK))
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
