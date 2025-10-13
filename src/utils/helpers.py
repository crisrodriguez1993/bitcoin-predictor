"""
Data Utilities for Bitcoin Predictor System
==========================================

Master's Thesis - Artificial Intelligence Program
Universidad San Francisco de Quito (USFQ)
Author: Cristian Rodríguez
Year: 2025

This module provides utility functions for data processing, validation,
and common operations used across the Bitcoin prediction system.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import logging
from typing import Dict, List, Optional, Tuple, Union
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def ensure_timezone_aware(df: pd.DataFrame, timestamp_col: str = 'timestamp') -> pd.DataFrame:
    """
    Ensure timestamp column is timezone-aware (UTC).
    
    Args:
        df: DataFrame with timestamp column
        timestamp_col: Name of the timestamp column
        
    Returns:
        DataFrame with timezone-aware timestamps
    """
    if timestamp_col not in df.columns:
        return df
    
    df = df.copy()
    
    if df[timestamp_col].dt.tz is None:
        df[timestamp_col] = df[timestamp_col].dt.tz_localize('UTC')
    else:
        df[timestamp_col] = df[timestamp_col].dt.tz_convert('UTC')
    
    return df


def resample_ohlcv(df: pd.DataFrame, 
                   freq: str = '1H', 
                   timestamp_col: str = 'timestamp') -> pd.DataFrame:
    """
    Resample OHLCV data to different time frequencies.
    
    Args:
        df: DataFrame with OHLCV data
        freq: Resampling frequency (e.g., '1H', '4H', '1D')
        timestamp_col: Name of the timestamp column
        
    Returns:
        Resampled DataFrame
    """
    if df.empty or timestamp_col not in df.columns:
        return df
    
    df = df.copy()
    df = ensure_timezone_aware(df, timestamp_col)
    df.set_index(timestamp_col, inplace=True)
    
    # Define aggregation rules
    agg_rules = {
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }
    
    # Only use columns that exist
    agg_rules = {col: rule for col, rule in agg_rules.items() if col in df.columns}
    
    # Resample
    resampled = df.resample(freq).agg(agg_rules)
    
    # Remove rows with NaN values
    resampled.dropna(inplace=True)
    
    # Reset index
    resampled.reset_index(inplace=True)
    
    return resampled


def calculate_returns(df: pd.DataFrame, 
                     price_col: str = 'close', 
                     periods: List[int] = [1, 24]) -> pd.DataFrame:
    """
    Calculate returns for different time periods.
    
    Args:
        df: DataFrame with price data
        price_col: Name of the price column
        periods: List of periods for return calculation
        
    Returns:
        DataFrame with return columns added
    """
    if df.empty or price_col not in df.columns:
        return df
    
    df = df.copy()
    
    for period in periods:
        # Simple returns
        df[f'return_{period}h'] = df[price_col].pct_change(periods=period)
        
        # Log returns
        df[f'log_return_{period}h'] = np.log(df[price_col] / df[price_col].shift(period))
    
    return df


def detect_outliers(df: pd.DataFrame, 
                   columns: List[str] = None, 
                   method: str = 'iqr',
                   threshold: float = 3.0) -> pd.DataFrame:
    """
    Detect outliers in numerical columns.
    
    Args:
        df: DataFrame to analyze
        columns: List of columns to check (default: all numerical)
        method: Method to use ('iqr', 'zscore', 'modified_zscore')
        threshold: Threshold for outlier detection
        
    Returns:
        DataFrame with outlier flags
    """
    if df.empty:
        return df
    
    df = df.copy()
    
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    for col in columns:
        if col not in df.columns:
            continue
            
        if method == 'iqr':
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            df[f'{col}_outlier'] = (df[col] < lower_bound) | (df[col] > upper_bound)
            
        elif method == 'zscore':
            z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
            df[f'{col}_outlier'] = z_scores > threshold
            
        elif method == 'modified_zscore':
            median = df[col].median()
            mad = np.median(np.abs(df[col] - median))
            modified_z_scores = 0.6745 * (df[col] - median) / mad
            df[f'{col}_outlier'] = np.abs(modified_z_scores) > threshold
    
    return df


def fill_missing_values(df: pd.DataFrame, 
                       method: str = 'forward',
                       columns: List[str] = None) -> pd.DataFrame:
    """
    Fill missing values in DataFrame.
    
    Args:
        df: DataFrame with missing values
        method: Method to use ('forward', 'backward', 'interpolate', 'mean', 'median')
        columns: List of columns to fill (default: all)
        
    Returns:
        DataFrame with filled values
    """
    if df.empty:
        return df
    
    df = df.copy()
    
    if columns is None:
        columns = df.columns.tolist()
    
    for col in columns:
        if col not in df.columns:
            continue
            
        if method == 'forward':
            df[col] = df[col].fillna(method='ffill')
        elif method == 'backward':
            df[col] = df[col].fillna(method='bfill')
        elif method == 'interpolate':
            df[col] = df[col].interpolate()
        elif method == 'mean' and df[col].dtype in [np.float64, np.int64]:
            df[col] = df[col].fillna(df[col].mean())
        elif method == 'median' and df[col].dtype in [np.float64, np.int64]:
            df[col] = df[col].fillna(df[col].median())
    
    return df


def merge_data_sources(dataframes: Dict[str, pd.DataFrame], 
                      timestamp_col: str = 'timestamp',
                      how: str = 'outer') -> pd.DataFrame:
    """
    Merge multiple data sources on timestamp.
    
    Args:
        dataframes: Dictionary of DataFrames to merge
        timestamp_col: Name of the timestamp column
        how: How to merge ('inner', 'outer', 'left', 'right')
        
    Returns:
        Merged DataFrame
    """
    if not dataframes:
        return pd.DataFrame()
    
    # Start with the first DataFrame
    result = None
    
    for source_name, df in dataframes.items():
        if df.empty:
            continue
            
        df = df.copy()
        df = ensure_timezone_aware(df, timestamp_col)
        
        # Add source suffix to columns (except timestamp)
        columns_to_rename = [col for col in df.columns if col != timestamp_col]
        df = df.rename(columns={col: f'{col}_{source_name}' for col in columns_to_rename})
        
        if result is None:
            result = df
        else:
            result = pd.merge(result, df, on=timestamp_col, how=how)
    
    if result is not None:
        result = result.sort_values(timestamp_col)
        result.reset_index(drop=True, inplace=True)
    
    return result if result is not None else pd.DataFrame()


def create_data_quality_report(df: pd.DataFrame) -> Dict:
    """
    Generate a comprehensive data quality report.
    
    Args:
        df: DataFrame to analyze
        
    Returns:
        Dictionary with quality metrics
    """
    if df.empty:
        return {'error': 'DataFrame is empty'}
    
    report = {
        'basic_info': {
            'rows': len(df),
            'columns': len(df.columns),
            'memory_usage': df.memory_usage(deep=True).sum(),
            'dtypes': df.dtypes.to_dict()
        },
        'missing_values': {
            'total_missing': df.isnull().sum().sum(),
            'missing_by_column': df.isnull().sum().to_dict(),
            'missing_percentage': (df.isnull().sum() / len(df) * 100).to_dict()
        },
        'duplicates': {
            'total_duplicates': df.duplicated().sum(),
            'duplicate_percentage': df.duplicated().sum() / len(df) * 100
        }
    }
    
    # Numerical columns analysis
    numerical_cols = df.select_dtypes(include=[np.number]).columns
    if len(numerical_cols) > 0:
        report['numerical_summary'] = df[numerical_cols].describe().to_dict()
        
        # Check for infinite values
        inf_counts = {}
        for col in numerical_cols:
            inf_count = np.isinf(df[col]).sum() if df[col].dtype in [np.float64, np.float32] else 0
            inf_counts[col] = inf_count
        report['infinite_values'] = inf_counts
    
    # Datetime columns analysis
    datetime_cols = df.select_dtypes(include=['datetime64']).columns
    if len(datetime_cols) > 0:
        datetime_info = {}
        for col in datetime_cols:
            datetime_info[col] = {
                'min_date': df[col].min(),
                'max_date': df[col].max(),
                'date_range_days': (df[col].max() - df[col].min()).days,
                'timezone_aware': df[col].dt.tz is not None
            }
        report['datetime_summary'] = datetime_info
    
    return report


def save_quality_report(report: Dict, filepath: str):
    """
    Save data quality report to file.
    
    Args:
        report: Quality report dictionary
        filepath: Path to save the report
    """
    import json
    
    # Convert numpy types to native Python types for JSON serialization
    def convert_types(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {key: convert_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [convert_types(item) for item in obj]
        else:
            return obj
    
    converted_report = convert_types(report)
    
    with open(filepath, 'w') as f:
        json.dump(converted_report, f, indent=2, default=str)
    
    logger.info(f"Data quality report saved to {filepath}")


def get_data_files(directory: str, pattern: str = "*.csv") -> List[str]:
    """
    Get list of data files in directory matching pattern.
    
    Args:
        directory: Directory to search
        pattern: File pattern to match
        
    Returns:
        List of file paths
    """
    from glob import glob
    
    directory_path = Path(directory)
    if not directory_path.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return []
    
    files = glob(str(directory_path / pattern))
    return sorted(files)


def load_latest_data(directory: str, prefix: str = "btc") -> Optional[pd.DataFrame]:
    """
    Load the most recent data file from directory.
    
    Args:
        directory: Directory containing data files
        prefix: Filename prefix to match
        
    Returns:
        DataFrame with latest data or None
    """
    files = get_data_files(directory, f"{prefix}*.csv")
    
    if not files:
        logger.warning(f"No data files found with prefix '{prefix}' in {directory}")
        return None
    
    # Get the most recent file (assuming timestamp in filename)
    latest_file = files[-1]
    
    try:
        df = pd.read_csv(latest_file)
        
        # Convert timestamp column if it exists
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
        
        logger.info(f"Loaded latest data from {latest_file}: {len(df)} records")
        return df
        
    except Exception as e:
        logger.error(f"Error loading data from {latest_file}: {e}")
        return None


# Example usage and testing functions
def test_utilities():
    """Test the utility functions with sample data."""
    # Create sample data
    dates = pd.date_range('2024-01-01', periods=100, freq='1H', tz='UTC')
    np.random.seed(42)
    
    sample_data = pd.DataFrame({
        'timestamp': dates,
        'open': 45000 + np.random.normal(0, 1000, 100).cumsum(),
        'high': 45000 + np.random.normal(500, 800, 100).cumsum(),
        'low': 45000 + np.random.normal(-500, 800, 100).cumsum(),
        'close': 45000 + np.random.normal(0, 1000, 100).cumsum(),
        'volume': np.random.exponential(1000, 100)
    })
    
    # Introduce some missing values
    sample_data.loc[10:12, 'close'] = np.nan
    sample_data.loc[50, 'volume'] = np.nan
    
    print("Testing utility functions...")
    
    # Test returns calculation
    data_with_returns = calculate_returns(sample_data)
    print(f"Added return columns: {[col for col in data_with_returns.columns if 'return' in col]}")
    
    # Test resampling
    daily_data = resample_ohlcv(sample_data, freq='1D')
    print(f"Resampled to daily: {len(daily_data)} records")
    
    # Test outlier detection
    data_with_outliers = detect_outliers(sample_data, columns=['close', 'volume'])
    outlier_cols = [col for col in data_with_outliers.columns if 'outlier' in col]
    print(f"Outlier detection columns: {outlier_cols}")
    
    # Test data quality report
    quality_report = create_data_quality_report(sample_data)
    print(f"Quality report keys: {list(quality_report.keys())}")
    
    print("All utility functions tested successfully!")


if __name__ == "__main__":
    test_utilities()
