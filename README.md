# Crypto Analytics Platform

A professional-grade quantitative analytics platform for real-time crypto market data collection, statistical arbitrage analysis, and algorithmic trading backtesting.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## Features

### Real-Time Data Ingestion
- **WebSocket Streaming** - Live tick data from Binance Futures with auto-reconnection
- **Multi-Symbol Support** - Track multiple trading pairs with batch database writes

### OHLC Aggregation
- **On-the-Fly Conversion** - Tick data to candlesticks in real-time
- **Multiple Timeframes** - 1s, 5s, 10s, 30s, 1min, 5min with volume aggregation

### Pair Trading Analytics
- **Hedge Ratio & Spread** - OLS/Huber regression with real-time spread computation
- **Z-Score & Cointegration** - Rolling z-score and ADF stationarity testing

### Visualization Dashboard
- **Interactive Charts** - OHLC candlesticks, spread/z-score plots, correlation heatmaps
- **Dark Theme UI** - Professional aesthetic with Plotly visualizations

### Backtesting Engine
- **Mean-Reversion Strategy** - Z-score based entry/exit with configurable thresholds
- **Trade Log & Metrics** - Detailed P&L tracking with win rate statistics

### Portfolio & P&L Tracker
- **Paper Trading** - Simulate LONG/SHORT positions with real-time P&L
- **Trade History** - Complete log with performance tracking

### Alert System
- **Price & Z-Score Alerts** - Threshold-based notifications for trading signals

---

## Architecture

### System Flowchart

![Architecture Flowchart](Flowchart.png)

### Project Structure

```
crypto-analytics-platform/
├── app.py              # Main Streamlit application
├── config.py           # Centralized configuration
├── database.py         # SQLite data storage layer
├── collector.py        # WebSocket data ingestion
├── data_feed.py        # Abstract data feed interface
├── analytics.py        # Quantitative analytics module
├── visualizations.py   # Chart generation functions
├── requirements.txt    # Python dependencies
└── crypto_ticks.db     # SQLite database (auto-created)
```

### Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Loose Coupling** | Separate modules for ingestion, storage, analytics, visualization |
| **Clean Interfaces** | Abstract `DataFeed` base class for pluggable sources |
| **Extensibility** | Add new analytics/charts without modifying existing code |
| **Configuration** | Centralized `config.py` with environment variable support |

---

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

```bash
# Clone repository
git clone <repository-url>
cd crypto-analytics-platform

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Dependencies

```
streamlit>=1.28.0
streamlit-autorefresh>=1.0.0
pandas>=2.0.0
numpy>=1.24.0
plotly>=5.18.0
websocket-client>=1.6.0
scipy>=1.11.0
statsmodels>=0.14.0
scikit-learn>=1.3.0
```

---

## AI Usage

I also took help of the AI to debug the code and optimize the code.

### Major Prompts Used during Developement

1. *"Help me with chart organization structure on the UI. Currently it is shifting towards right of the page and going blank."*

2. *"Please go through the collectors.py and database.py and check why I have inconsistency on the database and UI dashboard."*

3. *"Replace slow loading components with fast rendering components wherever possible to load the UI well."*

4. *"Why am I getting a z-score error for multiple values? Check visualizations.py and collector.py and don't change the UI analytics."*

5. *"How to remove goliath vs david correlation between bitcoin and ethereum candlestick chart as both are too far apart."*

6. *"Getting these errors in backtesting. It uses mean reversion strategy, please don't change that."*

### LLMs Used

- **Claude Opus 4.5 (Thinking) on Google Antigravity for Backend Debugging and Optimizations.** 
- **SWE-1 on Windsurf for minor UI Adjustments** 
- **Gemini-3 for Planning and Project Understanding.**

---

## Usage

### Starting the Application

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

### Quick Start

1. **Launch Dashboard** - Click the button on the landing page
2. **Configure Symbols** - Enter trading pairs (e.g., `btcusdt,ethusdt`)
3. **Start Collection** - Click "Start" to begin streaming data
4. **Wait for Data** - Allow 1-2 minutes for candles to form
5. **Analyze** - Navigate through tabs to view analytics

### Configuration

Override settings via environment variables:

```bash
set CRYPTO_DB_PATH=my_data.db
set BINANCE_WS_URL=wss://fstream.binance.com/ws
set REFRESH_INTERVAL=5000
set DEFAULT_TIMEFRAME=1min
streamlit run app.py
```

---

## Module Documentation

### `config.py`
Centralized configuration with environment variable support.

```python
from config import Config

