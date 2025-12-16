# Crypto Analytics Platform

A professional-grade quantitative analytics platform for real-time crypto market data collection, statistical arbitrage analysis, and algorithmic trading backtesting.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## Features

### Real-Time Data Ingestion
- **WebSocket Streaming** - Live tick data from Binance Futures
- **Multi-Symbol Support** - Track multiple trading pairs simultaneously
- **Auto-Reconnection** - Handles network interruptions gracefully
- **Batch Processing** - Efficient database writes with configurable batch sizes

### OHLC Aggregation
- **On-the-Fly Conversion** - Tick data to candlesticks in real-time
- **Multiple Timeframes** - 1s, 5s, 10s, 30s, 1min, 5min
- **Volume Aggregation** - Accurate volume tracking per candle

### Pair Trading Analytics
- **Hedge Ratio Calculation** - OLS and Huber regression methods
- **Spread Analysis** - Real-time spread computation
- **Z-Score Calculation** - Rolling z-score with configurable window
- **Correlation Analysis** - Rolling and static correlation matrices
- **Cointegration Testing** - Augmented Dickey-Fuller (ADF) test

### Visualization Dashboard
- **OHLC Candlestick Charts** - Dual Y-axis for comparing assets
- **Spread & Z-Score Plots** - Interactive Plotly charts
- **Correlation Heatmaps** - Visual correlation matrices
- **Distribution Charts** - Price and return distributions
- **Dark Theme UI** - Professional aesthetic with glassmorphism effects

### Backtesting Engine
- **Mean-Reversion Strategy** - Z-score based entry/exit signals
- **Configurable Thresholds** - Adjustable entry and exit levels
- **Trade Log** - Detailed entry/exit times with P&L
- **Performance Metrics** - Win rate, total P&L visualization

### Portfolio & P&L Tracker
- **Paper Trading** - Simulate LONG/SHORT positions
- **Real-Time P&L** - Live unrealized profit/loss updates
- **Trade History** - Complete log of closed trades
- **Win Rate Statistics** - Performance tracking

### Alert System
- **Price Alerts** - Threshold-based notifications
- **Z-Score Alerts** - Pair trading signal alerts
- **Real-Time Monitoring** - Continuous alert checking

---

## Architecture

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

---

## License

MIT License - See LICENSE file for details.

---

## Author

Developed as a Quantitative Developer Assignment demonstrating:
- Real-time data streaming
- Statistical arbitrage analytics
- Modular, scalable architecture
