"""Boletín diario de Cava Bot: el agente investiga con sus herramientas y redacta el reporte; después se envía a Telegram.

Uso: python daily_bulletin.py   (DRY_RUN=1 para imprimirlo sin enviarlo)
"""
import os
import time

from agent import build_agent
from telegram_client import send_telegram

TAREA_BOLETIN = """
Redacta el reporte diario del mercado para tus seguidores de Telegram.
Antes de escribir, recoge datos reales con tus herramientas: el tiempo en Málaga, el snapshot de mercado,
la tendencia (Bull/Bear) del MSCI World (URTH) y las noticias de economía, bolsa y geopolítica de las últimas 24h.

ESTRUCTURA OBLIGATORIA DEL MENSAJE (texto para Telegram, Markdown sencillo: *negrita*, sin tablas):

1. ☀️ El tiempo en Málaga: una sola frase breve con la temperatura y el estado del cielo reales.

2. 📰 Resumen de las últimas 24h: las 5 noticias más importantes de la bolsa y la economía. Usa viñetas y emojis.
   Sé extremadamente conciso y directo al grano. Incluye una mención a Bitcoin si los datos lo justifican.

3. 😈 Las Maldades del Mercado: un párrafo corto analizando lo peor de la jornada usando tu término estrella ("maldades").
   Si el día ha sido espectacularmente bueno, di claramente que "hoy nos hemos librado de sus maldades".

4. 🔮 Previsión y Cierre de Mercado:
   - Comienza indicando si estamos en 🐂 Bull Market o 🐻 Bear Market según assess_market_trend, con una justificación de una línea.
   - Muestra OBLIGATORIAMENTE el cierre de los 3 activos del snapshot: 📈 al final si la variación es positiva, 📉 si es negativa.
   - Formato exacto:
     • MSCI World: [Precio] ([Variación]%) [Emoji]
     • Vanguard Emerging Markets: [Precio] ([Variación]%) [Emoji]
     • Bitcoin: $[Precio] USD ([Variación]%) [Emoji]

Devuelve el mensaje completo como un único string con final_answer.
"""


FALLBACK_GEMINI_MODEL = "gemini/gemini-flash-latest"
MAX_ATTEMPTS = 3


def generate_bulletin() -> str:
    """Ejecuta el agente con reintentos: los picos de demanda de Gemini (503) suelen ser temporales.
    El último intento usa el alias gemini-flash-latest como respaldo."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        if attempt == MAX_ATTEMPTS and os.environ.get("MODEL_PROVIDER", "gemini") == "gemini":
            os.environ["GEMINI_MODEL"] = FALLBACK_GEMINI_MODEL
        try:
            return str(build_agent().run(TAREA_BOLETIN))
        except Exception as e:
            print(f"Intento {attempt}/{MAX_ATTEMPTS} fallido: {e}")
            if attempt == MAX_ATTEMPTS:
                raise
            time.sleep(60 * attempt)


def main():
    print("\n--- Iniciando Cava Agent ---")
    bulletin = generate_bulletin()
    if os.environ.get("DRY_RUN") == "1":
        print(bulletin)
    else:
        send_telegram(bulletin)
    print("--- Proceso finalizado ---\n")


if __name__ == "__main__":
    main()