Config.DB_PATH           # Database file path
Config.BINANCE_WS_BASE   # WebSocket base URL
Config.BUFFER_SIZE       # Tick buffer size (10000)
Config.BATCH_SIZE        # Database batch size (100)
Config.REFRESH_INTERVAL  # UI refresh rate (3000ms)
```

### `data_feed.py`
Abstract base class for pluggable data sources.

```python
from data_feed import DataFeed, CSVDataFeed, RESTDataFeed

# CSV feed for backtesting
feed = CSVDataFeed("historical_data.csv")
feed.set_callback(handler)
feed.connect(["btcusdt"])

# REST API polling
feed = RESTDataFeed("https://api.example.com", poll_interval=1.0)
```

### `collector.py`
WebSocket collector implementing `DataFeed` interface.

```python
from collector import BatchTickCollector

collector = BatchTickCollector()
collector.set_callback(save_tick)
collector.start(["btcusdt", "ethusdt"])
# ... later
collector.stop()
```

### `analytics.py`
Quantitative analysis functions.

```python
from analytics import Analytics

# Resample ticks to OHLC
ohlc_df = Analytics.resample_ohlcv(tick_df, "1min")

# Calculate hedge ratio
ratio, intercept = Analytics.calculate_hedge_ratio(price1, price2, method="ols")

# Calculate z-score
zscore = Analytics.calculate_zscore(spread, window=20)

# Run ADF test
result = Analytics.adf_test(spread)

# Backtest strategy
trades_df, positions = Analytics.backtest_mean_reversion(spread, zscore, entry_th=2.0)
```

### `visualizations.py`
Chart generation with dark theme.

```python
from visualizations import (
    create_ohlc_chart,
    create_spread_chart,
    create_correlation_heatmap,
    create_backtest_chart
)

fig = create_ohlc_chart(ohlc_df, symbols=["btcusdt", "ethusdt"])
fig = create_spread_chart(spread, zscore, entry_th=2.0, exit_th=0.0)
```

---

## Extending the Platform

### Adding a New Data Source

```python
from data_feed import DataFeed

class CMEDataFeed(DataFeed):
    def connect(self, symbols):
        # Connect to CME WebSocket
        pass
    
    def disconnect(self):
        pass
    
    def set_callback(self, callback):
        self.callback = callback
    
    def is_connected(self):
        return self._connected
    
    def get_stats(self):
        return {"source": "cme", "ticks": self._count}
```

### Adding New Analytics

```python
# Add to analytics.py
class Analytics:
    @staticmethod
    def calculate_bollinger_bands(prices, window=20, num_std=2):
        rolling_mean = prices.rolling(window).mean()
        rolling_std = prices.rolling(window).std()
        upper_band = rolling_mean + (rolling_std * num_std)
        lower_band = rolling_mean - (rolling_std * num_std)
        return upper_band, rolling_mean, lower_band
```

---

## Database Schema

### `ticks` Table
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| symbol | TEXT | Trading pair |
| timestamp | TEXT | ISO timestamp |
| price | REAL | Trade price |
| size | REAL | Trade volume |
| created_at | TIMESTAMP | Insert time |

### `ohlc_data` Table
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| symbol | TEXT | Trading pair |
| timestamp | INTEGER | Epoch ms |
| open, high, low, close | REAL | OHLC prices |
| volume | REAL | Candle volume |
| timeframe | TEXT | e.g., "1min" |

---

## Performance Considerations

- **Indexed Queries** - Symbol and timestamp indexes for fast lookups
- **Batch Inserts** - Reduces database write overhead
- **Buffer Management** - Configurable in-memory buffer size
- **Lazy Loading** - Charts render only when tab is active

