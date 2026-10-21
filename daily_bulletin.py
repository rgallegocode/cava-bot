"""Cava Bot daily bulletin: the agent researches the market with its tools, writes the report and sends it to Telegram.

Usage: python daily_bulletin.py   (DRY_RUN=1 prints it instead of sending it)
"""
import os

from agent import build_agent
from telegram_client import send_telegram

# The bulletin is published in Spanish for a Spanish-speaking Telegram audience: the section titles below are part
# of the product, so they stay in Spanish while the instructions to the agent are in English.
DAILY_BULLETIN_TASK = """
Write today's market report for your Telegram followers. The report MUST be written in Spanish.
Before writing, gather real data with your tools: the weather in Málaga, the market snapshot,
the Bull/Bear trend of the MSCI World (URTH) and the economy, stock market and geopolitics news of the last 24h.
Be efficient: gather all that data in a single code block (one call per tool, news only once, in Spanish)
and, in the next step, write the message and return it with final_answer.

MANDATORY MESSAGE STRUCTURE (Telegram text, simple Markdown: *bold*, no tables):

1. ☀️ El tiempo en Málaga: one short sentence with the real temperature and sky conditions.

2. 📰 Resumen de las últimas 24h: the 5 most important stock market and economy news. Use bullets and emojis.
   Be extremely concise and to the point. Mention Bitcoin if the data justifies it.

3. 😈 Las Maldades del Mercado: a short paragraph on the worst of the day, using your signature term ("maldades").
   If the day was outstandingly good, say clearly "hoy nos hemos librado de sus maldades".

4. 🔮 Previsión y Cierre de Mercado:
   - Start by stating whether we are in a 🐂 Bull Market or 🐻 Bear Market according to assess_market_trend,
     with a one-line justification.
   - You MUST show the close of the 3 snapshot assets: 📈 at the end if the change is positive, 📉 if negative.
   - Exact format:
     • MSCI World: [Price] ([Change]%) [Emoji]
     • Vanguard Emerging Markets: [Price] ([Change]%) [Emoji]
     • Bitcoin: $[Price] USD ([Change]%) [Emoji]

Return the whole message as a single string with final_answer.
"""


def main():
    print("\n--- Starting Cava Agent ---")
    # Retries on 429/503 are handled by the model wrapper (agent.RateLimitedLiteLLMModel)
    bulletin = str(build_agent().run(DAILY_BULLETIN_TASK))
    if os.environ.get("DRY_RUN") == "1":
        print(bulletin)
    else:
        send_telegram(bulletin)
    print("--- Done ---\n")


if __name__ == "__main__":
    main()
