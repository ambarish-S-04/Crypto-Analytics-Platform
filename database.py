"""
Database utilities for crypto tick data storage and retrieval
"""
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict

from config import Config

DB_PATH = Config.DB_PATH

def init_db():
    """Initialize SQLite database with optimized schema"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Main ticks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ticks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            price REAL NOT NULL,
            size REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Indexes for performance
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_symbol_timestamp 
        ON ticks(symbol, timestamp)
    """)
    
    # OHLC data table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ohlc_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            open REAL, high REAL, low REAL, close REAL, volume REAL,
            timeframe TEXT DEFAULT '1min',
            source TEXT DEFAULT 'live'
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_ohlc_symbol_timestamp 
        ON ohlc_data(symbol, timestamp)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_created_at 
        ON ticks(created_at)
    """)
    
    # Aggregated statistics table (for faster queries)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tick_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            interval_start TEXT NOT NULL,
            interval_end TEXT NOT NULL,
            tick_count INTEGER,
            min_price REAL,
            max_price REAL,
            avg_price REAL,
            total_volume REAL,
            price_change REAL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, interval_start)
        )
    """)
    
    conn.commit()
    conn.close()

def insert_tick(symbol: str, timestamp: str, price: float, size: float):
    """Insert a single tick into the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO ticks (symbol, timestamp, price, size)
        VALUES (?, ?, ?, ?)
    """, (symbol, timestamp, price, size))
    conn.commit()
    conn.close()

def insert_ticks_batch(ticks: List[Dict]):
    """Insert multiple ticks in a batch for better performance"""
    if not ticks:
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    data = [(tick['symbol'], tick['timestamp'], tick['price'], tick['size']) 
            for tick in ticks]
    
    cursor.executemany("""
        INSERT INTO ticks (symbol, timestamp, price, size)
        VALUES (?, ?, ?, ?)
    """, data)
    
    conn.commit()
    conn.close()

def get_ticks(symbol: Optional[str] = None, limit: int = 1000, 
              start_time: Optional[str] = None, end_time: Optional[str] = None) -> pd.DataFrame:
    """Retrieve ticks from database with optional filters"""
    conn = sqlite3.connect(DB_PATH)
    
    query = """
        SELECT symbol, timestamp, price, size, created_at
        FROM ticks
        WHERE 1=1
    """
    params = []
    
    if symbol:
        query += " AND symbol = ?"
        params.append(symbol)
    
    if start_time:
        query += " AND timestamp >= ?"
        params.append(start_time)
    
    if end_time:
        query += " AND timestamp <= ?"
        params.append(end_time)
    
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def get_statistics(symbol: Optional[str] = None) -> pd.DataFrame:
    """Get comprehensive statistics from database"""
    conn = sqlite3.connect(DB_PATH)
    
    query = """
        SELECT 
            symbol,
            COUNT(*) as tick_count,
            MIN(price) as min_price,
            MAX(price) as max_price,
            AVG(price) as avg_price,
            SUM(size) as total_volume,
            MIN(timestamp) as first_tick,
            MAX(timestamp) as last_tick,
            (MAX(price) - MIN(price)) / MIN(price) * 100 as price_range_pct
        FROM ticks
    """
    
    if symbol:
        query += " WHERE symbol = ?"
        params = [symbol]
    else:
        params = []
    
    query += " GROUP BY symbol"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def get_recent_price(symbol: str) -> Optional[float]:
    """Get the most recent price for a symbol"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT price FROM ticks
        WHERE symbol = ?
        ORDER BY timestamp DESC
        LIMIT 1
    """, (symbol,))
    
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else None

def get_price_change(symbol: str, minutes: int = 60) -> Dict:
    """Calculate price change over specified time period"""
    conn = sqlite3.connect(DB_PATH)
    
    # Get current price
    current_query = """
        SELECT price, timestamp FROM ticks
        WHERE symbol = ?
        ORDER BY timestamp DESC
        LIMIT 1
    """
    current_df = pd.read_sql_query(current_query, conn, params=[symbol])
    
    if current_df.empty:
        conn.close()
        return {'change': 0, 'change_pct': 0, 'current_price': 0, 'previous_price': 0}
    
    current_price = current_df.iloc[0]['price']
    current_time = pd.to_datetime(current_df.iloc[0]['timestamp'])
    
    # Get price from N minutes ago
    past_time = (current_time - timedelta(minutes=minutes)).isoformat()
    
    past_query = """
        SELECT price FROM ticks
        WHERE symbol = ? AND timestamp >= ?
        ORDER BY timestamp ASC
        LIMIT 1
    """
    past_df = pd.read_sql_query(past_query, conn, params=[symbol, past_time])
    
    conn.close()
    
    if past_df.empty:
        return {'change': 0, 'change_pct': 0, 'current_price': current_price, 'previous_price': current_price}
    
    previous_price = past_df.iloc[0]['price']
    change = current_price - previous_price
    change_pct = (change / previous_price * 100) if previous_price != 0 else 0
    
    return {
        'change': change,
        'change_pct': change_pct,
        'current_price': current_price,
        'previous_price': previous_price
    }

