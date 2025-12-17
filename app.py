"""
Crypto Tick Data Analytics Platform - Enhanced Version
Real-time data collection with advanced quantitative analytics
"""

import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import time
from datetime import datetime, timedelta

from config import Config
from database import (
    init_db, get_ticks, get_statistics, clear_database,
    get_price_change, get_database_size, cleanup_old_data,
    save_ohlc_data, get_ohlc_data
)
from collector import BatchTickCollector
from analytics import Analytics
from visualizations import (
    create_ohlc_chart, create_single_ohlc_chart, create_spread_chart, create_correlation_heatmap,
    create_backtest_chart, create_distribution_chart, create_rolling_correlation_chart
)

st.set_page_config(
    page_title="Crypto Analytics Platform",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background: #0a0a0f;
        background-color: #0a0a0f;  /* Fallback */
        background-image: 
            radial-gradient(ellipse at top, rgba(29, 78, 137, 0.15) 0%, transparent 50%),
            radial-gradient(ellipse at bottom right, rgba(99, 102, 241, 0.1) 0%, transparent 50%),
            radial-gradient(ellipse at bottom left, rgba(16, 185, 129, 0.08) 0%, transparent 50%);
        background-attachment: fixed;
        min-height: 100vh;
    }
    
    /* Force dark background on main container to prevent white flash */
    [data-testid="stAppViewContainer"] {
        background-color: #0a0a0f;
    }
    
    .main .block-container {
        background: rgba(15, 23, 35, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 2rem;
        margin: 1rem;
        backdrop-filter: blur(20px);
    }

    .hero-section {
        text-align: center;
        padding: 80px 20px 60px;
        position: relative;
    }
    
    .hero-badge {
        display: inline-block;
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(16, 185, 129, 0.2));
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 20px;
        padding: 6px 16px;
        font-size: 0.75rem;
        color: #a5b4fc;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 24px;
    }
    
    .hero-title {
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #ffffff 0%, #a5b4fc 50%, #10b981 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 20px;
        line-height: 1.1;
        letter-spacing: -1px;
    }
    
    .hero-subtitle {
        font-size: 1.25rem;
        color: #8899a6;
        margin-bottom: 40px;
        max-width: 600px;
        margin-left: auto;
        margin-right: auto;
        line-height: 1.6;
        font-weight: 400;
    }
    
    .feature-card {
        background: linear-gradient(145deg, rgba(20, 30, 48, 0.8), rgba(15, 23, 35, 0.9));
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 28px;
        text-align: left;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .feature-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.5), transparent);
        opacity: 0;
        transition: opacity 0.4s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-4px);
        border-color: rgba(99, 102, 241, 0.3);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
    }
    
    .feature-card:hover::before {
        opacity: 1;
    }
    
    .feature-icon {
        width: 48px;
        height: 48px;
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(16, 185, 129, 0.2));
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 16px;
        font-size: 1.5rem;
    }
    
    .feature-card h3 {
        color: #ffffff;
        margin-bottom: 10px;
        font-size: 1.1rem;
        font-weight: 600;
    }
    
    .feature-card p {
        color: #8899a6;
        font-size: 0.9rem;
        line-height: 1.6;
        margin: 0;
    }
    
    .steps-container {
        background: linear-gradient(145deg, rgba(20, 30, 48, 0.6), rgba(15, 23, 35, 0.8));
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 32px;
        margin: 40px 0;
    }
    
    .step-item {
        display: flex;
        align-items: flex-start;
        margin-bottom: 20px;
        padding: 16px;
        border-radius: 12px;
        transition: all 0.3s ease;
    }
    
    .step-item:hover {
        background: rgba(99, 102, 241, 0.05);
    }
    
    .step-number {
        width: 32px;
        height: 32px;
        background: linear-gradient(135deg, #6366f1, #10b981);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.9rem;
        color: #ffffff;
        margin-right: 16px;
        flex-shrink: 0;
    }
    
    .step-content h4 {
        color: #ffffff;
        margin: 0 0 4px 0;
        font-size: 1rem;
        font-weight: 600;
    }
    
    .step-content p {
        color: #8899a6;
        margin: 0;
        font-size: 0.9rem;
    }
    
    .cta-container {
        text-align: center;
        padding: 40px 0;
    }
    
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        text-align: center;
        color: #ffffff;
        margin-bottom: 0.5rem;
        letter-spacing: -0.5px;
    }
    
    .header-nav {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        padding-bottom: 16px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    .nav-brand {
        font-size: 1.2rem;
        font-weight: 700;
        color: #ffffff;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: rgba(20, 30, 48, 0.8);
        padding: 6px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        padding: 10px 20px;
        color: #8899a6 !important;
        font-weight: 500;
        font-size: 0.85rem;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(99, 102, 241, 0.1);
        color: #a5b4fc !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #6366f1, #4f46e5);
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f1419 0%, #15202b 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }
    
    [data-testid="stSidebar"] * {
        color: #d9d9d9 !important;
    }
    
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #ffffff !important;
        font-weight: 600;
        font-size: 0.9rem !important;
    }
    
    .metric-card {
        background: linear-gradient(145deg, rgba(20, 30, 48, 0.9), rgba(15, 23, 35, 0.95));
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 24px;
        margin: 8px 0;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        border-color: rgba(99, 102, 241, 0.3);
        transform: translateY(-2px);
        box-shadow: 0 12px 24px rgba(0, 0, 0, 0.2);
    }
    
    .metric-label {
        font-size: 0.7rem;
        color: #8899a6 !important;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 8px;
        font-weight: 600;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #ffffff !important;
    }
    
   
    .stButton>button {
        background: linear-gradient(135deg, #6366f1, #4f46e5);
        color: #ffffff !important;
        border: none;
        border-radius: 10px;
        padding: 12px 28px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #4f46e5, #4338ca);
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(99, 102, 241, 0.4);
    }
    

    .stDownloadButton>button {
        background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
    }
    

    div[data-testid="stMetricValue"] {
        font-size: 1.5rem;
        font-weight: 700;
        color: #ffffff !important;
    }
    
    div[data-testid="stMetricLabel"] {
        color: #8899a6 !important;
        font-weight: 500;
        font-size: 0.8rem;
    }
    
    div[data-testid="stMetricDelta"] svg {
        display: none;
    }
    
    /* === STATUS INDICATOR === */
    .status-indicator {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-active {
        background: #10b981;
        box-shadow: 0 0 12px rgba(16, 185, 129, 0.6);
        animation: pulse-green 2s infinite;
    }
    
    .status-inactive {
        background: #ef4444;
    }
    
    @keyframes pulse-green {
        0%, 100% { box-shadow: 0 0 12px rgba(16, 185, 129, 0.6); }
        50% { box-shadow: 0 0 20px rgba(16, 185, 129, 0.8); }
    }
    
    /* === INPUTS === */
    .stTextInput input, .stSelectbox > div > div, .stNumberInput input {
        background: rgba(20, 30, 48, 0.8) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #ffffff !important;
        border-radius: 10px;
    }
    
    .stTextInput input:focus, .stSelectbox > div > div:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2) !important;
    }
    
    /* === DATAFRAMES === */
    .stDataFrame {
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
    }
    
    /* === SLIDERS === */
    .stSlider > div > div > div {
        background: linear-gradient(90deg, #6366f1, #10b981) !important;
    }
    
    /* === ALERTS === */
    .stAlert {
        background: rgba(20, 30, 48, 0.9) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 12px;
        color: #d9d9d9 !important;
    }
    
    /* === EXPANDER === */
    .streamlit-expanderHeader {
        background: rgba(20, 30, 48, 0.8) !important;
        color: #ffffff !important;
        border-radius: 10px;
    }
    
    /* === HEADINGS === */
    h1, h2, h3 {
        color: #ffffff !important;
    }
    
    /* === TEXT === */
    p, span, label {
        color: #d9d9d9 !important;
    }
    
    /* === FIX: Remove white line/separator at top === */
    header[data-testid="stHeader"] {
        background: transparent !important;
        border-bottom: none !important;
    }
    
    .stDeployButton {
        display: none;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* === File Uploader Dark Theme === */
    [data-testid="stFileUploader"] {
        background: rgba(20, 30, 48, 0.8) !important;
        border-radius: 12px;
        padding: 12px;
    }
    
    [data-testid="stFileUploader"] section {
        background: rgba(15, 23, 35, 0.9) !important;
        border: 2px dashed rgba(99, 102, 241, 0.3) !important;
        border-radius: 10px;
    }
    
    [data-testid="stFileUploader"] section > div {
        color: #8899a6 !important;
    }
    
    [data-testid="stFileUploader"] button {
        background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px;
    }
    
    [data-testid="stFileUploader"] small {
        color: #8899a6 !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database
init_db()

# Session state initialization
if 'collector' not in st.session_state:
    st.session_state.collector = BatchTickCollector(buffer_size=10000, batch_size=50, batch_interval=3)
    from database import insert_tick
    def save_tick(tick):
        try:
            insert_tick(tick['symbol'], tick['timestamp'], tick['price'], tick['size'])
        except Exception as e:
            print(f"Error inserting tick: {e}")
    st.session_state.collector.set_callback(save_tick)

if 'collecting' not in st.session_state:
    st.session_state.collecting = False
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()
if 'alerts' not in st.session_state:
    st.session_state.alerts = []
if 'page' not in st.session_state:
    st.session_state.page = 'landing'
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []  # List of positions
if 'closed_trades' not in st.session_state:
    st.session_state.closed_trades = []  # Closed trade history

# Only auto-refresh when collecting data
if st.session_state.get('collecting', False):
    st_autorefresh(interval=Config.REFRESH_INTERVAL, key="data-refresh")


def show_landing_page():
    """Display a stunning landing page with instructions"""
    
    # Top navigation with Launch Dashboard button
    col1, col2, col3 = st.columns([2, 1, 1])
    with col3:
        st.markdown("""
            <div style="text-align: right;">
                <a href="/?page=dashboard" target="_blank" style="
                    display: inline-block;
                    text-decoration: none;
                    background: linear-gradient(135deg, #6366f1 0%, #10b981 100%);
                    color: white;
                    padding: 8px 16px;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 0.9rem;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
                    transition: transform 0.2s;
                ">
                    Launch Dashboard &rarr;
                </a>
            </div>
        """, unsafe_allow_html=True)
    
    # Hero Section
    st.markdown("""
    <div style="text-align: center; padding: 20px 20px 40px;">
        <div style="display: inline-block; background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(16, 185, 129, 0.2)); border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 20px; padding: 6px 16px; font-size: 0.75rem; color: #a5b4fc; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 24px;">Quantitative Trading Tools</div>
        <h1 style="font-size: 3.2rem; font-weight: 800; background: linear-gradient(135deg, #ffffff 0%, #a5b4fc 50%, #10b981 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin-bottom: 20px; line-height: 1.1; letter-spacing: -1px;">Binance Analytics<br>Platform</h1>
        <p style="font-size: 1.15rem; color: #8899a6; margin-bottom: 30px; max-width: 600px; margin-left: auto; margin-right: auto; line-height: 1.6; text-align: center;">
            Professional-grade tools for real-time market data collection, 
            statistical arbitrage analysis, and algorithmic trading backtesting.
        </p>
    </div>
    """, unsafe_allow_html=True)
    

    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">&#9889;</div>
            <h3>Real-Time Data Collection</h3>
            <p>Connect to Binance WebSocket feeds for live tick data. Track multiple trading pairs simultaneously with millisecond precision. Auto-saves to SQLite database.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">&#128202;</div>
            <h3>OHLC Candlestick Charts</h3>
            <p>Interactive candlestick charts with volume. Multiple timeframes (1s to 5min). Dual Y-axis for comparing assets with different price scales.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">&#128200;</div>
            <h3>Pair Trading Analytics</h3>
            <p>Calculate hedge ratios using OLS/Huber regression. Real-time spread and z-score calculation. Rolling correlation analysis. ADF stationarity tests.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col4, col5, col6 = st.columns(3)
    
    with col4:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">&#127919;</div>
            <h3>Strategy Backtesting</h3>
            <p>Mean-reversion backtest with customizable entry/exit thresholds. Trade log with P&L analysis. Win rate and performance metrics visualization.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">&#128176;</div>
            <h3>Portfolio & P&L Tracker</h3>
            <p>Paper trading with LONG/SHORT positions. Real-time unrealized P&L updates. Trade history with win rate statistics. Portfolio value tracking.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col6:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">&#128276;</div>
            <h3>Price & Z-Score Alerts</h3>
            <p>Set alerts for price thresholds. Z-score alerts for pair trading signals. Real-time monitoring with visual notifications when triggered.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    
    st.markdown("---")
    st.markdown("<h3 style='text-align: center; color: #ffffff;'>Getting Started</h3>", unsafe_allow_html=True)
    st.markdown("")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**1. Configure Symbols**")
        st.caption("Enter trading pairs in lowercase (e.g., btcusdt, ethusdt)")
        
        st.markdown("")
        
        st.markdown("**2. Start Collection**")
        st.caption("Click the Start button to begin receiving live market data")
    
    with col2:
        st.markdown("**3. Wait for Data**")
        st.caption("Allow 1-2 minutes for sufficient data to accumulate")
        
        st.markdown("")
        
        st.markdown("**4. Analyze & Export**")
        st.caption("Navigate through tabs to view charts, analytics, and export data")
    
    st.markdown("---")
    
    # CTA Button
    st.markdown("<div class='cta-container'>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1.2, 1, 1.2])
    with col2:
        # Link button to open dashboard in new tab
        st.markdown("""
            <div style="text-align: center;">
                <a href="/?page=dashboard" target="_blank" style="
                    display: inline-block;
                    text-decoration: none;
                    background: linear-gradient(135deg, #6366f1 0%, #10b981 100%);
                    color: white;
                    padding: 12px 28px;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 1.1rem;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
                    transition: transform 0.2s;
                ">
                    Launch Dashboard 🚀
                </a>
            </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def show_dashboard():
    """Display the main dashboard"""
    
    # Header with navigation
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("← Home", key="back_home"):
            st.session_state.page = 'landing'
            st.rerun()
    with col2:
        st.markdown('<h1 class="main-header">Binance Analytics Platform</h1>', unsafe_allow_html=True)
    with col3:
        pass  # Can add other nav items here
    
    st.markdown("*Real-time statistical arbitrage & market-making analytics*")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.markdown("### Configuration")
        
        # Symbol input
        symbols_input = st.text_input(
            "Trading Symbols",
            value="btcusdt,ethusdt",
            help="Comma-separated symbols (lowercase)"
        )
        symbols = [s.strip().lower() for s in symbols_input.split(',') if s.strip()]
        
        st.markdown("---")
        
        # Control buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Start", key="start_btn"):
                if not st.session_state.collecting:
                    st.session_state.collector.start(symbols)
                    st.session_state.collecting = True
                    st.success("Started!")
                    st.rerun()
                else:
                    st.warning("Already collecting!")
        
        with col2:
            if st.button("Stop", key="stop_btn"):
                if st.session_state.collecting:
                    st.session_state.collector.stop()
                    st.session_state.collecting = False
                    st.success("Stopped!")
                    st.rerun()
                else:
                    st.info("Not collecting")
        
        # Status
        collector_stats = st.session_state.collector.get_stats()
        status_class = "status-active" if st.session_state.collecting else "status-inactive"
        status_text = "Active" if st.session_state.collecting else "Inactive"
        
        st.markdown(f"""
            <div style="margin-top: 20px; padding: 16px; background: rgba(255,255,255,0.1); border-radius: 12px; border: 1px solid rgba(255,255,255,0.2);">
                <div style="display: flex; align-items: center; margin-bottom: 12px;">
                    <span class="status-indicator {status_class}"></span>
                    <span style="color: #f8fafc; font-weight: 600; font-size: 1.1rem;">Status: {status_text}</span>
                </div>
                <div style="color: #cbd5e1; font-size: 0.9rem; line-height: 1.8;">
                    <div>Buffer: {collector_stats['buffer_size']} ticks</div>
                    <div>Total: {collector_stats['total_ticks']:,} ticks</div>
                    <div>Threads: {collector_stats['active_threads']}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Analytics settings
        st.markdown("### Analytics Settings")
        timeframe = st.selectbox("Timeframe", ['1s', '5s', '10s', '30s', '1min', '5min'], index=0)
        rolling_window = st.slider("Rolling Window", 5, 100, Config.DEFAULT_ROLLING_WINDOW)
        regression_method = st.radio("Regression", ['ols', 'huber', 'kalman', 'rolling', 'tls'])
        
        st.markdown("---")
        
        # Database info
        st.markdown("### Database")
        
        db_info = get_database_size()
        st.markdown(f"""
            <div style="padding: 12px; background: rgba(255,255,255,0.1); border-radius: 10px; border: 1px solid rgba(255,255,255,0.2); margin-bottom: 12px;">
                <div style="color: #cbd5e1; font-size: 0.85rem; line-height: 1.8;">
                    <div>Records: {db_info['tick_count']:,}</div>
                    <div>Symbols: {db_info['symbol_count']}</div>
                    <div>Size: {db_info['size_mb']:.2f} MB</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Database actions
        if st.button("Clear Database", key="clear_btn"):
            clear_database()
            st.success("Database cleared!")
            st.rerun()
        
        # Export data
        df_export = get_ticks(limit=100000)
        if not df_export.empty:
            csv = df_export.to_csv(index=False)
            st.download_button(
                label="Export CSV",
                data=csv,
                file_name=f"ticks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key="export_btn"
            )
        
        st.markdown("---")
        
        # Alerts
        st.markdown("### Alerts")
        with st.expander("Create Alert"):
            if symbols:
                alert_symbol = st.selectbox("Symbol", symbols, key='alert_sym')
                alert_condition = st.selectbox("Condition", ['above', 'below'])
                alert_value = st.number_input("Threshold", min_value=0.0, value=50000.0)
                
                if st.button("Add Alert"):
                    st.session_state.alerts.append({
                        'symbol': alert_symbol,
                        'condition': alert_condition,
                        'value': alert_value
                    })
                    st.success("Alert added!")
        
        # Z-Score Alerts
        with st.expander("Z-Score Alert"):
            if symbols and len(symbols) >= 2:
                st.caption("Alert when spread z-score crosses threshold")
                zscore_condition = st.selectbox("Z-Score Condition", ['above', 'below'], key='zscore_cond')
                zscore_threshold = st.number_input("Z-Score Threshold", min_value=-5.0, max_value=5.0, value=2.0, step=0.1, key='zscore_th')
                
                if st.button("Add Z-Score Alert", key="add_zscore_alert"):
                    st.session_state.alerts.append({
                        'type': 'zscore',
                        'condition': zscore_condition,
                        'value': zscore_threshold,
                        'symbols': symbols[:2]
                    })
                    st.success("Z-Score alert added!")
            else:
                st.info("Need 2 symbols for z-score alerts")
        
        if st.session_state.alerts:
            st.write(f"**Active Alerts:** {len(st.session_state.alerts)}")
            if st.button("Clear Alerts"):
                st.session_state.alerts = []
                st.rerun()
        
        st.markdown("---")
        
        # OHLC Upload
        st.markdown("### Upload OHLC Data")
        uploaded_file = st.file_uploader("CSV File", type=['csv'])
        if uploaded_file:
            try:
                udf = pd.read_csv(uploaded_file)
                required_cols = ['symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume']
                if all(col in udf.columns for col in required_cols):
                    if save_ohlc_data(udf):
                        st.success(f"Uploaded {len(udf)} rows!")
                else:
                    st.error(f"Required columns: {required_cols}")
            except Exception as e:
                st.error(f"Error: {e}")
    
    # Main content
    df_trades = get_ticks(limit=10000)
    df_ohlc_db = get_ohlc_data(limit=10000)
    
    # Resample tick data to OHLC
    if not df_trades.empty:
        df_resampled = Analytics.resample_ohlcv(df_trades, timeframe)
    else:
        df_resampled = pd.DataFrame()
    
    # Combine with uploaded OHLC data
    if not df_ohlc_db.empty:
        df_ohlc_db['datetime'] = pd.to_datetime(df_ohlc_db['timestamp'], unit='ms')
        if df_resampled.empty:
            df_resampled = df_ohlc_db
        else:
            df_resampled = pd.concat([df_resampled, df_ohlc_db]).drop_duplicates()
    
    # Check for alerts (price and z-score)
    def check_alerts(df, alerts, rolling_window=20):
        triggered = []
        for alert in alerts:
            alert_type = alert.get('type', 'price')
            
            if alert_type == 'zscore':
                # Z-Score alert
                syms = alert.get('symbols', [])
                if len(syms) >= 2:
                    s1, s2 = syms[0], syms[1]
                    p1 = df[df['symbol'] == s1].set_index('datetime')['close'] if 'datetime' in df.columns else pd.Series()
                    p2 = df[df['symbol'] == s2].set_index('datetime')['close'] if 'datetime' in df.columns else pd.Series()
                    
                    if not p1.empty and not p2.empty:
                        common_idx = p1.index.intersection(p2.index)
                        if len(common_idx) > rolling_window:
                            p1 = p1.loc[common_idx]
                            p2 = p2.loc[common_idx]
                            hr, _ = Analytics.calculate_hedge_ratio(p1, p2)
                            spread = Analytics.calculate_spread(p1, p2, hr)
                            zscore = Analytics.calculate_zscore(spread, rolling_window)
                            
                            if not zscore.empty:
                                current_z = zscore.iloc[-1]
                                if alert['condition'] == 'above' and current_z > alert['value']:
                                    triggered.append(f"Z-SCORE ALERT: {s1.upper()}/{s2.upper()} z={current_z:.2f} > {alert['value']:.2f}")
                                elif alert['condition'] == 'below' and current_z < alert['value']:
                                    triggered.append(f"Z-SCORE ALERT: {s1.upper()}/{s2.upper()} z={current_z:.2f} < {alert['value']:.2f}")
            else:
                # Price alert
                symbol = alert.get('symbol', '')
                sdf = df[df['symbol'] == symbol]
                if not sdf.empty:
                    latest = sdf.iloc[-1]['close']
                    if alert['condition'] == 'above' and latest > alert['value']:
                        triggered.append(f"PRICE ALERT: {symbol.upper()} ${latest:.2f} > ${alert['value']:.2f}")
                    elif alert['condition'] == 'below' and latest < alert['value']:
                        triggered.append(f"PRICE ALERT: {symbol.upper()} ${latest:.2f} < ${alert['value']:.2f}")
        return triggered
    
    # Display alerts
    if st.session_state.alerts and not df_resampled.empty:
        triggered = check_alerts(df_resampled, st.session_state.alerts, rolling_window)
        if triggered:
            st.warning("### Alerts Triggered!")
            for t in triggered:
                st.write(t)
    
    # Tabs - Always show, handle empty states within each tab
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "Dashboard", "OHLC Charts", "Pair Analytics", 
        "Backtest", "Statistics", "Data Table", "Portfolio"
    ])
    
    with tab1:
        st.header("Market Overview")
        
        stats_df = get_statistics()
        
        if not stats_df.empty:
            cols = st.columns(4)
            
            total_ticks = stats_df['tick_count'].sum()
            total_symbols = len(stats_df)
            avg_price = stats_df['avg_price'].mean()
            total_volume = stats_df['total_volume'].sum()
            
            with cols[0]:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Total Ticks</div>
                        <div class="metric-value">{total_ticks:,}</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with cols[1]:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Active Symbols</div>
                        <div class="metric-value">{total_symbols}</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with cols[2]:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Avg Price</div>
                        <div class="metric-value">${avg_price:,.2f}</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with cols[3]:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Total Volume</div>
                        <div class="metric-value">{total_volume:,.2f}</div>
                    </div>
                """, unsafe_allow_html=True)
            
            # Price changes
            st.markdown("### Price Changes (1 Hour)")
            
            change_cols = st.columns(len(symbols))
            for idx, symbol in enumerate(symbols):
                with change_cols[idx]:
                    change_data = get_price_change(symbol, minutes=60)
                    change_pct = change_data['change_pct']
                    current_price = change_data['current_price']
                    
                    change_color = "#34d399" if change_pct >= 0 else "#f87171"
                    change_arrow = "+" if change_pct >= 0 else ""
                    
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">{symbol.upper()}</div>
                            <div class="metric-value" style="font-size: 1.8rem;">${current_price:,.2f}</div>
                            <div style="color: {change_color}; font-size: 0.9rem; font-weight: 600; margin-top: 8px;">
                                {change_arrow}{change_pct:.2f}%
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
        else:
            if st.session_state.collecting:
                st.info(f"📊 Collecting data... waiting for first {timeframe} candle")
            else:
                st.info("📊 Click **Start** in the sidebar to begin collecting data")
    
    with tab2:
        st.header("OHLC Candlestick Charts")
        
        if not df_resampled.empty:
            unique_symbols = list(df_resampled['symbol'].unique())
            
            # Get time window based on timeframe
            time_window = Config.TIMEFRAME_WINDOWS.get(timeframe, 60)
            
            # Calculate total available data duration
            min_time = df_resampled['datetime'].min()
            max_time = df_resampled['datetime'].max()
            total_seconds = int((max_time - min_time).total_seconds())
            max_scroll = max(0, total_seconds - time_window)
            
            # Show current time window info
            if time_window < 60:
                window_text = f"{time_window}s"
            elif time_window < 3600:
                window_text = f"{time_window // 60}min"
            else:
                window_text = f"{time_window // 3600}h"
            
            # Status info
            is_live = st.session_state.get('collecting', False)
            status_text = "🔴 LIVE" if is_live else "⏸️ Paused"
            st.caption(f"{status_text} | Window: {window_text} | Total data: {total_seconds}s")
            
            # Time scroll slider (only useful when not collecting or for historical view)
            time_offset = 0
            if max_scroll > 0:
                time_offset = st.slider(
                    "⏪ Scroll back in time (seconds)", 
                    min_value=0, 
                    max_value=max_scroll, 
                    value=0,
                    step=max(1, time_window // 10),
                    key="time_scroll",
                    help="Move slider to view historical data"
                )
            
            if len(unique_symbols) >= 2:
                # Volume toggle buttons
                toggle_col1, toggle_col2 = st.columns(2)
                with toggle_col1:
                    show_vol1 = st.checkbox(f"Show {unique_symbols[0].upper()} Volume", value=True, key="vol_toggle_1")
                with toggle_col2:
                    show_vol2 = st.checkbox(f"Show {unique_symbols[1].upper()} Volume", value=True, key="vol_toggle_2")
                
                # Side-by-side charts
                chart_col1, chart_col2 = st.columns(2)
                
                with chart_col1:
                    fig1 = create_single_ohlc_chart(df_resampled, unique_symbols[0], show_volume=show_vol1, 
                                                    time_window_seconds=time_window, time_offset_seconds=time_offset)
                    st.plotly_chart(fig1, use_container_width=True)
                
                with chart_col2:
                    fig2 = create_single_ohlc_chart(df_resampled, unique_symbols[1], show_volume=show_vol2, 
                                                    time_window_seconds=time_window, time_offset_seconds=time_offset)
                    st.plotly_chart(fig2, use_container_width=True)
                
                # Show any additional symbols below
                if len(unique_symbols) > 2:
                    st.markdown("### Additional Symbols")
                    for i, sym in enumerate(unique_symbols[2:]):
                        show_vol = st.checkbox(f"Show {sym.upper()} Volume", value=True, key=f"vol_toggle_{i+3}")
                        fig = create_single_ohlc_chart(df_resampled, sym, show_volume=show_vol, 
                                                       time_window_seconds=time_window, time_offset_seconds=time_offset)
                        st.plotly_chart(fig, use_container_width=True)
            
            elif len(unique_symbols) == 1:
                show_vol = st.checkbox(f"Show {unique_symbols[0].upper()} Volume", value=True, key="vol_toggle_single")
                fig = create_single_ohlc_chart(df_resampled, unique_symbols[0], show_volume=show_vol, 
                                               time_window_seconds=time_window, time_offset_seconds=time_offset)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No OHLC data available")
    
    with tab3:
        st.header("Pair Trading Analytics")
        
        unique_symbols = df_resampled['symbol'].unique() if not df_resampled.empty else []
        if len(unique_symbols) >= 2:
            col1, col2 = st.columns(2)
            with col1:
                s1 = st.selectbox("Primary Symbol", unique_symbols, key='s1')
            with col2:
                s2 = st.selectbox("Secondary Symbol", [s for s in unique_symbols if s != s1], key='s2')
            
            p1 = df_resampled[df_resampled['symbol'] == s1].set_index('datetime')['close']
            p2 = df_resampled[df_resampled['symbol'] == s2].set_index('datetime')['close']
            
            common_idx = p1.index.intersection(p2.index)
            p1 = p1.loc[common_idx]
            p2 = p2.loc[common_idx]
            
            if len(p1) > rolling_window:
                hr, intercept = Analytics.calculate_hedge_ratio(p1, p2, regression_method, window=rolling_window)
                
                # Handle dynamic hedge ratio display
                if isinstance(hr, pd.Series):
                    display_hr = hr.iloc[-1]
                    display_int = intercept.iloc[-1] if isinstance(intercept, pd.Series) else intercept
                    st.info(f"**Hedge Ratio ({regression_method.upper()}):** {display_hr:.4f} (Dynamic) | **Intercept:** {display_int:.4f}")
                else:
                    st.info(f"**Hedge Ratio ({regression_method.upper()}):** {hr:.4f} | **Intercept:** {intercept:.4f}")
                
                spread = Analytics.calculate_spread(p1, p2, hr)
                zscore = Analytics.calculate_zscore(spread, rolling_window)
                
                fig = create_spread_chart(spread, zscore, s1, s2)
                st.plotly_chart(fig)
                
                # Export Analytics Data
                analytics_df = pd.DataFrame({
                    'timestamp': spread.index,
                    'price1': p1.values,
                    'price2': p2.values,
                    'spread': spread.values,
                    'zscore': zscore.values
                })
                
                csv_analytics = analytics_df.to_csv(index=False)
                st.download_button(
                    label="Download Analytics Data (CSV)",
                    data=csv_analytics,
                    file_name=f"pair_analytics_{s1}_{s2}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key="download_analytics"
                )
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("Run ADF Test"):
                        adf = Analytics.adf_test(spread)
                        if adf:
                            with col2:
                                st.metric("ADF Statistic", f"{adf['statistic']:.4f}")
                            with col3:
                                status = "Stationary" if adf['is_stationary'] else "Non-stationary"
                                st.metric("P-Value", f"{adf['pvalue']:.4f}", delta=status)
                
                st.subheader("Rolling Correlation")
                rcorr = Analytics.rolling_correlation(p1, p2, rolling_window)
                fig_corr = create_rolling_correlation_chart(rcorr, s1, s2, rolling_window)
                st.plotly_chart(fig_corr)
            else:
                st.warning(f"Not enough data points yet. Need {rolling_window}, but only have {len(p1)}. Please wait...")
        else:
            st.info("Add at least 2 symbols for pair analytics")
    
    with tab4:
        st.header("Mean Reversion Backtest")
        
        unique_symbols = df_resampled['symbol'].unique() if not df_resampled.empty else []
        if len(unique_symbols) >= 2:
            col1, col2 = st.columns(2)
            with col1:
                s1 = st.selectbox("Primary Symbol", unique_symbols, key='bt1')
            with col2:
                s2 = st.selectbox("Secondary Symbol", [s for s in unique_symbols if s != s1], key='bt2')
            
            entry_th = st.slider("Entry Threshold (Z-Score)", 1.0, 3.0, 2.0, 0.1)
            exit_th = st.slider("Exit Threshold (Z-Score)", -0.5, 0.5, 0.0, 0.1)
            
            p1 = df_resampled[df_resampled['symbol'] == s1].set_index('datetime')['close']
            p2 = df_resampled[df_resampled['symbol'] == s2].set_index('datetime')['close']
            
            common_idx = p1.index.intersection(p2.index)
            p1 = p1.loc[common_idx]
            p2 = p2.loc[common_idx]
            
            if len(p1) > rolling_window:
                hr, _ = Analytics.calculate_hedge_ratio(p1, p2, regression_method, window=rolling_window)
                spread = Analytics.calculate_spread(p1, p2, hr)
                zscore = Analytics.calculate_zscore(spread, rolling_window)
                
                trades_df, positions = Analytics.backtest_mean_reversion(spread, zscore, entry_th, exit_th)
                
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                
                total_trades = len(trades_df)
                
                if not trades_df.empty and 'pnl' in trades_df.columns:
                    total_pnl = trades_df['pnl'].dropna().sum()
                    completed_trades = trades_df['pnl'].dropna()
                    win_rate = (len(completed_trades[completed_trades > 0]) / len(completed_trades) * 100) if len(completed_trades) > 0 else 0.0
                    avg_pnl = completed_trades.mean() if len(completed_trades) > 0 else 0.0
                else:
                    total_pnl = 0.0
                    win_rate = 0.0
                    avg_pnl = 0.0
                
                with col_m1:
                    st.metric("Total Trades", total_trades)
                with col_m2:
                    st.metric("Total P&L", f"{total_pnl:.4f}")
                with col_m3:
                    st.metric("Win Rate", f"{win_rate:.1f}%")
                with col_m4:
                    st.metric("Avg P&L", f"{avg_pnl:.4f}")
                
                st.subheader("Backtest Visualization")
                fig_bt = create_backtest_chart(trades_df, positions, spread)
                st.plotly_chart(fig_bt)
                
                if not trades_df.empty:
                    st.subheader("Trade Log")
                    st.dataframe(trades_df)
                    
                    csv_trades = trades_df.to_csv(index=False)
                    st.download_button(
                        label="Download Trade Log (CSV)",
                        data=csv_trades,
                        file_name=f"backtest_trades_{s1}_{s2}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        key="download_trades"
                    )
            else:
                st.warning(f"Not enough data points yet. Need {rolling_window}, but only have {len(p1)}. Please wait...")
        else:
            st.info("Select two different symbols to run backtest")
    
    with tab5:
        st.header("Statistical Analysis")
        
        unique_symbols = df_resampled['symbol'].unique() if not df_resampled.empty else []
        
        if len(unique_symbols) >= 2:
            st.subheader("Correlation Matrix")
            fig_heatmap = create_correlation_heatmap(df_resampled, unique_symbols)
            st.plotly_chart(fig_heatmap)
        
        if len(unique_symbols) > 0:
            st.subheader("Time Series Statistics")
            stats_data = []
            for symbol in unique_symbols:
                sdf = df_resampled[df_resampled['symbol'] == symbol]['close']
                if len(sdf) > 0:
                    stats_data.append({
                        'Symbol': symbol.upper(),
                        'Mean': sdf.mean(),
                        'Std': sdf.std(),
                        'Min': sdf.min(),
                        'Max': sdf.max(),
                        'Latest': sdf.iloc[-1],
                        'Change %': ((sdf.iloc[-1] / sdf.iloc[0] - 1) * 100)
                    })
            
            if stats_data:
                stats_table = pd.DataFrame(stats_data)
                st.dataframe(stats_table)
            
            st.subheader("Price Distribution")
            selected_dist_symbol = st.selectbox("Select Symbol", unique_symbols, key='dist_sym')
            if selected_dist_symbol:
                dist_data = df_resampled[df_resampled['symbol'] == selected_dist_symbol]['close']
                fig_dist = create_distribution_chart(dist_data, f"{selected_dist_symbol.upper()} Price Distribution")
                st.plotly_chart(fig_dist)
        else:
            st.info("No data available for statistics")
    
    with tab6:
        st.header("Data Management")
        
        st.subheader("Raw Tick Data")
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            table_symbol = st.selectbox("Filter by Symbol", ["All"] + [s.upper() for s in symbols], key="table_symbol")
        with col2:
            limit = st.number_input("Limit", min_value=10, max_value=10000, value=100, step=10, key="table_limit")
        with col3:
            sort_order = st.selectbox("Sort", ["Newest First", "Oldest First"], key="sort_order")
        
        selected_symbol = None if table_symbol == "All" else table_symbol.lower()
        df = get_ticks(symbol=selected_symbol, limit=limit)
        
        if not df.empty:
            if sort_order == "Oldest First":
                df = df.sort_values('timestamp')
            
            st.dataframe(df, hide_index=True)
            
            st.markdown("### Export Data")
            col_d1, col_d2 = st.columns(2)
            
            with col_d1:
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download Raw Ticks (CSV)",
                    data=csv,
                    file_name=f"ticks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key="download_ticks_tab"
                )
            
            with col_d2:
                if not df_resampled.empty:
                    csv_ohlc = df_resampled.to_csv(index=False)
                    st.download_button(
                        label="Download OHLC Analytics (CSV)",
                        data=csv_ohlc,
                        file_name=f"analytics_ohlc_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        key="download_ohlc_tab"
                    )
            
            st.markdown("### Table Summary")
            cols = st.columns(4)
            
            with cols[0]:
                st.metric("Records", len(df))
            with cols[1]:
                st.metric("Avg Price", f"${df['price'].mean():,.2f}")
            with cols[2]:
                st.metric("Total Volume", f"{df['size'].sum():,.2f}")
            with cols[3]:
                st.metric("Price Range", f"${df['price'].max() - df['price'].min():,.2f}")
        else:
            st.info("No data available")
    
    with tab7:
        st.header("Portfolio & P&L Tracker")
        
        # Get current prices for each symbol
        unique_symbols = df_resampled['symbol'].unique() if not df_resampled.empty else []
        current_prices = {}
        for sym in unique_symbols:
            sdf = df_resampled[df_resampled['symbol'] == sym]
            if not sdf.empty:
                current_prices[sym] = sdf.iloc[-1]['close']
        
        # Open Position Form
        st.subheader("Open New Position")
        
        if len(unique_symbols) > 0:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                pos_symbol = st.selectbox("Symbol", list(unique_symbols), key="pos_symbol")
            with col2:
                pos_side = st.selectbox("Side", ["LONG", "SHORT"], key="pos_side")
            with col3:
                pos_size = st.number_input("Position Size ($)", min_value=100.0, value=1000.0, step=100.0, key="pos_size")
            with col4:
                pos_entry = current_prices.get(pos_symbol, 0.0)
                st.metric("Current Price", f"${pos_entry:,.2f}")
            
            if st.button("Open Position", type="primary", key="open_pos"):
                if pos_entry > 0:
                    new_pos = {
                        'id': len(st.session_state.portfolio) + 1,
                        'symbol': pos_symbol,
                        'side': pos_side,
                        'size': pos_size,
                        'entry_price': pos_entry,
                        'entry_time': datetime.now(),
                        'quantity': pos_size / pos_entry
                    }
                    st.session_state.portfolio.append(new_pos)
                    st.success(f"Opened {pos_side} {pos_symbol.upper()} @ ${pos_entry:,.2f}")
                    st.rerun()
                else:
                    st.error("No price data available for this symbol")
        else:
            st.info("Start data collection to open positions")
        
        st.markdown("---")
        
        # Active Positions with Live P&L
        st.subheader("Active Positions")
        
        if st.session_state.portfolio:
            total_unrealized_pnl = 0
            total_position_value = 0
            
            for i, pos in enumerate(st.session_state.portfolio):
                current_price = current_prices.get(pos['symbol'], pos['entry_price'])
                
                # Calculate P&L
                if pos['side'] == 'LONG':
                    pnl = (current_price - pos['entry_price']) * pos['quantity']
                    pnl_pct = ((current_price / pos['entry_price']) - 1) * 100
                else:  # SHORT
                    pnl = (pos['entry_price'] - current_price) * pos['quantity']
                    pnl_pct = ((pos['entry_price'] / current_price) - 1) * 100
                
                current_value = pos['quantity'] * current_price
                total_unrealized_pnl += pnl
                total_position_value += current_value
                
                pnl_color = "#10b981" if pnl >= 0 else "#ef4444"
                
                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 2, 1])
                
                with col1:
                    st.markdown(f"**{pos['symbol'].upper()}** ({pos['side']})")
                    st.caption(f"Entry: ${pos['entry_price']:,.2f} | Qty: {pos['quantity']:.6f}")
                
                with col2:
                    st.metric("Current", f"${current_price:,.2f}")
                
                with col3:
                    st.metric("Value", f"${current_value:,.2f}")
                
                with col4:
                    st.markdown(f"<div style='color: {pnl_color}; font-size: 1.2rem; font-weight: 700;'>${pnl:+,.2f} ({pnl_pct:+.2f}%)</div>", unsafe_allow_html=True)
                
                with col5:
                    if st.button("Close", key=f"close_{i}"):
                        # Close position
                        closed_pos = pos.copy()
                        closed_pos['exit_price'] = current_price
                        closed_pos['exit_time'] = datetime.now()
                        closed_pos['pnl'] = pnl
                        closed_pos['pnl_pct'] = pnl_pct
                        st.session_state.closed_trades.append(closed_pos)
                        st.session_state.portfolio.pop(i)
                        st.success(f"Closed {pos['symbol'].upper()} for ${pnl:+,.2f}")
                        st.rerun()
                
                st.markdown("---")
            
            # Portfolio Summary
            st.subheader("Portfolio Summary")
            sum_cols = st.columns(4)
            
            with sum_cols[0]:
                st.metric("Open Positions", len(st.session_state.portfolio))
            with sum_cols[1]:
                st.metric("Total Value", f"${total_position_value:,.2f}")
            with sum_cols[2]:
                pnl_delta = "profit" if total_unrealized_pnl >= 0 else "loss"
                st.metric("Unrealized P&L", f"${total_unrealized_pnl:+,.2f}", delta=pnl_delta)
            with sum_cols[3]:
                # Calculate realized P&L from closed trades
                realized_pnl = sum(t.get('pnl', 0) for t in st.session_state.closed_trades)
                st.metric("Realized P&L", f"${realized_pnl:+,.2f}")
            
        else:
            st.info("No open positions. Open a position above to start tracking.")
        
        # Closed Trades History
        if st.session_state.closed_trades:
            st.subheader("Trade History")
            
            trades_data = []
            for t in st.session_state.closed_trades:
                trades_data.append({
                    'Symbol': t['symbol'].upper(),
                    'Side': t['side'],
                    'Entry': f"${t['entry_price']:,.2f}",
                    'Exit': f"${t['exit_price']:,.2f}",
                    'Size': f"${t['size']:,.2f}",
                    'P&L': f"${t['pnl']:+,.2f}",
                    'Return': f"{t['pnl_pct']:+.2f}%"
                })
            
            st.dataframe(pd.DataFrame(trades_data), hide_index=True)
            
            # Trade stats
            total_trades = len(st.session_state.closed_trades)
            winning_trades = len([t for t in st.session_state.closed_trades if t['pnl'] > 0])
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            stat_cols = st.columns(3)
            with stat_cols[0]:
                st.metric("Total Trades", total_trades)
            with stat_cols[1]:
                st.metric("Win Rate", f"{win_rate:.1f}%")
            with stat_cols[2]:
                total_pnl = sum(t['pnl'] for t in st.session_state.closed_trades)
                st.metric("Total Realized", f"${total_pnl:+,.2f}")
            
            if st.button("Clear Trade History", key="clear_history"):
                st.session_state.closed_trades = []
                st.rerun()


# Main app routing
# Main app routing
# Check query params for direct dashboard access
query_params = st.query_params
if query_params.get("page") == "dashboard":
    st.session_state.page = 'dashboard'

if st.session_state.page == 'landing':
    show_landing_page()
else:
    show_dashboard()
