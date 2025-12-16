"""
Advanced Analytics Module
Quantitative analysis functions for trading strategies
"""

import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.tsa.stattools import adfuller
from sklearn.linear_model import LinearRegression, HuberRegressor
import warnings
warnings.filterwarnings('ignore')


class Analytics:
    """Statistical and quantitative analytics for trading"""
    
    @staticmethod
    def resample_ohlcv(df: pd.DataFrame, timeframe: str = '1min') -> pd.DataFrame:
        """
        Resample tick data to OHLCV candles
        
        Args:
            df: DataFrame with columns ['symbol', 'timestamp', 'price', 'size']
            timeframe: Resampling period (e.g., '1min', '5min', '1H')
        
        Returns:
            DataFrame with OHLCV data
        """
        if df.empty:
            return pd.DataFrame()
        
        try:
            df = df.copy()
            # Filter out invalid prices
            df = df[df['price'] > 0]
            if df.empty:
                return pd.DataFrame()
            
            # Convert timestamp to datetime - handle both ISO strings and epoch ms
            if df['timestamp'].dtype == 'object':  # String timestamps (ISO format)
                # Use format='ISO8601' to handle variations in ISO format
                df['datetime'] = pd.to_datetime(df['timestamp'], format='ISO8601')
            else:  # Numeric timestamps (epoch ms)
                df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            df = df.set_index('datetime')
            
            ohlc_list = []
            for symbol in df['symbol'].unique():
                sdf = df[df['symbol'] == symbol]
                if sdf.empty:
                    continue
                
                # Resample price to OHLC
                price = sdf['price'].resample(timeframe).ohlc()
                if price.empty:
                    continue
                
                # Ensure low is valid
                price['low'] = price['low'].where(price['low'] > 0)
                
                # Resample volume
                volume = sdf['size'].resample(timeframe).sum().rename('volume')
                
                # Combine
                result = price.join(volume).dropna()
                if result.empty:
                    continue
                
                result['symbol'] = symbol
                ohlc_list.append(result)
            
            if ohlc_list:
                combined = pd.concat(ohlc_list).reset_index()
                combined.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume', 'symbol']
                return combined
            
            return pd.DataFrame()
        
        except Exception as e:
            print(f"Error resampling OHLCV: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def calculate_hedge_ratio(price1: pd.Series, price2: pd.Series, 
                             method: str = 'ols') -> tuple[float, float]:
        """
        Calculate hedge ratio between two price series
        
        Args:
            price1: First price series
            price2: Second price series
            method: 'ols' or 'huber' regression
        
        Returns:
            (hedge_ratio, intercept)
        """
        if len(price1) < 2 or len(price2) < 2:
            return 1.0, 0.0
        
        try:
            X = price1.values.reshape(-1, 1)
            y = price2.values
            
            model = HuberRegressor() if method == 'huber' else LinearRegression()
            model.fit(X, y)
            
            return float(model.coef_[0]), float(model.intercept_)
        
        except Exception as e:
            print(f"Error calculating hedge ratio: {e}")
            return 1.0, 0.0
    
    @staticmethod
    def calculate_spread(price1: pd.Series, price2: pd.Series, 
                        hedge_ratio: float = 1.0) -> pd.Series:
        """
        Calculate spread between two price series
        
        Args:
            price1: First price series
            price2: Second price series
            hedge_ratio: Hedge ratio to apply
        
        Returns:
            Spread series
        """
        return price1 - hedge_ratio * price2
    
    @staticmethod
    def calculate_zscore(series: pd.Series, window: int = 20) -> pd.Series:
        """
        Calculate rolling z-score
        
        Args:
            series: Price or spread series
            window: Rolling window size
        
        Returns:
            Z-score series
        """
        if len(series) < window:
            return pd.Series(0, index=series.index)
        
        try:
            rolling_mean = series.rolling(window=window).mean()
            rolling_std = series.rolling(window=window).std()
            
            # Avoid division by zero
            rolling_std = rolling_std.replace(0, np.nan)
            
            zscore = (series - rolling_mean) / rolling_std
            return zscore.fillna(0)
        
        except Exception as e:
            print(f"Error calculating z-score: {e}")
            return pd.Series(0, index=series.index)
    
    @staticmethod
    def adf_test(series: pd.Series) -> dict:
        """
        Augmented Dickey-Fuller test for stationarity
        
        Args:
            series: Time series to test
        
        Returns:
            Dictionary with test results
        """
        try:
            series_clean = series.dropna()
            if len(series_clean) < 10:
                return None
            
            result = adfuller(series_clean, maxlag=min(10, len(series_clean)//5))
            
            return {
                'statistic': float(result[0]),
                'pvalue': float(result[1]),
                'critical_values': {k: float(v) for k, v in result[4].items()},
                'is_stationary': result[1] < 0.05
            }
        
        except Exception as e:
            print(f"Error in ADF test: {e}")
            return None
    
    @staticmethod
    def rolling_correlation(s1: pd.Series, s2: pd.Series, 
                           window: int = 20) -> pd.Series:
        """
        Calculate rolling correlation between two series
        
        Args:
            s1: First series
            s2: Second series
            window: Rolling window size
        
        Returns:
            Rolling correlation series
        """
        try:
            return s1.rolling(window=window).corr(s2)
        except Exception as e:
            print(f"Error calculating rolling correlation: {e}")
            return pd.Series(0, index=s1.index)
    
    @staticmethod
    def backtest_mean_reversion(spread: pd.Series, zscore: pd.Series,
                                entry_th: float = 2.0, 
                                exit_th: float = 0.0) -> tuple[pd.DataFrame, pd.Series]:
        """
        Backtest mean reversion strategy
        
        Args:
            spread: Spread series
            zscore: Z-score series
            entry_th: Entry threshold (absolute z-score)
            exit_th: Exit threshold (z-score)
        
        Returns:
            (trades_df, positions_series)
        """
        try:
            positions = pd.Series(0, index=spread.index)
            trades = []
            pos = 0
            entry_price = 0
            
            for i in range(1, len(zscore)):
                z = zscore.iloc[i]
                
                # Entry logic
                if pos == 0:
                    if z > entry_th:  # Short when z-score is high
                        pos = -1
                        entry_price = spread.iloc[i]
                        trades.append({
                            'entry_time': spread.index[i],
                            'entry_price': entry_price,
                            'entry_zscore': z,
                            'side': 'short'
                        })
                    elif z < -entry_th:  # Long when z-score is low
                        pos = 1
                        entry_price = spread.iloc[i]
                        trades.append({
                            'entry_time': spread.index[i],
                            'entry_price': entry_price,
                            'entry_zscore': z,
                            'side': 'long'
                        })
                
                # Exit logic
                elif pos != 0:
                    if (pos == -1 and z < exit_th) or (pos == 1 and z > exit_th):
                        trades[-1]['exit_time'] = spread.index[i]
                        trades[-1]['exit_price'] = spread.iloc[i]
                        trades[-1]['exit_zscore'] = z
                        trades[-1]['pnl'] = pos * (entry_price - spread.iloc[i])
                        pos = 0
                
                positions.iloc[i] = pos
            
            return pd.DataFrame(trades), positions
        
        except Exception as e:
            print(f"Error in backtest: {e}")
            return pd.DataFrame(), pd.Series(0, index=spread.index)
    
    @staticmethod
    def calculate_returns(prices: pd.Series) -> pd.Series:
        """Calculate percentage returns"""
        return prices.pct_change().fillna(0)
    
    @staticmethod
    def calculate_volatility(returns: pd.Series, window: int = 20) -> pd.Series:
        """Calculate rolling volatility"""
        return returns.rolling(window=window).std() * np.sqrt(252)  # Annualized
    
    @staticmethod
    def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
        """Calculate Sharpe ratio"""
        if len(returns) < 2:
            return 0.0
        
        excess_returns = returns - risk_free_rate / 252  # Daily risk-free rate
        if excess_returns.std() == 0:
            return 0.0
        
        return np.sqrt(252) * excess_returns.mean() / excess_returns.std()
