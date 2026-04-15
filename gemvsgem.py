"""
GEM STRATEGY TRACKER v4.0
SYSTEM: macOS / Windows / Linux
TARGET: Gold, BTC, and Selected ETFs

"""

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import logging

# ==============================================================================
# 1. KONFIGURACJA ŚRODOWISKA I LOGOWANIA
# ==============================================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="GEM STRATEGY PRO",
    page_icon="wykres.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# 2. STYLE CSS (ZGODNIE ZE ZDJĘCIEM)
# ==============================================================================
def apply_advanced_styles():
    st.markdown("""
        <style>
        .stApp { background-color: #0d1117; color: #e6edf3; }
        .gem-card {
            background: linear-gradient(145deg, #161b22, #0d1117);
            border-radius: 12px;
            padding: 24px;
            border: 1px solid #30363d;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
            transition: all 0.3s ease;
            margin-bottom: 15px;
        }
        .gem-card:hover {
            border-color: #58a6ff;
            transform: translateY(-4px);
            box-shadow: 0 8px 20px rgba(88, 166, 255, 0.2);
        }
        .ticker-name { font-size: 1.25rem; font-weight: 700; color: #8b949e; margin-bottom: 10px; }
        .pct-value { font-size: 2.3rem; font-weight: 900; margin: 12px 0; }
        .pos { color: #3fb950; text-shadow: 0 0 8px rgba(63, 185, 80, 0.3); }
        .neg { color: #f85149; text-shadow: 0 0 8px rgba(248, 81, 73, 0.3); }
        .price-sub { color: #6e7681; font-size: 0.9rem; margin-top: 5px; }
        section[data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
        .js-plotly-plot { border: 1px solid #30363d; border-radius: 10px; }
        </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 3. MAPOWANIE TWOICH NAZW
# ==============================================================================
ASSETS_CONFIG = {
    "GC=F": "Gold",
    "BTC-USD": "BTC-USD",
    "CNDX.L": "CNDX.L",
    "IB01.L": "IB01.L",
    "CBU0.L": "CBU0.L",
    "IWDA.L": "IWDA.L",
    "EIMI.L": "EIMI.L"
}

# ==============================================================================
# 4. FUNKCJA POBIERANIA DANYCH
# ==============================================================================
@st.cache_data(ttl=3600)
def load_market_data(names_to_fetch, start_date, end_date):
    tickers = [t for t, n in ASSETS_CONFIG.items() if n in names_to_fetch]
    if not tickers:
        return None
    try:
        df = yf.download(tickers, start=start_date, end=end_date, progress=False, auto_adjust=True)
        if df.empty:
            return None
        final_df = df['Close'] if 'Close' in df.columns else df
        if isinstance(final_df, pd.Series):
            final_df = final_df.to_frame()
            final_df.columns = tickers
        return final_df.ffill().dropna()
    except Exception as e:
        logger.error(f"Błąd: {e}")
        return None

# ==============================================================================
# 5. PANEL BOCZNY (TUTAJ JEST ROZWIĄZANIE TWOJEGO PROBLEMU)
# ==============================================================================
def render_controls():
    # Ikona pieniędzy ze zdjęcia
    st.sidebar.image("money_.png", width=100)
    st.sidebar.title("Selected ETFs")
    st.sidebar.write("---")
    
    selected_names = st.sidebar.multiselect(
        "Jaki obiekt wariacie:",
        options=list(ASSETS_CONFIG.values()),
        default=list(ASSETS_CONFIG.values()),
        key="final_v_reset"
    )
    
    st.sidebar.write("---")
    st.sidebar.subheader("Horyzont czasowy")
    
    # Wybór okresu
    periods = {"1 Miesiąc": 1, "3 Miesiące": 3, "6 Miesięcy": 6, "12 Miesięcy": 12, "Własny": "custom"}
    period_label = st.sidebar.selectbox("Okres analizy:", list(periods.keys()), index=4)
    
    # LOGIKA DATY KONCOWEJ - TO O TO CI CHODZIŁO:
    if periods[period_label] == "custom":
        st.sidebar.info("Ustaw własny zakres dat:")
        start_date = st.sidebar.date_input("Start (Od):", date.today() - relativedelta(years=1))
        end_date = st.sidebar.date_input("Koniec (Do):", date.today())
    else:
        end_date = date.today()
        start_date = end_date - relativedelta(months=periods[period_label])
        
    st.sidebar.write("---")
    st.sidebar.subheader("Widoczność")
    v_mode = st.sidebar.radio("Skala wykresu:", ["Procentowa zmiana (%)", "Wartość nominalna ($)"])
    c_height = st.sidebar.slider("Wielkość wykresu (px)", 300, 1000, 550)
    
    return selected_names, start_date, end_date, v_mode, c_height

# 6. LOGIKA GŁÓWNA

def main():
    apply_advanced_styles()
    selected_names, start_dt, end_dt, view_mode, chart_h = render_controls()
    
    st.title("🚀 Global Equity Momentum")
    st.caption(f"Zakres analizy: {start_dt} do {end_dt}")

    if not selected_names:
        st.warning("⚠️ Wybierz instrumenty w ustawieniach.")
        return

    with st.spinner('Przetwarzanie danych...'):
        data = load_market_data(selected_names, start_dt, end_dt)

    if data is not None and not data.empty:
        final_stats = []
        for ticker, name in ASSETS_CONFIG.items():
            if name in selected_names and ticker in data.columns:
                series = data[ticker]
                val_start, val_end = series.iloc[0], series.iloc[-1]
                pct_move = ((val_end - val_start) / val_start) * 100
                abs_move = val_end - val_start
                final_stats.append({
                    'label': name, 'price': val_end, 'pct': pct_move, 
                    'abs': abs_move, 'history': series, 'base': val_start
                })

        final_stats = sorted(final_stats, key=lambda x: x['pct'], reverse=True)

        # WYKRES
        fig = go.Figure()
        for item in final_stats:
            y_vals = ((item['history'] / item['base']) - 1) * 100 if view_mode == "Procentowa zmiana (%)" else item['history']
            fig.add_trace(go.Scatter(x=data.index, y=y_vals, name=item['label'], mode='lines', line=dict(width=3)))

        fig.update_layout(
            template="plotly_dark", height=chart_h, margin=dict(l=0, r=0, t=10, b=0),
            hovermode="x unified", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

        # RANKING
        st.markdown("---")
        st.subheader("📋 Ranking Momentum")
        cols = st.columns(len(final_stats))
        for idx, item in enumerate(final_stats):
            with cols[idx]:
                st.markdown(f"""
                    <div class="gem-card">
                        <div class="ticker-name">{item['label']}</div>
                        <div class="pct-value {"pos" if item['pct'] >= 0 else "neg"}">
                            {"▲" if item['pct'] >= 0 else "▼"} {item['pct']:.2f}%
                        </div>
                        <div class="price-sub">Cena: {item['price']:.2f}<br>Zmiana: {item['abs']:+.2f}</div>
                    </div>
                """, unsafe_allow_html=True)
        st.write("---")
        st.success(f"💡 Lider: **{final_stats[0]['label']}**")
    else:
        st.error("Brak danych dla wybranego zakresu.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Błąd krytyczny: {e}")