def get_ohlc_data(symbol: str, interval_minutes: int = 5, limit: int = 100) -> pd.DataFrame:
    """Generate OHLC (candlestick) data from tick data"""
    conn = sqlite3.connect(DB_PATH)
    
    query = """
        SELECT 
            datetime(timestamp, '-' || (strftime('%M', timestamp) % ?) || ' minutes') as interval_start,
            MIN(price) as low,
            MAX(price) as high,
            SUM(size) as volume
        FROM ticks
        WHERE symbol = ?
        GROUP BY interval_start
        ORDER BY interval_start DESC
        LIMIT ?
    """
    
    df = pd.read_sql_query(query, conn, params=[interval_minutes, symbol, limit])
    
    # Get open and close prices for each interval
    if not df.empty:
        for idx, row in df.iterrows():
            interval_start = row['interval_start']
            
            # Get first price (open)
            open_query = """
                SELECT price FROM ticks
                WHERE symbol = ? AND timestamp >= ?
                ORDER BY timestamp ASC
                LIMIT 1
            """
            open_result = pd.read_sql_query(open_query, conn, params=[symbol, interval_start])
            df.at[idx, 'open'] = open_result.iloc[0]['price'] if not open_result.empty else row['low']
            
            # Get last price (close)
            close_query = """
                SELECT price FROM ticks
                WHERE symbol = ? AND timestamp >= ?
                ORDER BY timestamp DESC
                LIMIT 1
            """
            close_result = pd.read_sql_query(close_query, conn, params=[symbol, interval_start])
            df.at[idx, 'close'] = close_result.iloc[0]['price'] if not close_result.empty else row['high']
    
    conn.close()
    return df

def get_volume_profile(symbol: str, price_bins: int = 20) -> pd.DataFrame:
    """Calculate volume profile (volume at price levels)"""
    conn = sqlite3.connect(DB_PATH)
    
    # Get price range
    range_query = """
        SELECT MIN(price) as min_price, MAX(price) as max_price
        FROM ticks
        WHERE symbol = ?
    """
    range_df = pd.read_sql_query(range_query, conn, params=[symbol])
    
    if range_df.empty:
        conn.close()
        return pd.DataFrame()
    
    min_price = range_df.iloc[0]['min_price']
    max_price = range_df.iloc[0]['max_price']
    bin_size = (max_price - min_price) / price_bins
    
    # Get all ticks
    ticks_df = pd.read_sql_query("""
        SELECT price, size FROM ticks
        WHERE symbol = ?
    """, conn, params=[symbol])
    
    conn.close()
    
    # Create price bins
    ticks_df['price_bin'] = ((ticks_df['price'] - min_price) / bin_size).astype(int)
    ticks_df['price_bin'] = ticks_df['price_bin'].clip(0, price_bins - 1)
    
    # Aggregate volume by price bin
    volume_profile = ticks_df.groupby('price_bin').agg({
        'size': 'sum',
        'price': 'mean'
    }).reset_index()
    
    volume_profile.columns = ['bin', 'volume', 'price_level']
    
    return volume_profile.sort_values('price_level')

def clear_database():
    """Clear all ticks from database and shrink file size"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ticks")
    cursor.execute("DELETE FROM tick_stats")
    cursor.execute("DELETE FROM ohlc_data")
    conn.commit()
    # VACUUM to actually shrink the database file size
    cursor.execute("VACUUM")
    conn.close()

def get_database_size() -> Dict:
    """Get database size information"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get tick count
    cursor.execute("SELECT COUNT(*) FROM ticks")
    tick_count = cursor.fetchone()[0]
    
    # Get unique symbols
    cursor.execute("SELECT COUNT(DISTINCT symbol) FROM ticks")
    symbol_count = cursor.fetchone()[0]
    
    # Get database file size
    cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
    db_size = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'tick_count': tick_count,
        'symbol_count': symbol_count,
        'size_bytes': db_size,
        'size_mb': db_size / (1024 * 1024)
    }

def save_ohlc_data(df: pd.DataFrame) -> bool:
    """Save OHLC data to database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        for _, row in df.iterrows():
            conn.execute(
                '''INSERT INTO ohlc_data (symbol, timestamp, open, high, low, close, volume, source) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (row['symbol'], row['timestamp'], row['open'], row['high'], 
                 row['low'], row['close'], row['volume'], row.get('source', 'upload'))
            )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving OHLC data: {e}")
        return False

def get_ohlc_data(symbol: Optional[str] = None, limit: int = 10000) -> pd.DataFrame:
    """Get OHLC data from database"""
    conn = sqlite3.connect(DB_PATH)
    
    if symbol:
        query = "SELECT * FROM ohlc_data WHERE symbol = ? ORDER BY timestamp DESC LIMIT ?"
        params = [symbol, limit]
    else:
        query = "SELECT * FROM ohlc_data ORDER BY timestamp DESC LIMIT ?"
        params = [limit]
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def cleanup_old_data(days: int = 7):
    """Remove data older than specified days"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
    
    cursor.execute("""
        DELETE FROM ticks
        WHERE timestamp < ?
    """, (cutoff_date,))
    
    cursor.execute("""
        DELETE FROM ohlc_data
        WHERE timestamp < ?
    """, (int((datetime.now() - timedelta(days=days)).timestamp() * 1000),))
    
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    
    return deleted_count
