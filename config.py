import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# News Sources (RSS feeds)
NEWS_SOURCES = {
    'coindesk': 'https://www.coindesk.com/arc/outboundfeeds/rss/',
    'cointelegraph': 'https://cointelegraph.com/rss',
    'decrypt': 'https://decrypt.co/feed',
    'coinmarketcap': 'https://coinmarketcap.com/headlines/rss',
    'cryptonews': 'https://cryptonews.com/news/feed'
}

# Bot Configuration
MAX_ARTICLES_PER_SOURCE = 15
TOTAL_ARTICLES_LIMIT = 50
DIGEST_ARTICLES_COUNT = 10

# Scheduler Configuration
DIGEST_TIME_HOUR = 9  # 9 AM UTC
DIGEST_TIME_MINUTE = 0

# Database
DATABASE_PATH = 'users.db'

# Deployment
PORT = int(os.environ.get("PORT", 8000))
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "")