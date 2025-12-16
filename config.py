"""
Configuration module for the Crypto Analytics Platform
Centralizes all settings for easy modification and environment-based configuration
"""

import os


class Config:
    """Centralized configuration settings"""
    
    # Database settings
    DB_PATH = os.getenv("CRYPTO_DB_PATH", "crypto_ticks.db")
    
    # WebSocket settings
    BINANCE_WS_BASE = os.getenv("BINANCE_WS_URL", "wss://fstream.binance.com/ws")
    
    # Data collection settings
    BUFFER_SIZE = int(os.getenv("BUFFER_SIZE", "10000"))
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))
    BATCH_INTERVAL = int(os.getenv("BATCH_INTERVAL", "5"))
    
    # Auto-refresh interval (milliseconds)
    REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL", "3000"))
    
    # Analytics defaults
    DEFAULT_TIMEFRAME = os.getenv("DEFAULT_TIMEFRAME", "1s")
    DEFAULT_ROLLING_WINDOW = int(os.getenv("DEFAULT_ROLLING_WINDOW", "20"))
    
    # Cleanup settings
    DATA_RETENTION_HOURS = int(os.getenv("DATA_RETENTION_HOURS", "24"))
    
    # UI settings
    PAGE_TITLE = "Crypto Analytics Platform"
    DEFAULT_SYMBOLS = ["btcusdt", "ethusdt"]
    
    @classmethod
    def get_ws_url(cls, symbol: str) -> str:
        """Get WebSocket URL for a symbol"""
        return f"{cls.BINANCE_WS_BASE}/{symbol.lower()}@trade"
    
    @classmethod
    def to_dict(cls) -> dict:
        """Export all config as dictionary"""
        return {
            "db_path": cls.DB_PATH,
            "ws_base": cls.BINANCE_WS_BASE,
            "buffer_size": cls.BUFFER_SIZE,
            "batch_size": cls.BATCH_SIZE,
            "batch_interval": cls.BATCH_INTERVAL,
            "refresh_interval": cls.REFRESH_INTERVAL,
            "default_timeframe": cls.DEFAULT_TIMEFRAME,
            "rolling_window": cls.DEFAULT_ROLLING_WINDOW,
            "retention_hours": cls.DATA_RETENTION_HOURS,
        }
