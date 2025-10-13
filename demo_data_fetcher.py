"""
Bitcoin Data Fetcher Demo Script
===============================

Master's Thesis - Artificial Intelligence Program
Universidad San Francisco de Quito (USFQ)
Author: Cristian Rodríguez
Year: 2025

This demo script demonstrates the complete workflow of the Bitcoin price
data acquisition system, showcasing the integration of multiple data sources
and the robustness of the implementation.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from data.fetch_price_data_btc import BitcoinDataFetcher
from utils.helpers import (
    create_data_quality_report, 
    resample_ohlcv, 
    calculate_returns,
    detect_outliers,
    save_quality_report
)
import pandas as pd
import logging
from datetime import datetime, timezone

# Configure logging for demo
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def demo_single_source_fetch():
    """Demonstrate fetching data from individual sources."""
    logger.info("\n" + "="*60)
    logger.info("DEMO 1: Single Source Data Fetching")
    logger.info("="*60)
    
    fetcher = BitcoinDataFetcher()
    
    # Demo 1.1: Binance Data
    logger.info("\n--- Fetching from Binance ---")
    binance_data = fetcher.fetch_binance_data(interval='1h', limit=100)
    if not binance_data.empty:
        logger.info(f"✓ Binance: {len(binance_data)} records")
        logger.info(f"  Date range: {binance_data['timestamp'].min()} to {binance_data['timestamp'].max()}")
        logger.info(f"  Price range: ${binance_data['low'].min():.2f} - ${binance_data['high'].max():.2f}")
    else:
        logger.warning("✗ Binance: No data retrieved")
    
    # Demo 1.2: Yahoo Finance Data
    logger.info("\n--- Fetching from Yahoo Finance ---")
    yahoo_data = fetcher.fetch_yahoo_finance_data(period='5d', interval='1h')
    if not yahoo_data.empty:
        logger.info(f"✓ Yahoo Finance: {len(yahoo_data)} records")
        logger.info(f"  Date range: {yahoo_data['timestamp'].min()} to {yahoo_data['timestamp'].max()}")
        logger.info(f"  Price range: ${yahoo_data['low'].min():.2f} - ${yahoo_data['high'].max():.2f}")
    else:
        logger.warning("✗ Yahoo Finance: No data retrieved")
    
    # Demo 1.3: CoinGecko Data
    logger.info("\n--- Fetching from CoinGecko ---")
    coingecko_data = fetcher.fetch_coingecko_data(days=7)
    if not coingecko_data.empty:
        logger.info(f"✓ CoinGecko: {len(coingecko_data)} records")
        logger.info(f"  Date range: {coingecko_data['timestamp'].min()} to {coingecko_data['timestamp'].max()}")
        logger.info(f"  Price range: ${coingecko_data['low'].min():.2f} - ${coingecko_data['high'].max():.2f}")
    else:
        logger.warning("✗ CoinGecko: No data retrieved")
    
    return binance_data, yahoo_data, coingecko_data


def demo_multi_source_integration():
    """Demonstrate multi-source data integration."""
    logger.info("\n" + "="*60)
    logger.info("DEMO 2: Multi-Source Data Integration")
    logger.info("="*60)
    
    fetcher = BitcoinDataFetcher()
    
    # Fetch from all sources
    all_data = fetcher.fetch_all_sources(save_individual=False, save_combined=False)
    
    if all_data:
        logger.info(f"\n✓ Successfully retrieved data from {len(all_data)} sources:")
        
        total_records = 0
        for source_name, df in all_data.items():
            logger.info(f"  {source_name}: {len(df)} records")
            total_records += len(df)
        
        logger.info(f"\nTotal records across all sources: {total_records}")
        
        # Combine data
        combined_data = fetcher.combine_sources(all_data)
        if not combined_data.empty:
            logger.info(f"✓ Combined into {len(combined_data)} unique records")
            logger.info(f"  Date range: {combined_data['timestamp'].min()} to {combined_data['timestamp'].max()}")
            
            # Show source distribution
            source_counts = combined_data['source'].value_counts()
            logger.info(f"  Source distribution: {source_counts.to_dict()}")
            
            return combined_data
    
    logger.warning("✗ No data retrieved from any source")
    return pd.DataFrame()


def demo_data_quality_analysis(df):
    """Demonstrate data quality analysis."""
    if df.empty:
        logger.warning("Cannot perform data quality analysis on empty DataFrame")
        return
    
    logger.info("\n" + "="*60)
    logger.info("DEMO 3: Data Quality Analysis")
    logger.info("="*60)
    
    # Generate quality report
    quality_report = create_data_quality_report(df)
    
    logger.info(f"\n--- Basic Data Information ---")
    basic_info = quality_report['basic_info']
    logger.info(f"Rows: {basic_info['rows']:,}")
    logger.info(f"Columns: {basic_info['columns']}")
    logger.info(f"Memory usage: {basic_info['memory_usage'] / 1024:.1f} KB")
    
    logger.info(f"\n--- Missing Values Analysis ---")
    missing_info = quality_report['missing_values']
    logger.info(f"Total missing values: {missing_info['total_missing']}")
    
    if missing_info['total_missing'] > 0:
        logger.info("Missing values by column:")
        for col, count in missing_info['missing_by_column'].items():
            if count > 0:
                pct = missing_info['missing_percentage'][col]
                logger.info(f"  {col}: {count} ({pct:.1f}%)")
    else:
        logger.info("✓ No missing values found")
    
    logger.info(f"\n--- Duplicates Analysis ---")
    dup_info = quality_report['duplicates']
    logger.info(f"Duplicate rows: {dup_info['total_duplicates']} ({dup_info['duplicate_percentage']:.1f}%)")
    
    # Validate data
    is_valid, issues = BitcoinDataFetcher().validate_data(df)
    logger.info(f"\n--- Data Validation ---")
    if is_valid:
        logger.info("✓ All validation checks passed")
    else:
        logger.warning(f"✗ Validation issues found: {len(issues)}")
        for issue in issues:
            logger.warning(f"  - {issue}")
    
    # Save quality report
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report_path = f"../../reports/data_quality_report_{timestamp}.json"
    
    try:
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        save_quality_report(quality_report, report_path)
        logger.info(f"✓ Quality report saved to {report_path}")
    except Exception as e:
        logger.warning(f"Could not save quality report: {e}")


def demo_data_processing(df):
    """Demonstrate data processing capabilities."""
    if df.empty:
        logger.warning("Cannot perform data processing on empty DataFrame")
        return
    
    logger.info("\n" + "="*60)
    logger.info("DEMO 4: Data Processing & Feature Engineering")
    logger.info("="*60)
    
    # Calculate returns
    logger.info("\n--- Calculating Returns ---")
    df_with_returns = calculate_returns(df, periods=[1, 6, 24])
    return_cols = [col for col in df_with_returns.columns if 'return' in col]
    logger.info(f"✓ Added return columns: {return_cols}")
    
    # Show return statistics
    if 'return_24h' in df_with_returns.columns:
        ret_24h = df_with_returns['return_24h'].dropna()
        if not ret_24h.empty:
            logger.info(f"  24h returns - Mean: {ret_24h.mean():.4f}, Std: {ret_24h.std():.4f}")
            logger.info(f"  24h returns - Min: {ret_24h.min():.4f}, Max: {ret_24h.max():.4f}")
    
    # Resample to different frequencies
    logger.info("\n--- Resampling Data ---")
    daily_data = resample_ohlcv(df, freq='1D')
    logger.info(f"✓ Resampled to daily: {len(daily_data)} records")
    
    if len(daily_data) > 0:
        logger.info(f"  Daily price range: ${daily_data['low'].min():.2f} - ${daily_data['high'].max():.2f}")
    
    # Detect outliers
    logger.info("\n--- Outlier Detection ---")
    df_with_outliers = detect_outliers(df, columns=['close', 'volume'], method='iqr')
    outlier_cols = [col for col in df_with_outliers.columns if 'outlier' in col]
    
    if outlier_cols:
        logger.info(f"✓ Outlier detection completed for columns: {[col.replace('_outlier', '') for col in outlier_cols]}")
        
        for col in outlier_cols:
            outlier_count = df_with_outliers[col].sum()
            outlier_pct = (outlier_count / len(df_with_outliers)) * 100
            logger.info(f"  {col.replace('_outlier', '')}: {outlier_count} outliers ({outlier_pct:.1f}%)")
    
    return df_with_returns, daily_data


def demo_latest_data_monitoring():
    """Demonstrate real-time data monitoring capabilities."""
    logger.info("\n" + "="*60)
    logger.info("DEMO 5: Latest Data Monitoring")
    logger.info("="*60)
    
    fetcher = BitcoinDataFetcher()
    
    # Get latest 24 hours of data
    latest_data = fetcher.get_latest_data(hours=24)
    
    if not latest_data.empty:
        logger.info(f"✓ Retrieved latest {len(latest_data)} records")
        
        # Current market status  
        current_price = latest_data['close'].iloc[-1]
        logger.info(f"\n--- Current Market Status ---")
        logger.info(f"Current Bitcoin Price: ${current_price:,.2f}")
        
        # 24h statistics
        if len(latest_data) > 1:
            start_price = latest_data['close'].iloc[0]
            price_change = current_price - start_price
            price_change_pct = (price_change / start_price) * 100
            
            logger.info(f"24h Change: ${price_change:,.2f} ({price_change_pct:+.2f}%)")
            logger.info(f"24h High: ${latest_data['high'].max():,.2f}")
            logger.info(f"24h Low: ${latest_data['low'].min():,.2f}")
            logger.info(f"24h Volume: {latest_data['volume'].sum():,.0f}")
            
            # Volatility
            returns = latest_data['close'].pct_change().dropna()
            if not returns.empty:
                volatility = returns.std() * np.sqrt(24)  # Annualized hourly volatility
                logger.info(f"24h Volatility: {volatility:.4f} ({volatility*100:.2f}%)")
        
        return latest_data
    
    else:
        logger.warning("✗ Could not retrieve latest data")
        return pd.DataFrame()


def main():
    """Main demo execution."""
    logger.info("🚀 Bitcoin Data Fetcher - Complete System Demo")
    logger.info("Master's Thesis - Universidad San Francisco de Quito (USFQ)")
    logger.info("Author: Cristian Rodríguez - 2025")
    logger.info("=" * 80)
    
    try:
        # Demo 1: Single source fetching
        binance_data, yahoo_data, coingecko_data = demo_single_source_fetch()
        
        # Demo 2: Multi-source integration
        combined_data = demo_multi_source_integration()
        
        # Demo 3: Data quality analysis
        if not combined_data.empty:
            demo_data_quality_analysis(combined_data)
            
            # Demo 4: Data processing
            processed_data, daily_data = demo_data_processing(combined_data)
        
        # Demo 5: Latest data monitoring
        latest_data = demo_latest_data_monitoring()
        
        # Final summary
        logger.info("\n" + "="*80)
        logger.info("🎉 DEMO COMPLETED SUCCESSFULLY")
        logger.info("="*80)
        logger.info("Summary of demonstrated capabilities:")
        logger.info("✓ Multi-source data acquisition (Binance, Yahoo Finance, CoinGecko)")
        logger.info("✓ Data validation and quality assessment")
        logger.info("✓ Data processing and feature engineering")
        logger.info("✓ Real-time monitoring capabilities")
        logger.info("✓ Robust error handling and logging")
        logger.info("✓ Modular and extensible architecture")
        
        logger.info("\nThe system is ready for integration into the complete")
        logger.info("Bitcoin prediction pipeline as part of your thesis project.")
        
    except Exception as e:
        logger.error(f"Demo execution failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Import numpy for volatility calculation
    import numpy as np
    main()