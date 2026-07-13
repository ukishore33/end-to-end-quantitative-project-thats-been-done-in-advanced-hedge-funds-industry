"""Market data loading from multiple sources"""

import pandas as pd
import numpy as np
import yfinance as yf
from typing import List, Union, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MarketDataLoader:
    """Load market data from multiple sources (Yahoo Finance, CSV, etc.)"""
    
    @staticmethod
    def load_from_yahoo(
        symbols: Union[str, List[str]],
        start: str,
        end: str,
        freq: str = 'daily',
        progress: bool = False
    ) -> pd.DataFrame:
        """
        Load price data from Yahoo Finance
        
        Args:
            symbols: Single ticker or list of tickers (e.g., 'AAPL' or ['AAPL', 'MSFT'])
            start: Start date in format 'YYYY-MM-DD'
            end: End date in format 'YYYY-MM-DD'
            freq: Frequency - 'daily', 'weekly', 'monthly'
            progress: Show download progress
        
        Returns:
            pd.DataFrame: Adjusted close prices with symbols as columns
        
        Raises:
            ValueError: If invalid parameters provided
            ConnectionError: If unable to connect to Yahoo Finance
        
        Example:
            >>> data = MarketDataLoader.load_from_yahoo(['AAPL', 'MSFT'], '2023-01-01', '2023-12-31')
            >>> data.shape
            (252, 2)
        """
        # Convert single symbol to list
        if isinstance(symbols, str):
            symbols = [symbols]
        
        try:
            # Validate dates
            start_date = pd.to_datetime(start)
            end_date = pd.to_datetime(end)
            
            if start_date >= end_date:
                raise ValueError(f"Start date {start} must be before end date {end}")
            
            logger.info(f"Downloading data for {symbols} from {start} to {end}")
            
            # Download data from Yahoo Finance
            data = yf.download(
                symbols,
                start=start,
                end=end,
                progress=progress,
                interval='1d' if freq == 'daily' else '1wk' if freq == 'weekly' else '1mo'
            )
            
            # Handle single symbol case - yfinance returns Series instead of DataFrame
            if len(symbols) == 1:
                data = pd.DataFrame({symbols[0]: data['Adj Close']})
            else:
                # Extract adjusted close prices
                data = data['Adj Close']
            
            # Remove any NaN rows
            data = data.dropna()
            
            logger.info(f"Downloaded {len(data)} rows of data")
            
            return data
        
        except Exception as e:
            logger.error(f"Error downloading data: {str(e)}")
            raise ConnectionError(f"Failed to download data from Yahoo Finance: {str(e)}")
    
    @staticmethod
    def load_from_csv(filepath: str) -> pd.DataFrame:
        """
        Load market data from CSV file
        
        Args:
            filepath: Path to CSV file (must have Date index and price columns)
        
        Returns:
            pd.DataFrame: Price data
        
        Example:
            >>> data = MarketDataLoader.load_from_csv('data/raw/prices.csv')
        """
        try:
            logger.info(f"Loading data from CSV: {filepath}")
            
            data = pd.read_csv(filepath, index_col=0, parse_dates=True)
            
            logger.info(f"Loaded {len(data)} rows from CSV")
            
            return data
        
        except FileNotFoundError:
            logger.error(f"File not found: {filepath}")
            raise FileNotFoundError(f"CSV file not found: {filepath}")
        except Exception as e:
            logger.error(f"Error reading CSV: {str(e)}")
            raise
    
    @classmethod
    def load(
        cls,
        symbols: Union[str, List[str]],
        start: str,
        end: str,
        source: str = 'yahoo',
        freq: str = 'daily'
    ) -> pd.DataFrame:
        """
        Unified interface for loading market data
        
        Args:
            symbols: Stock ticker(s)
            start: Start date 'YYYY-MM-DD'
            end: End date 'YYYY-MM-DD'
            source: Data source - 'yahoo' or 'csv'
            freq: Frequency - 'daily', 'weekly', 'monthly'
        
        Returns:
            pd.DataFrame: Market data with dates as index
        
        Raises:
            ValueError: If unsupported source specified
        
        Example:
            >>> # Load multiple stocks
            >>> data = MarketDataLoader.load(
            ...     ['AAPL', 'MSFT', 'GOOGL'],
            ...     '2023-01-01',
            ...     '2023-12-31',
            ...     source='yahoo'
            ... )
            >>> data.shape
            (252, 3)
        """
        if source == 'yahoo':
            return cls.load_from_yahoo(symbols, start, end, freq)
        elif source == 'csv':
            if isinstance(symbols, list):
                raise ValueError("CSV source requires single filepath as 'symbols'")
            return cls.load_from_csv(symbols)
        else:
            raise ValueError(f"Unknown data source: {source}. Use 'yahoo' or 'csv'")
    
    @staticmethod
    def validate_data(data: pd.DataFrame) -> bool:
        """
        Validate market data quality
        
        Args:
            data: DataFrame with price data
        
        Returns:
            bool: True if data is valid
        
        Raises:
            ValueError: If data quality issues found
        """
        if data.empty:
            raise ValueError("Data is empty")
        
        if not isinstance(data.index, pd.DatetimeIndex):
            raise ValueError("Data index must be datetime")
        
        # Check for NaN values
        if data.isnull().sum().sum() > 0:
            logger.warning(f"Found {data.isnull().sum().sum()} NaN values in data")
        
        # Check for negative prices
        if (data < 0).any().any():
            raise ValueError("Found negative prices in data")
        
        return True


if __name__ == "__main__":
    # Example usage
    print("Testing MarketDataLoader...")
    
    # Load single stock
    aapl = MarketDataLoader.load('AAPL', '2023-01-01', '2023-12-31')
    print(f"AAPL shape: {aapl.shape}")
    print(f"AAPL head:\n{aapl.head()}")
    
    # Load multiple stocks
    data = MarketDataLoader.load(
        ['AAPL', 'MSFT', 'GOOGL'],
        '2023-01-01',
        '2023-12-31'
    )
    print(f"\nMultiple stocks shape: {data.shape}")
    print(f"Multiple stocks head:\n{data.head()}")
    
    # Save for reference
    data.to_csv('data/raw/sample_data.csv')
    print("\nData saved to data/raw/sample_data.csv")
