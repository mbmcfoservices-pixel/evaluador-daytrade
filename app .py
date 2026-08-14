import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 1. Page Configuration
st.set_page_config(page_title="Informe Estructural Day Trade", layout="centered")

# 2. Minimalist Dark Mode CSS (Black Background, Green Accent, Yellow PayPal Button)
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
    div[data-testid="stLinkButton"] > a {
        background-color: #ffc439 !important;
        color: #000000 !important;
        font-weight: bold !important;
        border-radius: 5px !important;
        border: none !important;
        width: 100% !important;
        text-align: center !important;
    }
    .disclaimer-box {
        background-color: #1a1a00;
        border-left: 4px solid #ffcc00;
        padding: 10px;
        margin-top: 15px;
        margin-bottom: 20px;
        font-size: 0.85rem;
    }
    .report-card {
        background-color: #141414;
        border: 1px solid #262626;
        border-radius: 8px;
        padding: 15px;
        margin-top: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Headers and Disclaimers
st.title("⚡ Métrica y Estructura Day Trade")
st.caption("Datos cuantitativos e institucionales para Acciones, Forex y Cripto")

st.markdown("""
<div class="disclaimer-box">
    <strong>⚠️ AVISO DE RIESGO OBLIGATORIO:</strong><br>
    • Esta herramienta proporciona datos objetivos para <strong>operaciones de DAY TRADING (Intradía)</strong>.<br>
    • <strong>NO emite señales de compra o venta</strong>. Evalúa los datos bajo tu propio criterio y gestión de riesgo.<br>
    • Compatible con Acciones (ej. TSLA, NVDA) y Divisas Forex (ej. EURUSD=X, GBPUSD=X).<br>
    • Invierte de manera responsable y utiliza siempre un stop-loss estricto.
</div>
""", unsafe_allow_html=True)

# 4. Input Form
with st.form(key="trade_form"):
    ticker_symbol = st.text_input("SÍMBOLO DEL TICKER (Ej. TSLA, EURUSD=X, AAPL)", value="", max_chars=15).upper().strip()
    submit_button = st.form_submit_button(label="ANALIZAR ESTRUCTURA (GO)")

# 5. Donation Area Below Ticker
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style="background-color: #1a0000; border-left: 4px solid #ff4444; padding: 12px; border-radius: 4px; margin-bottom: 15px;">
    <strong>🇨🇴 Fondo de Ayuda Humanitaria:</strong><br>
    El 100% de los fondos recaudados a través de esta herramienta serán destinados directamente a apoyar a las familias y comunidades afectadas por los recientes terremotos en Colombia.
</div>
""", unsafe_allow_html=True)

# *** REEMPLAZA CON TU ENLACE REAL DE PAYPAL CUANDO LO TENGAS ***
PAYPAL_DONATE_URL = "https://www.paypal.com"

st.link_button("💛 Donar y Apoyar a Colombia (PayPal)", url=PAYPAL_DONATE_URL)
st.markdown("---")

# 6. Institutional Calculation Engine
if submit_button and ticker_symbol:
    with st.spinner(f"Obteniendo estructura de mercado para {ticker_symbol}..."):
        try:
            # Download 15-minute timeframe data
            df = yf.download(tickers=ticker_symbol, period="5d", interval="15m", progress=False)
            
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            if df.empty or len(df) < 20:
                st.error("❌ Símbolo no encontrado o datos insuficientes. Para Forex añade '=X' al final (Ej. EURUSD=X).")
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
                fvg_status = "Estructura Balanceada"
                if len(df) >= 3:
                    c1, c3 = df.iloc[-3], df.iloc[-1]
                    if c3['Low'] > c1['High']:
                        fvg_status = f"Desbalance Alcista [{c1['High']:.4f} - {c3['Low']:.4f}]"
                        fvg_color = "green"
                    elif c3['High'] < c1['Low']:
                        fvg_status = f"Desbalance Bajista [{c3['High']:.4f} - {c1['Low']:.4f}]"
                        fvg_color = "red"
                    else:
                        fvg_color = "white"

                # DISPLAY RESULTS
                st.subheader(f"📊 Informe de Mercado: {ticker_symbol}")
                
                col_price, col_vwap = st.columns(2)
                col_price.metric("Precio Actual", f"{latest['Close']:.4f}")
                col_vwap.metric("VWAP de la Sesión", f"{current_vwap:.4f}")

                st.markdown("<div class='report-card'>", unsafe_allow_html=True)
                st.markdown("#### 🎯 Niveles de Liquidez y Desviación")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Banda Superior VWAP (+1 σ):** {upper_band:.4f}")
                    st.write(f"**Banda Inferior VWAP (-1 σ):** {lower_band:.4f}")
                    st.write(f"**Volatilidad (ATR 14):** {atr:.4f}")
                with col2:
                    st.write(f"**Piscina de Liquidez Superior:** {liquidity_high:.4f}")
                    st.write(f"**Piscina de Liquidez Inferior:** {liquidity_low:.4f}")
                    st.write(f"**Estado Estructural:** {fvg_status}")
                st.markdown("</div>", unsafe_allow_html=True)

                # TRADER INTERPRETATION FRAMEWORK
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("#### 🧠 Guía para la Interpretación del Operador:")
                st.info("""
                • **Precio por encima de VWAP (+1 σ):** El mercado se encuentra en estado sobreextendido. Evalúa posibles reversiones a la media o rupturas de alto volumen.
                • **Precio por debajo de VWAP (-1 σ):** El mercado cotiza con descuento en relación al volumen de la sesión.
                • **Piscinas de Liquidez:** Representan zonas donde se acumulan órdenes de Stop-Loss. Los algoritmos suelen buscar estas zonas antes de cambiar de dirección.
                """)
                
        except Exception as e:
            st.error(f"Error procesando los datos: {e}")
