import streamlit as st
import yfinance as yf
import pandas as pd

# 1. Page Config
st.set_page_config(page_title="Evaluador de Riesgo Day Trade", layout="centered")

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
    </style>
""", unsafe_allow_html=True)

# 3. Headers and Disclaimers
st.title("⚡ Evaluador de Riesgo Day Trade")
st.caption("Herramienta cuantitativa para operaciones intradía (Day Trading)")

st.markdown("""
<div class="disclaimer-box">
    <strong>⚠️ AVISO DE RIESGO OBLIGATORIO:</strong><br>
    • Esta herramienta evalúa parámetros exclusivamente para <strong>operaciones de DAY TRADING (Intradía)</strong>.<br>
    • <strong>NO aplica</strong> para inversiones a mediano o largo plazo.<br>
    • Los resultados son modelos de probabilidad y <strong>NO garantizan rendimiento futuro</strong>.<br>
    • Invierte de manera responsable y gestiona siempre tu capital con un stop-loss estricto.
</div>
""", unsafe_allow_html=True)

# 4. Input Form
with st.form(key="trade_form"):
    ticker_symbol = st.text_input("SÍMBOLO DEL TICKER (Ej. TSLA, NVDA, AAPL)", value="", max_chars=10).upper().strip()
    submit_button = st.form_submit_button(label="ANALIZAR RIESGO (GO)")

# 5. Donation Area Below Ticker
st.markdown("<br>", unsafe_allow_html=True)
st.write("☕ **¿Te resulta útil esta herramienta?** Apoya el mantenimiento del servidor con una donación.")

# *** PASTE YOUR PAYPAL LINK HERE ***
PAYPAL_DONATE_URL = "https://www.paypal.com"

st.link_button("💛 Donar con PayPal", url=PAYPAL_DONATE_URL)
st.markdown("---")

# 6. Evaluation Logic
if submit_button and ticker_symbol:
    with st.spinner(f"Analizando métricas intradía para {ticker_symbol}..."):
        try:
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period="1mo")
            info = ticker.info
            
            if hist.empty:
                st.error("❌ Símbolo no encontrado. Por favor verifica el ticker ingresado.")
            else:
                vol_actual = hist['Volume'].iloc[-1]
                vol_promedio = hist['Volume'].mean()
                rvol = vol_actual / vol_promedio if vol_promedio > 0 else 1.0
                
                float_shares = info.get('floatShares', 0)
                short_pct = (info.get('shortPercentOfFloat', 0) or 0) * 100
                
                try:
                    expiraciones = ticker.options
                    iv_promedio = ticker.option_chain(expiraciones[0]).calls['impliedVolatility'].mean() * 100 if expiraciones else 0
                except:
                    iv_promedio = 0
                
                score_rvol = 10 if rvol >= 2.5 else (7 if rvol >= 1.5 else 3)
                score_short = 10 if short_pct >= 15 else (7 if short_pct >= 7 else 4)
                score_float = 9 if (float_shares and float_shares < 50e6) else 5
                score_iv = 9 if iv_promedio >= 70 else (7 if iv_promedio >= 35 else 3)
                
                puntaje_final = round((score_rvol * 0.35) + (score_float * 0.20) + (score_short * 0.25) + (score_iv * 0.20), 1)

                st.metric(label="PUNTUACIÓN DE RIESGO / MOMENTO (1 a 10)", value=f"{puntaje_final} / 10")
                
                if puntaje_final >= 8.0:
                    st.success("🔥 **EVALUACIÓN:** Alta volatilidad y volumen. Configuración óptima para Day Trading con gestión estricta de riesgo.")
                elif puntaje_final >= 5.5:
                    st.warning("⚡ **EVALUACIÓN:** Configuración moderada. Requiere confirmación de patrón técnico antes de entrar.")
                else:
                    st.error("🚫 **EVALUACIÓN:** Bajo volumen o momentum. Alto riesgo de estancamiento (Chop). No recomendado para Day Trade hoy.")

                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Volumen Relativo (RVOL):** {rvol:.2f}x")
                    st.write(f"**Interés en Corto:** {short_pct:.1f}%")
                with col2:
                    flotante_m = f"{float_shares/1e6:.1f}M" if float_shares else "N/D"
                    st.write(f"**Acciones en Flotante:** {flotante_m}")
                    st.write(f"**Volatilidad Implícita:** {iv_promedio:.1f}%")
                    
        except Exception as e:
            st.error(f"Error procesando los datos: {e}")
