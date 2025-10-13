"""
Bitcoin Price Data Fetcher - Simplified Version
==============================================

Master's Thesis - Artificial Intelligence Program
Universidad San Francisco de Quito (USFQ)
Author: Cristian Rodríguez
Year: 2025

Simplified version focused only on data acquisition from free APIs.
This script fetches Bitcoin price data and saves it to the bronze layer.
"""

import pandas as pd
import requests
import json
from datetime import datetime, timezone, timedelta
import time
import os
from pathlib import Path
import logging
from dotenv import load_dotenv
import yfinance as yf

# Load environment variables
load_dotenv()

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=getattr(logging, log_level),
    format=os.getenv('LOG_FORMAT', '[%(asctime)s] %(levelname)s - %(message)s')
)
logger = logging.getLogger(__name__)


def load_config():
    """Load configuration from environment variables."""
    config = {
        'binance': {
            'enabled': os.getenv('BINANCE_ENABLED', 'true').lower() == 'true',
            'intervals': os.getenv('BINANCE_INTERVALS', '1h,4h,1d').split(','),
            'symbol': os.getenv('BINANCE_SYMBOL', 'BTCUSDT'),
            'limit': int(os.getenv('BINANCE_LIMIT', '1000')),
            'delay': float(os.getenv('BINANCE_DELAY', '1')),
            'description': 'Binance cryptocurrency exchange API'
        },
        'yahoo_finance': {
            'enabled': os.getenv('YAHOO_ENABLED', 'true').lower() == 'true',
            'intervals': os.getenv('YAHOO_INTERVALS', '1h,1d').split(','),
            'symbol': os.getenv('YAHOO_SYMBOL', 'BTC-USD'),
            'periods': {
                '1h': os.getenv('YAHOO_PERIOD_1H', '60d'),
                '1d': os.getenv('YAHOO_PERIOD_1D', '2y')
            },
            'delay': float(os.getenv('YAHOO_DELAY', '0.5')),
            'description': 'Yahoo Finance API'
        },
        'coingecko': {
            'enabled': os.getenv('COINGECKO_ENABLED', 'false').lower() == 'true',
            'intervals': ['1h', '1d'],
            'coin_id': os.getenv('COINGECKO_COIN_ID', 'bitcoin'),
            'vs_currency': os.getenv('COINGECKO_VS_CURRENCY', 'usd'),
            'days': {
                '1h': int(os.getenv('COINGECKO_DAYS_1H', '30')),
                '1d': int(os.getenv('COINGECKO_DAYS_1D', '365'))
            },
            'api_key': os.getenv('COINGECKO_API_KEY', ''),
            'delay': float(os.getenv('COINGECKO_DELAY', '2')),
            'description': 'CoinGecko API (requires key)'
        },
        'coinapi': {
            'enabled': os.getenv('COINAPI_ENABLED', 'false').lower() == 'true',
            'symbol': os.getenv('COINAPI_SYMBOL', 'BTC'),
            'currency': os.getenv('COINAPI_CURRENCY', 'USD'),
            'api_key': os.getenv('COINAPI_API_KEY', ''),
            'delay': float(os.getenv('COINAPI_DELAY', '1')),
            'description': 'CoinAPI (requires key)'
        },
        'storage': {
            'bronze_path': os.getenv('DATA_BRONZE_PATH', 'data/bronze'),
            'silver_path': os.getenv('DATA_SILVER_PATH', 'data/silver'),
            'gold_path': os.getenv('DATA_GOLD_PATH', 'data/gold'),
            'clean_old_files': os.getenv('CLEAN_OLD_FILES', 'true').lower() == 'true',
            'backup_old_files': os.getenv('BACKUP_OLD_FILES', 'false').lower() == 'true',
            'max_backup_days': int(os.getenv('MAX_BACKUP_DAYS', '7'))
        },
        'system': {
            'timeout': int(os.getenv('REQUEST_TIMEOUT', '30')),
            'max_retries': int(os.getenv('MAX_RETRIES', '3')),
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'debug_mode': os.getenv('DEBUG_MODE', 'true').lower() == 'true'
        }
    }
    return config


