"""
Bitcoin News Data Fetcher for Sentiment Analysis
==============================================

Master's Thesis - Artificial Intelligence Program
Universidad San Francisco de Quito (USFQ)
Author: Cristian Rodríguez
Year: 2025

This script fetches Bitcoin-related news from multiple sources for sentiment analysis.
The data is saved to the bronze layer for later processing with FinBERT.
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
import feedparser
import re
from urllib.parse import urljoin, urlparse
import hashlib

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
    return {
        'news_sources': {
            'enabled': os.getenv('NEWS_ENABLED', 'true').lower() == 'true',
            'sources': os.getenv('NEWS_SOURCES', 'coindesk,cointelegraph,bitcoin_magazine,decrypt').split(','),
            'max_articles_per_source': int(os.getenv('MAX_ARTICLES_PER_SOURCE', '100')),
            'days_back': int(os.getenv('NEWS_DAYS_BACK', '30')),
        },
        'newsapi': {
            'enabled': os.getenv('NEWSAPI_ENABLED', 'false').lower() == 'true',
            'api_key': os.getenv('NEWSAPI_KEY', ''),
            'sources': 'crypto-coins-news,the-verge',
            'query': 'bitcoin OR BTC OR cryptocurrency',
        },
        'reddit': {
            'enabled': os.getenv('REDDIT_ENABLED', 'false').lower() == 'true',
            'subreddits': os.getenv('REDDIT_SUBREDDITS', 'Bitcoin,CryptoCurrency,btc').split(','),
            'limit': int(os.getenv('REDDIT_LIMIT', '50')),
        },
        'system': {
            'bronze_path': os.getenv('BRONZE_DATA_PATH', 'data/bronze'),
            'request_delay': float(os.getenv('REQUEST_DELAY', '2.0')),
            'timeout': int(os.getenv('TIMEOUT', '30')),
            'max_retries': int(os.getenv('MAX_RETRIES', '3')),
        }
    }


class NewsDataFetcher:
    """Fetches Bitcoin news from multiple sources for sentiment analysis."""
    
    def __init__(self, config):
        self.config = config
        self.bronze_path = Path(config['system']['bronze_path'])
        self.bronze_path.mkdir(parents=True, exist_ok=True)
        
        # RSS feed URLs for crypto news sources
        self.rss_feeds = {
            'coindesk': 'https://www.coindesk.com/arc/outboundfeeds/rss/',
            'cointelegraph': 'https://cointelegraph.com/rss',
            'bitcoin_magazine': 'https://bitcoinmagazine.com/.rss/full/',
            'decrypt': 'https://decrypt.co/feed',
            'cryptocompare': 'https://www.cryptocompare.com/news/rss/',
            'coinmarketcap': 'https://coinmarketcap.com/headlines/rss',
        }

    def clean_text(self, text):
        """Clean and normalize text content."""
        if not text:
            return ""
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\!\?\,\-\:\;]', '', text)
        
        return text.strip()

    def generate_article_id(self, title, source, published_date):
        """Generate unique ID for article to avoid duplicates."""
        content = f"{title}_{source}_{published_date}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def fetch_rss_news(self, source_name, feed_url):
        """Fetch news from RSS feed."""
        logger.info(f"Fetching RSS news from {source_name}...")
        
        try:
            # Parse RSS feed
            feed = feedparser.parse(feed_url)
            
            if feed.bozo:
                logger.warning(f"RSS feed parsing issues for {source_name}")
            
            articles = []
            cutoff_date = datetime.now() - timedelta(days=self.config['news_sources']['days_back'])
            max_articles = self.config['news_sources']['max_articles_per_source']
            
            for entry in feed.entries[:max_articles]:
                try:
                    # Parse publication date
                    pub_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        pub_date = datetime(*entry.updated_parsed[:6])
                    
                    # Skip old articles
                    if pub_date and pub_date < cutoff_date:
                        continue
                    
                    # Extract article data
                    title = self.clean_text(entry.get('title', ''))
                    summary = self.clean_text(entry.get('summary', ''))
                    link = entry.get('link', '')
                    
                    # Filter Bitcoin-related articles
                    bitcoin_keywords = ['bitcoin', 'btc', 'cryptocurrency', 'crypto', 'blockchain']
                    content_text = f"{title} {summary}".lower()
                    
                    if any(keyword in content_text for keyword in bitcoin_keywords):
                        article_id = self.generate_article_id(title, source_name, str(pub_date))
                        
                        articles.append({
                            'article_id': article_id,
                            'source': source_name,
                            'title': title,
                            'summary': summary,
                            'content': summary,  # For RSS, summary is our content
                            'url': link,
                            'published_date': pub_date.isoformat() if pub_date else None,
                            'fetched_date': datetime.now().isoformat(),
                            'word_count': len(content_text.split()),
                            'language': 'en'
                        })
                
                except Exception as e:
                    logger.warning(f"Error processing article from {source_name}: {e}")
                    continue
            
            logger.info(f"Successfully fetched {len(articles)} Bitcoin articles from {source_name}")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching RSS from {source_name}: {e}")
            return []

    def fetch_newsapi_articles(self):
        """Fetch articles from NewsAPI (requires API key)."""
        if not self.config['newsapi']['enabled'] or not self.config['newsapi']['api_key']:
            logger.info("NewsAPI disabled or no API key provided")
            return []
        
        logger.info("Fetching articles from NewsAPI...")
        
        try:
            base_url = "https://newsapi.org/v2/everything"
            
            # Calculate date range
            from_date = (datetime.now() - timedelta(days=self.config['news_sources']['days_back'])).strftime('%Y-%m-%d')
            
            params = {
                'q': self.config['newsapi']['query'],
                'sources': self.config['newsapi']['sources'],
                'from': from_date,
                'sortBy': 'publishedAt',
                'language': 'en',
                'pageSize': 100,
                'apiKey': self.config['newsapi']['api_key']
            }
            
            response = requests.get(base_url, params=params, timeout=self.config['system']['timeout'])
            response.raise_for_status()
            
            data = response.json()
            articles = []
            
            if data.get('status') == 'ok':
                for article in data.get('articles', []):
                    try:
                        title = self.clean_text(article.get('title', ''))
                        description = self.clean_text(article.get('description', ''))
                        content = self.clean_text(article.get('content', ''))
                        
                        # Combine description and content
                        full_content = f"{description} {content}".strip()
                        
                        article_id = self.generate_article_id(
                            title, 
                            article.get('source', {}).get('name', 'newsapi'),
                            article.get('publishedAt', '')
                        )
                        
                        articles.append({
                            'article_id': article_id,
                            'source': f"newsapi_{article.get('source', {}).get('name', 'unknown')}",
                            'title': title,
                            'summary': description,
                            'content': full_content,
                            'url': article.get('url', ''),
                            'published_date': article.get('publishedAt'),
                            'fetched_date': datetime.now().isoformat(),
                            'word_count': len(full_content.split()),
                            'language': 'en'
                        })
                    
                    except Exception as e:
                        logger.warning(f"Error processing NewsAPI article: {e}")
                        continue
            
            logger.info(f"Successfully fetched {len(articles)} articles from NewsAPI")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching from NewsAPI: {e}")
            return []

    def fetch_reddit_posts(self):
        """Fetch Bitcoin-related posts from Reddit (no API key required)."""
        if not self.config['reddit']['enabled']:
            logger.info("Reddit fetching disabled")
            return []
        
        logger.info("Fetching Bitcoin discussions from Reddit...")
        
        all_posts = []
        
        for subreddit in self.config['reddit']['subreddits']:
            try:
                # Use Reddit's JSON API (no authentication required for public posts)
                url = f"https://www.reddit.com/r/{subreddit}/hot.json"
                
                headers = {
                    'User-Agent': 'Bitcoin-Predictor/1.0 (Educational Research)'
                }
                
                response = requests.get(
                    url, 
                    headers=headers, 
                    timeout=self.config['system']['timeout']
                )
                response.raise_for_status()
                
                data = response.json()
                posts = []
                
                for post_data in data.get('data', {}).get('children', []):
                    try:
                        post = post_data.get('data', {})
                        
                        title = self.clean_text(post.get('title', ''))
                        selftext = self.clean_text(post.get('selftext', ''))
                        
                        # Filter Bitcoin-related posts
                        bitcoin_keywords = ['bitcoin', 'btc', 'cryptocurrency', 'crypto']
                        content_text = f"{title} {selftext}".lower()
                        
                        if any(keyword in content_text for keyword in bitcoin_keywords):
                            created_utc = post.get('created_utc')
                            pub_date = datetime.fromtimestamp(created_utc) if created_utc else None
                            
                            # Filter by date
                            cutoff_date = datetime.now() - timedelta(days=self.config['news_sources']['days_back'])
                            if pub_date and pub_date < cutoff_date:
                                continue
                            
                            article_id = self.generate_article_id(
                                title, 
                                f"reddit_{subreddit}",
                                str(pub_date)
                            )
                            
                            posts.append({
                                'article_id': article_id,
                                'source': f"reddit_{subreddit}",
                                'title': title,
                                'summary': selftext[:200] + '...' if len(selftext) > 200 else selftext,
                                'content': selftext,
                                'url': f"https://reddit.com{post.get('permalink', '')}",
                                'published_date': pub_date.isoformat() if pub_date else None,
                                'fetched_date': datetime.now().isoformat(),
                                'word_count': len(f"{title} {selftext}".split()),
                                'language': 'en',
                                'reddit_score': post.get('score', 0),
                                'reddit_comments': post.get('num_comments', 0)
                            })
                    
                    except Exception as e:
                        logger.warning(f"Error processing Reddit post: {e}")
                        continue
                
                all_posts.extend(posts[:self.config['reddit']['limit']])
                logger.info(f"Fetched {len(posts)} posts from r/{subreddit}")
                
                # Rate limiting
                time.sleep(self.config['system']['request_delay'])
                
            except Exception as e:
                logger.error(f"Error fetching from r/{subreddit}: {e}")
                continue
        
        logger.info(f"Successfully fetched {len(all_posts)} posts from Reddit")
        return all_posts

    def save_news_data(self, articles, source_type):
        """Save news data to CSV file."""
        if not articles:
            logger.warning(f"No articles to save for {source_type}")
            return
        
        try:
            df = pd.DataFrame(articles)
            
            # Sort by published date (newest first)
            df['published_date_parsed'] = pd.to_datetime(df['published_date'], errors='coerce')
            df = df.sort_values('published_date_parsed', ascending=False)
            df = df.drop('published_date_parsed', axis=1)
            
            # Remove duplicates based on article_id
            df = df.drop_duplicates(subset=['article_id'])
            
            # Save to CSV
            filename = f"bitcoin_news_{source_type}_{datetime.now().strftime('%Y%m%d')}.csv"
            filepath = self.bronze_path / filename
            
            df.to_csv(filepath, index=False, encoding='utf-8')
            
            # Save metadata
            metadata = {
                'source_type': source_type,
                'articles_count': int(len(df)),
                'date_range': {
                    'oldest': str(df['published_date'].min()) if 'published_date' in df.columns else None,
                    'newest': str(df['published_date'].max()) if 'published_date' in df.columns else None
                },
                'sources': df['source'].unique().tolist() if 'source' in df.columns else [],
                'total_words': int(df['word_count'].sum()) if 'word_count' in df.columns else 0,
                'fetched_at': datetime.now().isoformat(),
                'file_path': str(filepath)
            }
            
            metadata_path = filepath.with_suffix('.json')
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Data saved: {filepath}")
            logger.info(f"Metadata saved: {metadata_path}")
            logger.info(f"Articles saved: {len(df)}")
            
        except Exception as e:
            logger.error(f"Error saving news data: {e}")

    def fetch_all_news(self):
        """Fetch news from all configured sources."""
        logger.info("Starting Bitcoin news data acquisition...")
        logger.info("Universidad San Francisco de Quito (USFQ)")
        logger.info("Author: Cristian Rodríguez - 2025")
        
        all_articles = []
        
        # Fetch from RSS sources
        if self.config['news_sources']['enabled']:
            rss_articles = []
            
            for source_name in self.config['news_sources']['sources']:
                if source_name in self.rss_feeds:
                    articles = self.fetch_rss_news(source_name, self.rss_feeds[source_name])
                    rss_articles.extend(articles)
                    
                    # Rate limiting
                    time.sleep(self.config['system']['request_delay'])
            
            if rss_articles:
                self.save_news_data(rss_articles, 'rss')
                all_articles.extend(rss_articles)
        
        # Fetch from NewsAPI
        newsapi_articles = self.fetch_newsapi_articles()
        if newsapi_articles:
            self.save_news_data(newsapi_articles, 'newsapi')
            all_articles.extend(newsapi_articles)
        
        # Fetch from Reddit
        reddit_articles = self.fetch_reddit_posts()
        if reddit_articles:
            self.save_news_data(reddit_articles, 'reddit')
            all_articles.extend(reddit_articles)
        
        # Save combined dataset
        if all_articles:
            self.save_news_data(all_articles, 'combined')
            
            logger.info(f"\nNews data acquisition completed successfully!")
            logger.info(f"Total articles collected: {len(all_articles)}")
            
            # Show summary by source
            sources_summary = {}
            for article in all_articles:
                source = article.get('source', 'unknown')
                sources_summary[source] = sources_summary.get(source, 0) + 1
            
            logger.info("Articles by source:")
            for source, count in sources_summary.items():
                logger.info(f"  - {source}: {count} articles")
                
            return pd.DataFrame(all_articles)
        
        else:
            logger.error("No news articles were fetched")
            return pd.DataFrame()


def main():
    """Main execution function."""
    try:
        # Load configuration
        config = load_config()
        
        # Create fetcher instance
        fetcher = NewsDataFetcher(config)
        
        # Fetch all news data
        news_data = fetcher.fetch_all_news()
        
        if not news_data.empty:
            print(f"\nNews data collection completed!")
            print(f"Total articles: {len(news_data)}")
            print(f"Data saved to: {fetcher.bronze_path}")
            print("\nNext steps:")
            print("  - Clean and preprocess text data")
            print("  - Apply FinBERT sentiment analysis")
            print("  - Combine with price data for feature engineering")
        else:
            print("No news data was collected. Check configuration and internet connection.")
            
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise


if __name__ == "__main__":
    main()
