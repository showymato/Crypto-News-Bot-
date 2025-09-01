from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import re
import logging
import random

logger = logging.getLogger(__name__)

class AIProcessor:
    def __init__(self):
        logger.info("Initializing AI Processor (Lightweight version)")
        try:
            self.sentiment_analyzer = SentimentIntensityAnalyzer()
            logger.info("VADER Sentiment Analyzer loaded successfully")
        except Exception as e:
            logger.error(f"Error loading sentiment analyzer: {e}")
            self.sentiment_analyzer = None

    def clean_text(self, text):
        """Clean and preprocess text"""
        if not text:
            return ""

        try:
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', '', text)
            # Remove extra whitespace
            text = ' '.join(text.split())
            # Remove special characters that might interfere
            text = re.sub(r'[^\w\s.,!?-]', '', text)
            return text
        except Exception as e:
            logger.error(f"Text cleaning error: {e}")
            return text

    def create_summary(self, title, content):
        """Create summary without heavy ML models"""
        try:
            # Clean the content
            title = self.clean_text(title) if title else ""
            content = self.clean_text(content) if content else ""

            # If content is very short, use title + content
            if len(content) < 50:
                summary = f"{title}. {content}".strip()
            else:
                # Use first few sentences
                sentences = re.split(r'[.!?]+', content)
                if sentences:
                    # Take first 1-2 sentences
                    good_sentences = [s.strip() for s in sentences[:2] if len(s.strip()) > 20]
                    if good_sentences:
                        summary = '. '.join(good_sentences)
                        if not summary.endswith('.'):
                            summary += '.'
                    else:
                        summary = content[:200] + "..." if len(content) > 200 else content
                else:
                    summary = content[:200] + "..." if len(content) > 200 else content

            # Ensure summary is reasonable length
            if len(summary) < 30:
                summary = title + ". " + content[:150] + "..."
            elif len(summary) > 400:
                summary = summary[:400] + "..."

            return summary.strip()

        except Exception as e:
            logger.error(f"Summary creation error: {e}")
            # Fallback
            fallback = f"{title}. {content}"[:200]
            return fallback + "..." if len(fallback) == 200 else fallback

    def analyze_sentiment(self, text):
        """Analyze sentiment and return emoji + label"""
        if not self.sentiment_analyzer:
            return "⚠️", "NEUTRAL"

        try:
            if not text:
                return "⚠️", "NEUTRAL"

            # Clean text for analysis
            clean_text = self.clean_text(text)

            if len(clean_text) < 5:
                return "⚠️", "NEUTRAL"

            # Get VADER scores
            scores = self.sentiment_analyzer.polarity_scores(clean_text)
            compound = scores['compound']

            # Determine sentiment with more nuanced thresholds
            if compound >= 0.2:
                return "🚀", "BULLISH"
            elif compound <= -0.2:
                return "🐻", "BEARISH"
            elif compound >= 0.05:
                return "📈", "SLIGHTLY_BULLISH"
            elif compound <= -0.05:
                return "📉", "SLIGHTLY_BEARISH"
            else:
                return "⚠️", "NEUTRAL"

        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return "⚠️", "NEUTRAL"

    def generate_investment_insight(self, title, summary, sentiment_label):
        """Generate investment insights based on keywords and sentiment"""
        try:
            # Combine title and summary for analysis
            text_for_analysis = f"{title} {summary}".lower()

            # Keyword-based insights
            keyword_insights = {
                # Bitcoin specific
                'bitcoin': {
                    'BULLISH': "Bitcoin strength often signals broader crypto market confidence.",
                    'BEARISH': "Bitcoin weakness may indicate market-wide caution ahead.",
                    'NEUTRAL': "Bitcoin developments warrant monitoring for portfolio positioning.",
                    'SLIGHTLY_BULLISH': "Positive Bitcoin sentiment could support market momentum.",
                    'SLIGHTLY_BEARISH': "Bitcoin headwinds may create short-term volatility."
                },
                'btc': {
                    'BULLISH': "BTC momentum could drive institutional adoption forward.",
                    'BEARISH': "BTC concerns may pressure alternative cryptocurrency valuations.",
                    'NEUTRAL': "BTC movements typically influence broader crypto sentiment.",
                    'SLIGHTLY_BULLISH': "BTC gains often correlate with increased market activity.",
                    'SLIGHTLY_BEARISH': "BTC weakness might signal consolidation phase ahead."
                },

                # Ethereum specific
                'ethereum': {
                    'BULLISH': "Ethereum improvements typically boost DeFi ecosystem growth.",
                    'BEARISH': "Ethereum challenges could impact decentralized applications.",
                    'NEUTRAL': "Ethereum developments affect the broader smart contract landscape.",
                    'SLIGHTLY_BULLISH': "Ethereum progress supports long-term blockchain adoption.",
                    'SLIGHTLY_BEARISH': "Ethereum concerns may slow DeFi innovation pace."
                },
                'eth': {
                    'BULLISH': "ETH strength indicates healthy demand for DeFi services.",
                    'BEARISH': "ETH pressure might reduce staking and DeFi participation.",
                    'NEUTRAL': "ETH movements reflect broader smart contract platform health.",
                    'SLIGHTLY_BULLISH': "ETH developments could enhance network utility value.",
                    'SLIGHTLY_BEARISH': "ETH headwinds may create DeFi liquidity concerns."
                },

                # Regulatory
                'regulation': {
                    'BULLISH': "Clear regulations could accelerate institutional crypto adoption.",
                    'BEARISH': "Regulatory uncertainty may constrain market growth potential.",
                    'NEUTRAL': "Regulatory developments shape long-term market structure.",
                    'SLIGHTLY_BULLISH': "Regulatory progress supports mainstream acceptance trends.",
                    'SLIGHTLY_BEARISH': "Regulatory concerns could limit short-term price momentum."
                },
                'sec': {
                    'BULLISH': "Favorable SEC stance may unlock institutional investment flows.",
                    'BEARISH': "SEC scrutiny could create compliance costs and delays.",
                    'NEUTRAL': "SEC decisions significantly influence US crypto market access.",
                    'SLIGHTLY_BULLISH': "SEC clarity benefits long-term market development.",
                    'SLIGHTLY_BEARISH': "SEC enforcement may increase market volatility short-term."
                },

                # ETF
                'etf': {
                    'BULLISH': "ETF approvals typically increase retail and institutional access.",
                    'BEARISH': "ETF rejections may delay mainstream adoption timelines.",
                    'NEUTRAL': "ETF developments affect traditional finance crypto integration.",
                    'SLIGHTLY_BULLISH': "ETF progress supports price discovery and liquidity.",
                    'SLIGHTLY_BEARISH': "ETF delays might reduce near-term institutional interest."
                },

                # Adoption
                'adoption': {
                    'BULLISH': "Growing adoption validates cryptocurrency utility and value.",
                    'BEARISH': "Adoption challenges highlight scalability and usability issues.",
                    'NEUTRAL': "Adoption metrics indicate long-term market maturation.",
                    'SLIGHTLY_BULLISH': "Adoption progress supports fundamental value growth.",
                    'SLIGHTLY_BEARISH': "Adoption slowdown may indicate market saturation risks."
                },

                # DeFi
                'defi': {
                    'BULLISH': "DeFi innovations expand cryptocurrency practical applications.",
                    'BEARISH': "DeFi risks could undermine trust in decentralized finance.",
                    'NEUTRAL': "DeFi developments influence blockchain utility perceptions.",
                    'SLIGHTLY_BULLISH': "DeFi growth demonstrates blockchain technology value.",
                    'SLIGHTLY_BEARISH': "DeFi concerns may reduce yield farming activity."
                },

                # Market terms
                'price': {
                    'BULLISH': "Price momentum could attract momentum-based investment strategies.",
                    'BEARISH': "Price pressure may trigger stop-loss selling cascades.",
                    'NEUTRAL': "Price movements reflect underlying supply-demand dynamics.",
                    'SLIGHTLY_BULLISH': "Price stability supports long-term value accumulation.",
                    'SLIGHTLY_BEARISH': "Price volatility may discourage risk-averse investors."
                },
                'market': {
                    'BULLISH': "Strong markets typically correlate with increased crypto interest.",
                    'BEARISH': "Market weakness often leads to risk-asset liquidation.",
                    'NEUTRAL': "Market conditions significantly influence crypto performance.",
                    'SLIGHTLY_BULLISH': "Market strength supports risk-on asset allocation.",
                    'SLIGHTLY_BEARISH': "Market uncertainty encourages defensive positioning."
                }
            }

            # Find matching keywords
            for keyword, insights in keyword_insights.items():
                if keyword in text_for_analysis:
                    if sentiment_label in insights:
                        return insights[sentiment_label]

            # Fallback insights based on sentiment only
            fallback_insights = {
                'BULLISH': "Strong fundamentals could support continued upward momentum.",
                'BEARISH': "Market headwinds may create near-term volatility challenges.",
                'NEUTRAL': "Development bears monitoring for future market implications.",
                'SLIGHTLY_BULLISH': "Positive signals suggest gradual improvement potential.",
                'SLIGHTLY_BEARISH': "Cautious sentiment indicates consolidation may continue."
            }

            return fallback_insights.get(sentiment_label, "Market development worth tracking for portfolio impact.")

        except Exception as e:
            logger.error(f"Insight generation error: {e}")
            return "Important development for crypto market participants to monitor."

    def process_article(self, article):
        """Process a single article with AI analysis"""
        try:
            # Create summary
            summary = self.create_summary(
                article.get('title', ''),
                article.get('summary', '')
            )

            # Analyze sentiment
            emoji, sentiment_label = self.analyze_sentiment(
                f"{article.get('title', '')} {summary}"
            )

            # Generate insight
            insight = self.generate_investment_insight(
                article.get('title', ''),
                summary,
                sentiment_label
            )

            # Return processed article
            processed_article = {
                'title': article.get('title', 'No Title'),
                'summary': summary,
                'emoji': emoji,
                'sentiment_label': sentiment_label,
                'insight': insight,
                'link': article.get('link', ''),
                'source': article.get('source_name', 'Unknown'),
                'source_title': article.get('source_title', 'Unknown'),
                'published': article.get('published', ''),
                'processed_at': article.get('fetched_at', '')
            }

            return processed_article

        except Exception as e:
            logger.error(f"Article processing error: {e}")
            return None