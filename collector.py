"""
WebSocket collector for Binance Futures tick data
Implements DataFeed interface for pluggable data source architecture
"""
import websocket
import json
import threading
import time
from datetime import datetime
from collections import deque
from typing import List, Callable, Optional, Dict
import logging

from config import Config
from data_feed import DataFeed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TickCollector(DataFeed):
    """Collects real-time tick data from Binance Futures WebSocket"""
    
    def __init__(self, buffer_size: int = None):
        self.buffer_size = buffer_size or Config.BUFFER_SIZE
        self.running = False
        self.buffer = deque(maxlen=self.buffer_size)
        self.threads = []
        self.websockets = []
        self.on_tick_callback: Optional[Callable] = None
        self.stats = {
            'total_ticks': 0,
            'ticks_per_symbol': {},
            'errors': 0,
            'reconnections': 0,
            'source': 'binance_ws'
        }
        
    def set_callback(self, callback: Callable):
        """Set callback function to be called on each tick"""
        self.on_tick_callback = callback
    
    def connect(self, symbols: List[str]):
        """Alias for start() to match DataFeed interface"""
        self.start(symbols)
    
    def disconnect(self):
        """Alias for stop() to match DataFeed interface"""
        self.stop()
    
    def is_connected(self) -> bool:
        """Check if collector is running"""
        return self.running
    
    def start(self, symbols: List[str]):
        """Start collecting ticks for given symbols"""
        if self.running:
            logger.warning("Collector already running")
            return
        
        self.running = True
        self.stats['ticks_per_symbol'] = {symbol: 0 for symbol in symbols}
        
        for symbol in symbols:
            thread = threading.Thread(
                target=self._collect,
                args=(symbol,),
                daemon=True,
                name=f"Collector-{symbol}"
            )
            thread.start()
            self.threads.append(thread)
            logger.info(f"Started collector for {symbol}")
    
    def _collect(self, symbol: str):
        """Collect ticks for a single symbol"""
        url = Config.get_ws_url(symbol)
        
        def on_message(ws, message):
            try:
                data = json.loads(message)
                if data.get('e') == 'trade':
                    tick = self._normalize_tick(data)
                    self.buffer.append(tick)
                    
                    # Update statistics
                    self.stats['total_ticks'] += 1
                    self.stats['ticks_per_symbol'][symbol] = \
                        self.stats['ticks_per_symbol'].get(symbol, 0) + 1
                    
                    # Call callback if set
                    if self.on_tick_callback:
                        try:
                            self.on_tick_callback(tick)
                        except Exception as e:
                            logger.error(f"Callback error: {e}")
                            
            except Exception as e:
                logger.error(f"Error processing message for {symbol}: {e}")
                self.stats['errors'] += 1
        
        def on_error(ws, error):
            logger.error(f"WebSocket error for {symbol}: {error}")
            self.stats['errors'] += 1
        
        def on_close(ws, close_status_code, close_msg):
            logger.info(f"WebSocket closed for {symbol}: {close_status_code} - {close_msg}")
        
        def on_open(ws):
            logger.info(f"WebSocket connected for {symbol}")
        
        # Keep reconnecting while running
        while self.running:
            try:
                ws = websocket.WebSocketApp(
                    url,
                    on_message=on_message,
                    on_error=on_error,
                    on_close=on_close,
                    on_open=on_open
                )
                
                self.websockets.append(ws)
                ws.run_forever()
                
                # If we get here, connection was closed
                if self.running:
                    logger.info(f"Reconnecting {symbol} in 5 seconds...")
                    self.stats['reconnections'] += 1
                    time.sleep(5)
                    
            except Exception as e:
                logger.error(f"Connection error for {symbol}: {e}")
                self.stats['errors'] += 1
                if self.running:
                    time.sleep(5)
    
    def _normalize_tick(self, data: dict) -> dict:
        """Normalize Binance tick data to standard format"""
        timestamp = datetime.fromtimestamp(data['T'] / 1000).isoformat()
        return {
            'symbol': data['s'].lower(),
            'timestamp': timestamp,
            'price': float(data['p']),
            'size': float(data['q']),
            'trade_id': data.get('t'),
            'is_buyer_maker': data.get('m', False)
        }
    
    def stop(self):
        """Stop collecting ticks"""
        if not self.running:
            logger.warning("Collector not running")
            return
        
        logger.info("Stopping collector...")
        self.running = False
        
        # Close all WebSocket connections
        for ws in self.websockets:
            try:
                ws.close()
            except:
                pass
        
        self.websockets = []
        self.threads = []
        logger.info("Collector stopped")
    
    def get_buffer_size(self) -> int:
        """Get current buffer size"""
        return len(self.buffer)
    
    def get_buffer_data(self, limit: Optional[int] = None) -> List[dict]:
        """Get data from buffer"""
        if limit:
            return list(self.buffer)[-limit:]
        return list(self.buffer)
    
    def clear_buffer(self):
        """Clear the buffer"""
        self.buffer.clear()
        logger.info("Buffer cleared")
    
    def get_stats(self) -> dict:
        """Get collector statistics"""
        return {
            **self.stats,
            'buffer_size': len(self.buffer),
            'active_threads': len([t for t in self.threads if t.is_alive()]),
            'is_running': self.running
        }
    
    def is_running(self) -> bool:
        """Check if collector is running"""
        return self.running


class BatchTickCollector(TickCollector):
    """Extended collector with batch database insertion"""
    
    def __init__(self, buffer_size: int = 10000, batch_size: int = 100, 
                 batch_interval: int = 5):
        super().__init__(buffer_size)
        self.batch_size = batch_size
        self.batch_interval = batch_interval
        self.batch_buffer = []
        self.batch_thread = None
        
    def start(self, symbols: List[str]):
        """Start collecting with batch processing"""
        super().start(symbols)
        
        # Start batch processor thread
        self.batch_thread = threading.Thread(
            target=self._batch_processor,
            daemon=True,
            name="BatchProcessor"
        )
        self.batch_thread.start()
        logger.info("Batch processor started")
    
    def _batch_processor(self):
        """Process ticks in batches"""
        from database import insert_ticks_batch
        
        while self.running:
            time.sleep(self.batch_interval)
            
            if len(self.batch_buffer) >= self.batch_size:
                # Insert batch
                try:
                    ticks_to_insert = self.batch_buffer[:self.batch_size]
                    insert_ticks_batch(ticks_to_insert)
                    self.batch_buffer = self.batch_buffer[self.batch_size:]
                    logger.info(f"Inserted batch of {len(ticks_to_insert)} ticks")
                except Exception as e:
                    logger.error(f"Batch insert error: {e}")
    
    def set_callback(self, callback: Callable):
        """Override to add batch buffering"""
        def batch_callback(tick):
            self.batch_buffer.append(tick)
            if callback:
                callback(tick)
        
        super().set_callback(batch_callback)
    
    def stop(self):
        """Stop collector and flush remaining batch"""
        super().stop()
        
        # Flush remaining ticks
        if self.batch_buffer:
            try:
                from database import insert_ticks_batch
                insert_ticks_batch(self.batch_buffer)
                logger.info(f"Flushed {len(self.batch_buffer)} remaining ticks")
                self.batch_buffer = []
            except Exception as e:
                logger.error(f"Error flushing batch: {e}")
