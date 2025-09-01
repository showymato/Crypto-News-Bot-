import feedparser
import requests
from datetime import datetime, timedelta
import logging
import time
from bs4 import BeautifulSoup
from config import NEWS_SOURCES, MAX_ARTICLES_PER_SOURCE, TOTAL_ARTICLES_LIMIT

logger = logging.getLogger(__name__)

class NewsAggregator:
    def __init__(self):
        self.sources = NEWS_SOURCES
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CryptoNewsBot/1.0 (Telegram Bot)'
        })

    def clean_text(self, text):
        """Clean HTML and format text"""
        if not text:
            return ""

        try:
            # Remove HTML tags
            soup = BeautifulSoup(text, 'html.parser')
            clean_text = soup.get_text()

            # Clean whitespace
            clean_text = ' '.join(clean_text.split())

            # Limit length
            if len(clean_text) > 500:
                clean_text = clean_text[:500] + "..."

            return clean_text

        except Exception as e:
            logger.error(f"Text cleaning error: {e}")
            return text[:200] if text else ""

    def fetch_rss_feed(self, source_name, url):
        """Fetch and parse RSS feed"""
        articles = []

        try:
            logger.info(f"Fetching from {source_name}: {url}")

            # Set timeout for RSS parsing
            feedparser._parse_date = lambda x: None  # Skip date parsing issues

            feed = feedparser.parse(url)

            if feed.bozo and feed.bozo_exception:
                logger.warning(f"RSS parsing warning for {source_name}: {feed.bozo_exception}")

            if not hasattr(feed, 'entries') or not feed.entries:
                logger.warning(f"No entries found for {source_name}")
                return []

            for i, entry in enumerate(feed.entries[:MAX_ARTICLES_PER_SOURCE]):
                try:
                    # Extract article data
                    article = {
                        'title': self.clean_text(getattr(entry, 'title', 'No Title')),
                        'summary': self.clean_text(getattr(entry, 'summary', '') or getattr(entry, 'description', '')),
                        'link': getattr(entry, 'link', ''),
                        'published': getattr(entry, 'published', ''),
                        'source_name': source_name,
                        'source_title': getattr(feed.feed, 'title', source_name),
                        'guid': getattr(entry, 'id', f"{source_name}_{i}"),
                        'fetched_at': datetime.now().isoformat()
                    }

                    # Skip if no title or link
                    if not article['title'] or article['title'] == 'No Title':
                        continue
                    if not article['link']:
                        continue

                    articles.append(article)

                except Exception as e:
                    logger.error(f"Error processing entry from {source_name}: {e}")
                    continue

            logger.info(f"Successfully fetched {len(articles)} articles from {source_name}")
            return articles

        except Exception as e:
            logger.error(f"Error fetching RSS from {source_name}: {e}")
            return []

    def remove_duplicates(self, articles):
        """Remove duplicate articles based on title similarity"""
        if not articles:
            return []

        unique_articles = []
        seen_titles = set()

        for article in articles:
            title = article['title'].lower().strip()

            # Create a normalized title for comparison
            title_words = set(title.split())

            # Check if we've seen a very similar title
            is_duplicate = False
            for seen_title in seen_titles:
                seen_words = set(seen_title.split())

                # If more than 70% of words are the same, consider it duplicate
                if len(title_words) > 0 and len(seen_words) > 0:
                    common_words = title_words.intersection(seen_words)
                    similarity = len(common_words) / max(len(title_words), len(seen_words))

                    if similarity > 0.7:
                        is_duplicate = True
                        break

            if not is_duplicate:
                seen_titles.add(title)
                unique_articles.append(article)

        logger.info(f"Removed {len(articles) - len(unique_articles)} duplicate articles")
        return unique_articles

    def rank_articles(self, articles):
        """Simple ranking based on keywords and recency"""
        if not articles:
            return []

        # Keywords that increase article importance
        important_keywords = [
            'bitcoin', 'btc', 'ethereum', 'eth', 'crypto', 'blockchain',
            'defi', 'nft', 'regulation', 'sec', 'etf', 'adoption',
            'price', 'market', 'trading', 'investment', 'bull', 'bear'
        ]

        for article in articles:
            score = 0
            title_lower = article['title'].lower()
            summary_lower = article['summary'].lower()

            # Score based on keyword presence
            for keyword in important_keywords:
                if keyword in title_lower:
                    score += 3  # Title matches are more important
                if keyword in summary_lower:
                    score += 1

            # Boost score for certain sources
            if article['source_name'] in ['coindesk', 'cointelegraph']:
                score += 2

            article['relevance_score'] = score

        # Sort by relevance score (descending)
        sorted_articles = sorted(articles, key=lambda x: x.get('relevance_score', 0), reverse=True)

        return sorted_articles

    def get_latest_news(self):
        """Main method to get processed news articles"""
        all_articles = []

        # Fetch from all sources
        for source_name, url in self.sources.items():
            try:
                articles = self.fetch_rss_feed(source_name, url)
                all_articles.extend(articles)

                # Small delay between requests to be respectful
                time.sleep(0.5)

            except Exception as e:
                logger.error(f"Failed to fetch from {source_name}: {e}")
                continue

        if not all_articles:
            logger.warning("No articles fetched from any source")
            return []

        logger.info(f"Total articles fetched: {len(all_articles)}")

        # Remove duplicates
        unique_articles = self.remove_duplicates(all_articles)

        # Rank articles by relevance
        ranked_articles = self.rank_articles(unique_articles)

        # Limit total articles
        final_articles = ranked_articles[:TOTAL_ARTICLES_LIMIT]

        logger.info(f"Final processed articles: {len(final_articles)}")
        return final_articles

    def get_article_summary(self, article):
        """Get article summary with fallback"""
        summary = article.get('summary', '')

        if not summary or len(summary) < 50:
            # Try to create summary from title
            title = article.get('title', '')
            if len(title) > 100:
                summary = title[:200] + "..."
            else:
                summary = title + ". Full details available at source."

        # Ensure summary is not too long
        if len(summary) > 300:
            summary = summary[:300] + "..."

        return summary