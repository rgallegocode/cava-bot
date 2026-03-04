import os
import requests
import yfinance as yf
from google import genai
import schedule
import time
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURACIÓN Y CREDENCIALES
# ==========================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Configurar el nuevo cliente de Gemini
cliente_gemini = genai.Client(api_key=GEMINI_API_KEY)

# ==========================================
# 2. FUNCIONES PRINCIPALES
# ==========================================

def obtener_noticias():
    """Obtiene las noticias financieras y mundiales de las últimas 24 horas usando NewsAPI."""
    print("Obteniendo noticias del mundo...")
    ayer = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    url = f"https://newsapi.org/v2/everything?q=economy OR stock market OR geopolitics&from={ayer}&sortBy=popularity&language=es&apiKey={NEWS_API_KEY}"
    
    try:
        respuesta = requests.get(url).json()
        titulares = []
        
        if respuesta.get("status") == "ok":
            for articulo in respuesta["articles"][:15]:
                titulares.append(f"- {articulo.get('title', 'Sin título')}: {articulo.get('description', 'Sin descripción')}")
                
        return "\n".join(titulares)
    except Exception as e:
        print(f"Error obteniendo noticias: {e}")
        return "No se pudieron obtener las noticias de hoy."

def obtener_datos_yahoo():
    """Obtiene precios y variaciones de Yahoo Finance para los activos solicitados."""
    print("Obteniendo datos de mercado de Yahoo Finance...")
    
    # Usamos ETFs representativos para los índices globales que pides
    activos = {
        "MSCI World (iShares URTH)": "URTH",
        "Vanguard Emerging Markets": "VWO",
        "Bitcoin": "BTC-USD"
    }
    
    datos_mercado = "📊 DATOS REALES DEL MERCADO HOY:\n"
    
    for nombre, ticker in activos.items():
        try:
            historial = yf.Ticker(ticker).history(period="2d")
            if len(historial) >= 2:
                precio_ayer = historial['Close'].iloc[0]
                precio_hoy = historial['Close'].iloc[1]
                variacion = ((precio_hoy - precio_ayer) / precio_ayer) * 100
                datos_mercado += f"- {nombre}: {precio_hoy:,.2f} ({variacion:+.2f}%)\n"
            else:
                # Si solo hay 1 día (ej. fin de semana/festivo)
                precio_hoy = historial['Close'].iloc[-1]
                datos_mercado += f"- {nombre}: {precio_hoy:,.2f} (Mercado cerrado/Sin variación)\n"
        except Exception as e:
            print(f"Error obteniendo {nombre}: {e}")
            datos_mercado += f"- {nombre}: Error al obtener datos.\n"
            
    return datos_mercado

def analizar_con_ia(contexto_completo):
    """Envía las noticias y los datos a la IA para que redacte el boletín al estilo Cava."""
    print("Analizando datos con Gemini...")
    
    prompt = f"""
    Eres 'Cava Bot', un analista financiero experto, directo y sin pelos en la lengua, con el inconfundible estilo de José Luis Cava. 
    Tu misión es redactar el reporte diario del mercado para tus seguidores usando la información real que te proporciono a continuación.
    
    AQUÍ TIENES LOS DATOS REALES Y NOTICIAS DE HOY:
    {contexto_completo}

    REGLA DE ORO ("Las Maldades"): 
    Cada vez que el mercado caiga, haya datos macroeconómicos desastrosos, manipulación institucional o decisiones de los bancos centrales que perjudiquen al inversor, DEBES referirte a estos eventos explícitamente como "Las Maldades" o "Las maldades de los de siempre".

    ESTRUCTURA OBLIGATORIA DEL MENSAJE:
    
    1. ☀️ El tiempo en Málaga: Una sola frase breve con la temperatura y el estado del cielo actual (invéntalo de forma realista si no tienes el dato exacto, pero que suene natural).
    
    2. 📰 Resumen de las últimas 24h: Las 5 noticias más importantes de la bolsa y la economía. Usa viñetas y emojis. Sé extremadamente conciso y directo al grano. Incluye siempre una mención a Bitcoin si los datos lo justifican.
    
    3. 😈 Las Maldades del Mercado: Un párrafo corto analizando lo peor de la jornada usando tu término estrella ("maldades"). Si el día ha sido espectacularmente bueno, di claramente que "hoy nos hemos librado de sus maldades".
    
    4. 🔮 Previsión y Cierre de Mercado: 
       - Comienza indicando claramente si estamos en 🐂 Bull Market o 🐻 Bear Market con una brevísima justificación de una sola línea.
       - A continuación, muestra OBLIGATORIAMENTE el cierre de los 3 activos proporcionados, aplicando esta regla estricta:
         * Si el porcentaje es positivo (+), añade al final el gráfico verde 📈.
         * Si el porcentaje es negativo (-), añade al final el gráfico rojo 📉.
       - Formato exacto que debes usar para los datos:
         • MSCI World: [Precio] ([Variación]%) [Emoji]
         • Vanguard Emerging Markets: [Precio] ([Variación]%) [Emoji]
         • Bitcoin: $[Precio] USD ([Variación]%) [Emoji]
         
    No inventes precios ni porcentajes que no estén en los datos proporcionados.
    """
    
    try:
        respuesta = cliente_gemini.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return respuesta.text
    except Exception as e:
        print(f"Error generando el texto con Gemini: {e}")
        return f"Ups, Cava Bot tuvo un problema analizando los datos hoy. Error: {e}"

def enviar_telegram(mensaje):
    """Envía el texto final a tu chat de Telegram."""
    print("Enviando mensaje a Telegram...")
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown"
    }
    requests.post(url, data=payload)
    print(f"[{datetime.now()}] Mensaje enviado a Telegram con éxito.")

def trabajo_diario():
    """La rutina completa de Cava Bot."""
    print("\n--- Iniciando Cava Bot ---")
    
    # 1. Obtener datos de ambos mundos (Noticias + Yahoo Finance)
    noticias = obtener_noticias()
    datos_mercado = obtener_datos_yahoo()
    
    # 2. Unir todo para dárselo a la IA
    contexto_completo = f"{datos_mercado}\n\nNOTICIAS DE HOY:\n{noticias}"
    
    # 3. Analizar y enviar
    analisis_ia = analizar_con_ia(contexto_completo)
    enviar_telegram(analisis_ia)
    print("--- Proceso finalizado ---\n")

# ==========================================
# 3. EJECUCIÓN DEL BOT (VERSIÓN NUBE)
# ==========================================
# PRUEBA RÁPIDA
# trabajo_diario()

if __name__ == "__main__":
    trabajo_diario()
