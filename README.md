# Bot de Alertas RSI + MACD + ADX para Criptomonedas

Este bot analiza los pares USDT del Top 100 de CoinGecko usando temporalidades de 4h y 1D. Envía alertas por Telegram cuando detecta condiciones extremas de RSI junto con señales de MACD y la fuerza de tendencia usando ADX.

## Indicadores usados:
- RSI (Sobrecomprado/Sobrevendido)
- MACD (Cruces alcistas/bajistas)
- ADX (Fuerza de la tendencia)

## Configuración en Render.com

1. Subir este proyecto a GitHub.
2. Crear un **Background Worker** en [https://render.com](https://render.com).
3. Variables de entorno necesarias:
   - `TELEGRAM_TOKEN`: token de tu bot
   - `TELEGRAM_CHAT_ID`: canal o grupo destino

## Ejecución continua

El bot corre indefinidamente y escanea el mercado cada 2 horas.