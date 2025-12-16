"""
Data Feed Abstract Base Class
Provides interface for pluggable data sources (Binance, CME, CSV, REST API, etc.)
"""

from abc import ABC, abstractmethod
from typing import List, Callable, Optional, Dict
from datetime import datetime


class DataFeed(ABC):
    """Abstract base class for all data feeds"""
    
    @abstractmethod
    def connect(self, symbols: List[str]) -> None:
        """Connect to data source and start receiving data"""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from data source"""
        pass
    
    @abstractmethod
    def set_callback(self, callback: Callable[[dict], None]) -> None:
        """Set callback function to handle incoming ticks"""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if feed is currently connected"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict:
        """Get feed statistics"""
        pass
    
    @staticmethod
    def normalize_tick(raw_data: dict, source: str) -> dict:
        """
        Normalize tick data to standard format
        
        Standard format:
        {
            'symbol': str,
            'timestamp': str (ISO format),
            'price': float,
            'size': float,
            'source': str
        }
        """
        raise NotImplementedError("Subclasses must implement normalize_tick")


class CSVDataFeed(DataFeed):
    """Data feed from CSV file (for backtesting/historical analysis)"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.connected = False
        self.callback: Optional[Callable] = None
        self.stats = {'total_ticks': 0, 'source': 'csv'}
    
    def connect(self, symbols: List[str]) -> None:
        import pandas as pd
        self.connected = True
        
        df = pd.read_csv(self.file_path)
        
        for _, row in df.iterrows():
            if symbols and row.get('symbol', '').lower() not in [s.lower() for s in symbols]:
                continue
            
            tick = self.normalize_tick(row.to_dict(), 'csv')
            self.stats['total_ticks'] += 1
            
            if self.callback:
                self.callback(tick)
        
        self.connected = False
    
    def disconnect(self) -> None:
        self.connected = False
    
    def set_callback(self, callback: Callable[[dict], None]) -> None:
        self.callback = callback
    
    def is_connected(self) -> bool:
        return self.connected
    
    def get_stats(self) -> Dict:
        return self.stats
    
    @staticmethod
    def normalize_tick(raw_data: dict, source: str) -> dict:
        return {
            'symbol': str(raw_data.get('symbol', '')).lower(),
            'timestamp': raw_data.get('timestamp', datetime.now().isoformat()),
            'price': float(raw_data.get('price', 0)),
            'size': float(raw_data.get('size', raw_data.get('volume', 0))),
            'source': source
        }


class RESTDataFeed(DataFeed):
    """Data feed from REST API (polling-based)"""
    
    def __init__(self, base_url: str, poll_interval: float = 1.0):
        self.base_url = base_url
        self.poll_interval = poll_interval
        self.connected = False
        self.callback: Optional[Callable] = None
        self.stats = {'total_ticks': 0, 'source': 'rest', 'polls': 0}
        self._running = False
    
    def connect(self, symbols: List[str]) -> None:
        import threading
        import time
        import requests
        
        self.connected = True
        self._running = True
        
        def poll_loop():
            while self._running:
                for symbol in symbols:
                    try:
                        response = requests.get(f"{self.base_url}/{symbol}")
                        if response.status_code == 200:
                            data = response.json()
                            tick = self.normalize_tick(data, 'rest')
                            tick['symbol'] = symbol
                            self.stats['total_ticks'] += 1
                            
                            if self.callback:
                                self.callback(tick)
                    except Exception as e:
                        self.stats['errors'] = self.stats.get('errors', 0) + 1
                
                self.stats['polls'] += 1
                time.sleep(self.poll_interval)
        
        threading.Thread(target=poll_loop, daemon=True).start()
    
    def disconnect(self) -> None:
        self._running = False
        self.connected = False
    
    def set_callback(self, callback: Callable[[dict], None]) -> None:
        self.callback = callback
    
    def is_connected(self) -> bool:
        return self.connected
    
    def get_stats(self) -> Dict:
        return self.stats
    
    @staticmethod
    def normalize_tick(raw_data: dict, source: str) -> dict:
        return {
            'symbol': str(raw_data.get('symbol', '')).lower(),
            'timestamp': raw_data.get('timestamp', datetime.now().isoformat()),
            'price': float(raw_data.get('price', raw_data.get('last', 0))),
            'size': float(raw_data.get('size', raw_data.get('volume', 0))),
            'source': source
        }