class BitcoinDataFetcher:
    """Multi-source Bitcoin data fetcher with configurable sources."""
    
    def __init__(self, config=None):
        # Load configuration from environment or use provided config
        self.config = config or load_config()
        
        # Set up data paths
        base_path = Path(__file__).parent.parent.parent
        self.bronze_path = base_path / self.config['storage']['bronze_path']
        self.silver_path = base_path / self.config['storage']['silver_path']
        self.gold_path = base_path / self.config['storage']['gold_path']
        
        # Create directories
        self.bronze_path.mkdir(parents=True, exist_ok=True)
        self.silver_path.mkdir(parents=True, exist_ok=True)
        self.gold_path.mkdir(parents=True, exist_ok=True)
        
        # Log configuration
        if self.config['system']['debug_mode']:
            self.log_configuration()
    
    def log_configuration(self):
        """Log current configuration for debugging."""
        logger.info("=== CONFIGURATION LOADED ===")
        logger.info(f"Environment: {self.config['system']['environment']}")
        logger.info(f"Binance enabled: {self.config['binance']['enabled']}")
        logger.info(f"Yahoo Finance enabled: {self.config['yahoo_finance']['enabled']}")
        logger.info(f"CoinGecko enabled: {self.config['coingecko']['enabled']}")
        logger.info(f"Data path: {self.bronze_path}")
        logger.info("==============================")
    
    def clean_old_data(self, backup=True):
        """
        Clean old data files from bronze layer.
        
        Args:
            backup: If True, create a backup of existing files before cleaning
        """
        try:
            # Find all CSV files in bronze directory
            csv_files = list(self.bronze_path.glob("*.csv"))
            
            if not csv_files:
                logger.info("No existing data files found to clean")
                return
            
            logger.info(f"Found {len(csv_files)} existing data files")
            
            # Create backup if requested
            if backup:
                backup_dir = self.bronze_path / "backup"
                backup_dir.mkdir(exist_ok=True)
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                
                for file_path in csv_files:
                    backup_path = backup_dir / f"{file_path.stem}_backup_{timestamp}{file_path.suffix}"
                    file_path.rename(backup_path)
                    logger.info(f"Backed up: {file_path.name} → {backup_path.name}")
            else:
                # Simply remove files
                for file_path in csv_files:
                    file_path.unlink()
                    logger.info(f"Removed: {file_path.name}")
            
            logger.info("Old data files cleaned successfully")
            
        except Exception as e:
            logger.error(f"Error cleaning old data: {e}")
    
    def get_existing_files_info(self):
        """Get information about existing data files."""
        csv_files = list(self.bronze_path.glob("*.csv"))
        
        if not csv_files:
            return None
        
        files_info = []
        total_size = 0
        
        for file_path in csv_files:
            stat = file_path.stat()
            size_mb = stat.st_size / (1024 * 1024)
            modified = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
            
            files_info.append({
                'name': file_path.name,
                'size_mb': size_mb,
                'modified': modified
            })
            total_size += size_mb
        
        return {
            'files': files_info,
            'total_files': len(csv_files),
            'total_size_mb': total_size
        }
        
    def fetch_binance_data(self, symbol="BTCUSDT", interval="1h", limit=1000):
        """
        Fetch OHLCV data from Binance public API.
        
        Args:
            symbol: Trading pair (e.g., BTCUSDT)
            interval: Time interval (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)
            limit: Number of candles (max 1000)
        """
        try:
            url = "https://api.binance.com/api/v3/klines"
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': min(limit, 1000)
            }
            
            logger.info(f"Fetching Binance data for {symbol} ({interval})...")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                logger.warning("No data received from Binance")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # Convert data types
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            df[numeric_columns] = df[numeric_columns].astype(float)
            
            # Convert timestamp
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
            
            # Select relevant columns
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].copy()
            df['source'] = 'binance'
            df['symbol'] = symbol
            df['interval'] = interval
            
            logger.info(f"Successfully fetched {len(df)} records from Binance")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching Binance data: {e}")
            return pd.DataFrame()
    
    def fetch_yahoo_finance_data(self, symbol="BTC-USD", period="60d", interval="1h"):
        """
        Fetch OHLCV data from Yahoo Finance API.
        
        Args:
            symbol: Stock/crypto symbol (e.g., BTC-USD, ETH-USD)
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Time interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
        """
        try:
            logger.info(f"Fetching Yahoo Finance data for {symbol} ({interval}, {period})...")
            
            # Create ticker object
            ticker = yf.Ticker(symbol)
            
            # Fetch historical data
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                logger.warning(f"No data received from Yahoo Finance for {symbol}")
                return pd.DataFrame()
            
            # Reset index to make timestamp a column
            df.reset_index(inplace=True)
            
            # Rename columns to match our schema
            column_mapping = {
                'Datetime': 'timestamp',
                'Date': 'timestamp',  # For daily data
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            }
            
            # Only rename columns that exist
            existing_mapping = {old: new for old, new in column_mapping.items() if old in df.columns}
            df.rename(columns=existing_mapping, inplace=True)
            
            # Ensure timestamp is timezone-aware
            if 'timestamp' in df.columns:
                if df['timestamp'].dt.tz is None:
                    df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
                else:
                    df['timestamp'] = df['timestamp'].dt.tz_convert('UTC')
            
            # Add metadata
            df['source'] = 'yahoo_finance'
            df['symbol'] = symbol
            df['interval'] = interval
            
            # Select relevant columns (handle missing volume for some intervals)
            columns_to_keep = ['timestamp', 'open', 'high', 'low', 'close', 'source', 'symbol', 'interval']
            if 'volume' in df.columns:
                columns_to_keep.insert(5, 'volume')
            else:
                df['volume'] = 0  # Add placeholder volume if not available
                columns_to_keep.insert(5, 'volume')
            
            df = df[columns_to_keep].copy()
            
            logger.info(f"Successfully fetched {len(df)} records from Yahoo Finance")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching Yahoo Finance data: {e}")
            return pd.DataFrame()
    
    def fetch_coingecko_data(self, coin_id="bitcoin", vs_currency="usd", days=30):
        """
        Fetch price data from CoinGecko API.
        
        Args:
            coin_id: Coin identifier (bitcoin, ethereum, etc.)
            vs_currency: Currency to compare against
            days: Number of days of historical data (max 365 for free tier)
        """
        try:
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
            params = {
                'vs_currency': vs_currency,
                'days': min(days, 365),  # Free tier limit
                'interval': 'hourly' if days <= 90 else 'daily'
            }
            
            logger.info(f"Fetching CoinGecko data for {coin_id} ({days} days)...")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'prices' not in data:
                logger.warning("No price data in CoinGecko response")
                return pd.DataFrame()
            
            # Convert prices to DataFrame
            prices = data['prices']
            volumes = data.get('total_volumes', [])
            
            df = pd.DataFrame(prices, columns=['timestamp', 'close'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
            
            # Add volume if available
            if volumes:
                volume_df = pd.DataFrame(volumes, columns=['timestamp', 'volume'])
                volume_df['timestamp'] = pd.to_datetime(volume_df['timestamp'], unit='ms', utc=True)
                df = df.merge(volume_df, on='timestamp', how='left')
                
            # For CoinGecko, use close price for OHLC (limitation of free API)
            df['open'] = df['close']
            df['high'] = df['close']  
            df['low'] = df['close']
            df['volume'] = df.get('volume', 0)
            
            # Add metadata
            df['source'] = 'coingecko'
            df['symbol'] = coin_id
            df['interval'] = params['interval']
            
            # Reorder columns
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume', 'source', 'symbol', 'interval']].copy()
            
            logger.info(f"Successfully fetched {len(df)} records from CoinGecko")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching CoinGecko data: {e}")
            return pd.DataFrame()
    
    def fetch_coinapi_data(self, symbol="BTC", currency="USD", limit=100):
        """
        Fetch data from CoinAPI (free tier - limited requests).
        Note: This requires API key for production use.
        """
        try:
            # Using the free tier endpoint (limited)
            url = f"https://rest.coinapi.io/v1/ohlcv/{symbol}/{currency}/latest"
            params = {
                'period_id': '1HRS',
                'limit': min(limit, 100)  # Free tier limit
            }
            
            # Note: In production, add API key
            # headers = {'X-CoinAPI-Key': 'YOUR_API_KEY'}
            
            logger.info(f"Attempting to fetch CoinAPI data for {symbol}/{currency}...")
            response = requests.get(url, params=params, timeout=30)
            
            # CoinAPI requires API key, so we'll skip if unauthorized
            if response.status_code == 401:
                logger.info("CoinAPI requires API key, skipping...")
                return pd.DataFrame()
            
            response.raise_for_status()
            data = response.json()
            
            if not data:
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Rename columns to match our schema
            if 'time_period_start' in df.columns:
                df['timestamp'] = pd.to_datetime(df['time_period_start'], utc=True)
            
            column_mapping = {
                'price_open': 'open',
                'price_high': 'high', 
                'price_low': 'low',
                'price_close': 'close',
                'volume_traded': 'volume'
            }
            df.rename(columns=column_mapping, inplace=True)
            
            # Add metadata
            df['source'] = 'coinapi'
            df['symbol'] = f"{symbol}/{currency}"
            df['interval'] = '1h'
            
            # Select relevant columns
            columns_to_keep = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'source', 'symbol', 'interval']
            available_columns = [col for col in columns_to_keep if col in df.columns]
            df = df[available_columns].copy()
            
            logger.info(f"Successfully fetched {len(df)} records from CoinAPI")
            return df
            
        except Exception as e:
            logger.info(f"CoinAPI not available (likely requires API key): {e}")
            return pd.DataFrame()
    
    def save_data(self, df, filename, add_timestamp=False):
        """
        Save DataFrame to CSV in bronze layer.
        
        Args:
            df: DataFrame to save
            filename: Base filename (without extension)
            add_timestamp: If True, add timestamp to filename (default: False for consistent naming)
        """
        if df.empty:
            logger.warning(f"Cannot save empty DataFrame: {filename}")
            return
        
        if add_timestamp:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filepath = self.bronze_path / f"{filename}_{timestamp}.csv"
        else:
            filepath = self.bronze_path / f"{filename}.csv"
        
        try:
            df.to_csv(filepath, index=False)
            
            # Add metadata to the file (as comments or separate info)
            file_info = {
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'records_count': len(df),
                'date_range': f"{df['timestamp'].min()} to {df['timestamp'].max()}" if 'timestamp' in df.columns else 'N/A',
                'sources': df['source'].unique().tolist() if 'source' in df.columns else []
            }
            
            # Save metadata as JSON
            metadata_path = filepath.with_suffix('.json')
            with open(metadata_path, 'w') as f:
                json.dump(file_info, f, indent=2, default=str)
            
            logger.info(f"Data saved: {filepath}")
            logger.info(f"Metadata saved: {metadata_path}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Error saving data: {e}")
            return None
    
    def fetch_all_data(self):
        """Fetch data from all configured sources."""
        logger.info("=== Starting Bitcoin Data Acquisition ===")
        logger.info("Master's Thesis - Universidad San Francisco de Quito (USFQ)")
        logger.info("Author: Cristian Rodríguez - 2025")
        logger.info("=" * 50)
        
        # Check existing files
        existing_info = self.get_existing_files_info()
        if existing_info:
            logger.info(f"\nExisting data files detected:")
            logger.info(f"   Files: {existing_info['total_files']}")
            logger.info(f"   Total size: {existing_info['total_size_mb']:.2f} MB")
        
        # Clean old data if configured
        if self.config['storage']['clean_old_files'] and existing_info:
            logger.info(f"\nCleaning old data files...")
            self.clean_old_data(backup=self.config['storage']['backup_old_files'])
        
        results = {}
        saved_files = []
        source_count = 0
        
        # 1. Fetch from Binance (if enabled)
        if self.config['binance']['enabled']:
            source_count += 1
            logger.info(f"\n{source_count}. Fetching from Binance API...")
            
            binance_config = self.config['binance']
            for interval in binance_config['intervals']:
                df = self.fetch_binance_data(
                    symbol=binance_config['symbol'],
                    interval=interval,
                    limit=binance_config['limit']
                )
                if not df.empty:
                    results[f'binance_{interval}'] = df
                    filepath = self.save_data(df, f"binance_btc_{interval}")
                    if filepath:
                        saved_files.append(filepath)
                
                # Rate limiting
                time.sleep(binance_config['delay'])
        
        # 2. Fetch from Yahoo Finance (if enabled)
        if self.config['yahoo_finance']['enabled']:
            source_count += 1
            logger.info(f"\n{source_count}. Fetching from Yahoo Finance API...")
            
            yahoo_config = self.config['yahoo_finance']
            for interval in yahoo_config['intervals']:
                period = yahoo_config['periods'].get(interval, '60d')
                df = self.fetch_yahoo_finance_data(
                    symbol=yahoo_config['symbol'],
                    period=period,
                    interval=interval
                )
                if not df.empty:
                    results[f'yahoo_{interval}'] = df
                    filepath = self.save_data(df, f"yahoo_btc_{interval}")
                    if filepath:
                        saved_files.append(filepath)
                
                # Rate limiting
                time.sleep(yahoo_config['delay'])
        
        # 3. Fetch from CoinGecko (if enabled)
        if self.config['coingecko']['enabled']:
            source_count += 1
            logger.info(f"\n{source_count}. Fetching from CoinGecko API...")
            
            coingecko_config = self.config['coingecko']
            for interval in coingecko_config['intervals']:
                days = coingecko_config['days'].get(interval, 30)
                df = self.fetch_coingecko_data(
                    coin_id=coingecko_config['coin_id'],
                    vs_currency=coingecko_config['vs_currency'],
                    days=days
                )
                if not df.empty:
                    results[f'coingecko_{interval}'] = df
                    filepath = self.save_data(df, f"coingecko_btc_{interval}")
                    if filepath:
                        saved_files.append(filepath)
                
                # Rate limiting
                time.sleep(coingecko_config['delay'])
        
        # 4. Fetch from CoinAPI (if enabled and has API key)
        if self.config['coinapi']['enabled'] and self.config['coinapi']['api_key']:
            source_count += 1
            logger.info(f"\n{source_count}. Fetching from CoinAPI...")
            df_coinapi = self.fetch_coinapi_data()
            if not df_coinapi.empty:
                results['coinapi'] = df_coinapi
                filepath = self.save_data(df_coinapi, "coinapi_btc")
                if filepath:
                    saved_files.append(filepath)
        
        # 4. Create combined dataset
        if results:
            logger.info("\n4. Creating combined dataset...")
            all_dfs = list(results.values())
            combined_df = pd.concat(all_dfs, ignore_index=True)
            
            # Sort by timestamp and remove duplicates
            combined_df = combined_df.sort_values('timestamp')
            combined_df = combined_df.drop_duplicates(subset=['timestamp'], keep='first')
            combined_df.reset_index(drop=True, inplace=True)
            
            filepath = self.save_data(combined_df, "btc_combined_data")
            if filepath:
                saved_files.append(filepath)
            
            # Show summary
            logger.info(f"\n=== DATA ACQUISITION SUMMARY ===")
            logger.info(f"Sources fetched: {len(results)}")
            logger.info(f"Total unique records: {len(combined_df)}")
            logger.info(f"Date range: {combined_df['timestamp'].min()} to {combined_df['timestamp'].max()}")
            
            if 'close' in combined_df.columns:
                current_price = combined_df['close'].iloc[-1]
                logger.info(f"Latest Bitcoin price: ${current_price:,.2f}")
            
            # Source breakdown
            logger.info("\nRecords by source:")
            for source, df in results.items():
                logger.info(f"  {source}: {len(df)} records")
            
            logger.info(f"\nFiles saved in: {self.bronze_path}")
            for filepath in saved_files:
                logger.info(f"  - {Path(filepath).name}")
            
            return combined_df, saved_files
        
        else:
            logger.error("No data was successfully fetched from any source")
            return pd.DataFrame(), []
    
    def quick_price_check(self):
        """Quick check of current Bitcoin price from available sources."""
        logger.info("=== Quick Bitcoin Price Check ===")
        
        # Try enabled sources in order of preference
        if self.config['binance']['enabled']:
            df = self.fetch_binance_data(
                symbol=self.config['binance']['symbol'],
                limit=1
            )
        
            if not df.empty:
                price = df['close'].iloc[-1]
                timestamp = df['timestamp'].iloc[-1]
                logger.info(f"Current Bitcoin Price: ${price:,.2f} (Binance)")
                logger.info(f"Last updated: {timestamp}")
                return price
        
        # Try Yahoo Finance if enabled
        if self.config['yahoo_finance']['enabled']:
            df = self.fetch_yahoo_finance_data(
                symbol=self.config['yahoo_finance']['symbol'],
                period='1d',
                interval='1h'
            )
            if not df.empty:
                price = df['close'].iloc[-1]
                timestamp = df['timestamp'].iloc[-1]
                logger.info(f"Current Bitcoin Price: ${price:,.2f} (Yahoo Finance)")
                logger.info(f"Last updated: {timestamp}")
                return price
        
        # Fallback to CoinGecko if enabled
        if self.config['coingecko']['enabled']:
            df = self.fetch_coingecko_data(days=1)
            if not df.empty:
                price = df['close'].iloc[-1]
                timestamp = df['timestamp'].iloc[-1]
                logger.info(f"Current Bitcoin Price: ${price:,.2f} (CoinGecko)")
                logger.info(f"Last updated: {timestamp}")
                return price
        
        logger.error("Could not fetch current price from any enabled source")
        return None


def main():
    """Main execution function."""
    
    # Ask user about cleaning strategy
    print("\n" + "="*60)
    print("DATA ACQUISITION STRATEGY")
    print("="*60)
    print("1. Clean & Download Fresh (Recommended for thesis)")
    print("2. Keep Existing & Add New (Accumulate files)")
    print("3. View Existing Files Only")
    
    choice = input("\nSelect option (1-3, default=1): ").strip() or "1"
    
    if choice == "3":
        # Just view existing files
        temp_fetcher = BitcoinDataFetcher()
        existing_info = temp_fetcher.get_existing_files_info()
        if existing_info:
            print(f"\nExisting data files:")
            print(f"   Total files: {existing_info['total_files']}")
            print(f"   Total size: {existing_info['total_size_mb']:.2f} MB")
            for file_info in existing_info['files']:
                print(f"   - {file_info['name']} ({file_info['size_mb']:.2f} MB)")
        else:
            print("\nNo existing data files found")
        return
    
    # Initialize fetcher based on choice
    clean_before = choice == "1"
    fetcher = BitcoinDataFetcher()
    
    try:
        # Quick price check first
        fetcher.quick_price_check()
        
        print("\n" + "="*60)
        input("Press Enter to start full data acquisition...")
        
        # Full data acquisition
        combined_data, saved_files = fetcher.fetch_all_data()
        
        if not combined_data.empty:
            logger.info("\nData acquisition completed successfully!")
            logger.info("Data is ready for the next pipeline stages:")
            logger.info("  - Cleaning & Normalization")
            logger.info("  - Sentiment Analysis")
            logger.info("  - Feature Engineering")
            
        else:
            logger.error("Data acquisition failed")
        
    except KeyboardInterrupt:
        logger.info("\nData acquisition interrupted by user")
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()