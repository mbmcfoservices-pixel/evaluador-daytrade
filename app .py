import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 1. Page Configuration
st.set_page_config(page_title="Herramienta Fácil Day Trade", layout="centered")

# 2. Minimalist Dark Mode CSS
st.markdown("""
    <style>
    .stApp {
        background-color: #0d0d0d;
        color: #ffffff;
    }
    div[data-baseweb="input"] > div {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        border: 1px solid #00ff66 !important;
    }
    input {
        color: #ffffff !important;
    }
    div.stButton > button {
        background-color: #00ff66 !important;
        color: #0d0d0d !important;
        font-weight: bold !important;
        border: none !important;
        width: 100% !important;
        padding: 10px !important;
        border-radius: 5px !important;
    }
    div.stButton > button:hover {
        background-color: #00cc52 !important;
        color: #ffffff !important;
    }
    .disclaimer-box {
        background-color: #1a1a00;
        border-left: 4px solid #ffcc00;
        padding: 12px;
        margin-top: 15px;
        margin-bottom: 20px;
        font-size: 0.88rem;
        border-radius: 4px;
    }
    .metric-card {
        background-color: #141414;
        border: 1px solid #262626;
        border-radius: 8px;
        padding: 15px;
        margin-top: 10px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Headers and Disclaimers
st.title("⚡ Analizador de Mercado Day Trade")
st.caption("Estructura de precios simplificada para principiantes y la comunidad")

st.markdown("""
<div class="disclaimer-box">
    <strong>💡 ¿CÓMO USAR ESTA HERRAMIENTA?</strong><br>
    • Esta herramienta <strong>NO te dice cuándo comprar o vender</strong>.<br>
    • Te muestra el estado real del mercado en un lenguaje sencillo para que <strong>tú tomes tus propias decisiones</strong>.<br>
    • Funciona con Acciones (ej. <code>TSLA</code>, <code>NVDA</code>) y Monedas Forex (ej. <code>EURUSD</code>, <code>GBPUSD</code>).
</div>
""", unsafe_allow_html=True)

# 4. Input Form
with st.form(key="trade_form"):
    ticker_symbol = st.text_input("ESCRIBE EL SÍMBOLO DEL ACTIVO (Ej. TSLA, EURUSD, AAPL)", value="", max_chars=15).upper().strip()
    submit_button = st.form_submit_button(label="VER ESTADO DEL MERCADO 🚀")

# 5. Institutional Calculation Engine
if submit_button and ticker_symbol:
    # Auto-fix: If user types a 6-letter FX pair (e.g., 'EURUSD'), automatically append '=X'
    if len(ticker_symbol) == 6 and ticker_symbol.isalpha() and not ticker_symbol.endswith("=X"):
        ticker_symbol = f"{ticker_symbol}=X"

    clean_display_name = ticker_symbol.replace("=X", "")

    with st.spinner(f"Analizando los datos de {clean_display_name}..."):
        try:
            # Download 15-minute timeframe data
            df = yf.download(tickers=ticker_symbol, period="5d", interval="15m", progress=False)
            
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            if df.empty or len(df) < 20:
                st.error("❌ No encontramos ese símbolo. Verifica que esté bien escrito (Ejemplo: TSLA o EURUSD).")
            else:
                latest = df.iloc[-1]
                
                # A. VWAP & Standard Deviation Bands
                tp = (df['High'] + df['Low'] + df['Close']) / 3
                vol = df['Volume'].replace(0, 1) # Tick volume support for Forex
                vwap_series = (tp * vol).cumsum() / vol.cumsum()
                std_dev = df['Close'].std()
                
                current_vwap = vwap_series.iloc[-1]
                upper_band = current_vwap + std_dev
                lower_band = current_vwap - std_dev
                
                # B. Average True Range (ATR 14)
                high_low = df['High'] - df['Low']
                high_close = (df['High'] - df['Close'].shift()).abs()
                low_close = (df['Low'] - df['Close'].shift()).abs()
                tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
                atr = tr.rolling(14).mean().iloc[-1]
                
                # C. Liquidity Clusters (20-Period Extremes)
                liquidity_high = df['High'].tail(20).max()
                liquidity_low = df['Low'].tail(20).min()
                
                # D. Fair Value Gap (FVG) / Structural Imbalance
                fvg_status = "Mercado Ordenado (Equilibrado)"
                fvg_explanation = "El precio se ha movido de forma pareja sin dejar vacíos importantes."
                if len(df) >= 3:
                    c1, c3 = df.iloc[-3], df.iloc[-1]
                    if c3['Low'] > c1['High']:
                        fvg_status = "Hueco Alcista (Rápido impulso hacia arriba)"
                        fvg_explanation = f"El precio subió muy rápido entre {c1['High']:.4f} y {c3['Low']:.4f}. A veces el mercado regresa a 'rellenar' esta zona."
                    elif c3['High'] < c1['Low']:
                        fvg_status = "Hueco Bajista (Rápido impulso hacia abajo)"
                        fvg_explanation = f"El precio cayó muy rápido entre {c3['High']:.4f} y {c1['Low']:.4f}. A veces el mercado regresa a 'rellenar' esta zona."

                # DISPLAY RESULTS
                st.markdown("---")
                st.subheader(f"📊 Reporte de Mercado: {clean_display_name}")
                
                # Main Numbers
                col_price, col_vwap = st.columns(2)
                col_price.metric("Precio Actual", f"{latest['Close']:.4f}", help="El último precio al que se vendió o compró este activo.")
                col_vwap.metric("Precio Justo del Día (VWAP)", f"{current_vwap:.4f}", help="Es el precio promedio ponderado por volumen. Sirve como la 'línea central' del día.")

                # Explanatory Cards
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                st.markdown("#### 1. 📏 Zonas de Precio (¿Está Caro o Barato?)")
                st.write(f"• **Zona Alta (Precio Caro / Sobreextendido):** `{upper_band:.4f}`")
                st.write(f"• **Zona Baja (Precio Barato / Descuento):** `{lower_band:.4f}`")
                st.caption("💡 *Si el precio actual supera la Zona Alta, el mercado está estirado hacia arriba. Si cae de la Zona Baja, está en descuento relativo al día.*")
                st.markdown("</div>", unsafe_allow_html=True)

                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                st.markdown("#### 2. ⚡ Movimiento y Puntos de Interés")
                st.write(f"• **Fuerza de Movimiento (ATR / Volatilidad):** `{atr:.4f}` *(Promedio de cambio por vela)*")
                st.write(f"• **Techo Reciente (Imán Superior):** `{liquidity_high:.4f}`")
                st.write(f"• **Suelo Reciente (Imán Inferior):** `{liquidity_low:.4f}`")
                st.caption("💡 *El Techo y el Suelo son zonas donde muchos operadores ponen sus protecciones (Stop-Loss). El precio suele buscar estas zonas como un imán.*")
                st.markdown("</div>", unsafe_allow_html=True)

                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                st.markdown("#### 3. ⚖️ Vacíos de Mercado (Estructura)")
                st.write(f"**Estado:** {fvg_status}")
                st.caption(f"💡 *{fvg_explanation}*")
                st.markdown("</div>", unsafe_allow_html=True)

                # TRADER INTERPRETATION FRAMEWORK IN LAYMAN TERMS
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("#### 🧠 ¿Cómo interpretar esto bajo tu propio criterio?")
                st.info("""
                1. **Mira el Precio Justo (VWAP):** Si el precio actual está muy cerca del VWAP, el mercado está tranquilo y en equilibrio.
                2. **Identifica los Extremos:** Si el precio llega a la **Zona Alta** o **Zona Baja**, pregúntate: *¿Tiene suficiente fuerza para romper o va a regresar al centro (VWAP)?*
                3. **Usa los Imanes:** Cuando el precio se acerca al Techo o Suelo reciente, suele haber movimientos rápidos porque ahí se activan muchas órdenes automáticas.
                """)
                
        except Exception as e:
            st.error(f"Ocurrió un detalle al leer los datos. Intenta nuevamente.")
