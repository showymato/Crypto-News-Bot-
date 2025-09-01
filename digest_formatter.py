from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DigestFormatter:
    def __init__(self):
        self.max_message_length = 4000  # Telegram limit is 4096, leave some buffer
        self.max_title_length = 80
        self.max_summary_length = 200

    def truncate_text(self, text, max_length, add_ellipsis=True):
        """Truncate text to specified length"""
        if not text or len(text) <= max_length:
            return text

        truncated = text[:max_length].rstrip()
        return truncated + "..." if add_ellipsis else truncated

    def format_daily_digest(self, processed_articles):
        """Format articles into daily digest message"""
        if not processed_articles:
            return self.format_no_news_message()

        try:
            current_date = datetime.now().strftime("%A, %B %d, %Y")

            # Header
            message = f"📈 **CRYPTO DIGEST**\n*{current_date}*\n\n"

            # Process articles
            for i, article in enumerate(processed_articles[:10], 1):
                article_section = self.format_article_section(article, i)

                # Check if adding this article would exceed message limit
                if len(message + article_section) > self.max_message_length:
                    # If we haven't added any articles yet, add a truncated version
                    if i == 1:
                        truncated_section = self.format_article_section(article, i, truncate=True)
                        message += truncated_section
                    break

                message += article_section

            # Footer
            footer = "\n💡 **Commands:** /hot for trending | /settings for preferences | /help for more"

            if len(message + footer) <= self.max_message_length:
                message += footer

            return message

        except Exception as e:
            logger.error(f"Error formatting daily digest: {e}")
            return self.format_error_message()

    def format_article_section(self, article, number, truncate=False):
        """Format individual article section"""
        try:
            emoji = article.get('emoji', '⚠️')
            sentiment = article.get('sentiment_label', 'NEUTRAL')
            title = article.get('title', 'No Title')
            summary = article.get('summary', 'No summary available')
            insight = article.get('insight', 'Monitor for developments')
            source = article.get('source', 'Unknown')

            # Truncate for length
            max_title = 60 if truncate else self.max_title_length
            max_summary = 120 if truncate else self.max_summary_length
            max_insight = 80 if truncate else 150

            title = self.truncate_text(title, max_title)
            summary = self.truncate_text(summary, max_summary)
            insight = self.truncate_text(insight, max_insight)

            # Format sentiment label for display
            display_sentiment = sentiment.replace('_', ' ')

            article_text = (
                f"**{number}. {emoji} {display_sentiment}** | {title}\n"
                f"*{summary}*\n"
                f"**💡 Why it matters:** {insight}\n"
                f"📰 *Source: {source}*\n\n"
            )

            return article_text

        except Exception as e:
            logger.error(f"Error formatting article section: {e}")
            return f"**{number}.** Article formatting error\n\n"

    def format_trending_news(self, processed_articles):
        """Format trending news by sentiment"""
        if not processed_articles:
            return "📊 **TRENDING NEWS**\n\nNo trending stories available right now!"

        try:
            # Group by sentiment
            sentiment_groups = {
                'BULLISH': [],
                'SLIGHTLY_BULLISH': [],
                'BEARISH': [],
                'SLIGHTLY_BEARISH': [],
                'NEUTRAL': []
            }

            for article in processed_articles:
                sentiment = article.get('sentiment_label', 'NEUTRAL')
                sentiment_groups[sentiment].append(article)

            message = "📊 **TRENDING BY SENTIMENT**\n\n"

            # Bullish stories
            bullish_stories = sentiment_groups['BULLISH'] + sentiment_groups['SLIGHTLY_BULLISH']
            if bullish_stories:
                message += "🚀 **BULLISH TRENDS**\n"
                for article in bullish_stories[:4]:
                    title = self.truncate_text(article.get('title', ''), 65)
                    source = article.get('source', 'Unknown')
                    message += f"• {title} *({source})*\n"
                message += "\n"

            # Bearish stories
            bearish_stories = sentiment_groups['BEARISH'] + sentiment_groups['SLIGHTLY_BEARISH']
            if bearish_stories:
                message += "🐻 **BEARISH TRENDS**\n"
                for article in bearish_stories[:4]:
                    title = self.truncate_text(article.get('title', ''), 65)
                    source = article.get('source', 'Unknown')
                    message += f"• {title} *({source})*\n"
                message += "\n"

            # Neutral stories
            if sentiment_groups['NEUTRAL']:
                message += "⚠️ **NEUTRAL DEVELOPMENTS**\n"
                for article in sentiment_groups['NEUTRAL'][:3]:
                    title = self.truncate_text(article.get('title', ''), 65)
                    source = article.get('source', 'Unknown')
                    message += f"• {title} *({source})*\n"

            message += "\n💡 Use /today for detailed analysis!"

            return message

        except Exception as e:
            logger.error(f"Error formatting trending news: {e}")
            return "📊 **TRENDING NEWS**\n\nError loading trending news. Please try again!"

    def format_welcome_message(self):
        """Welcome message for new users"""
        return (
            "👋 **Welcome to Crypto Investor Sidekick!**\n\n"
            "🤖 I'm your AI-powered crypto news assistant. Here's what I do:\n\n"

            "**📊 Core Features:**\n"
            "• Daily top 10 crypto news summaries\n"
            "• 🚀🐻 Smart sentiment analysis\n"
            "• 💡 Investment insights for each story\n"
            "• 🕘 Automated delivery at 9 AM UTC\n"
            "• 📰 Multiple trusted news sources\n\n"

            "**⚡ Quick Commands:**\n"
            "/today - Get today's digest (instant)\n"
            "/hot - Trending news by sentiment\n"
            "/subscribe - Enable daily auto-delivery\n"
            "/settings - Manage your preferences\n"
            "/help - Full command reference\n\n"

            "**🚀 Ready to get started?**\n"
            "Try /today to see your first crypto digest!\n\n"

            "*Powered by advanced sentiment analysis & multi-source aggregation*"
        )

    def format_help_message(self):
        """Comprehensive help message"""
        return (
            "🤖 **CRYPTO INVESTOR SIDEKICK - HELP**\n\n"

            "**📊 News Commands:**\n"
            "/today - Get today's top 10 crypto digest\n"
            "/hot - Trending news organized by sentiment\n\n"

            "**⚙️ Settings & Subscriptions:**\n"
            "/subscribe - Enable daily 9 AM UTC digests\n"
            "/unsubscribe - Disable daily digests\n"
            "/settings - View current preferences\n\n"

            "**ℹ️ Information:**\n"
            "/start - Show welcome message\n"
            "/help - Display this help menu\n\n"

            "**🎯 How It Works:**\n"
            "• I monitor 5+ trusted crypto news sources\n"
            "• AI analyzes sentiment: 🚀 Bullish, 🐻 Bearish\n"
            "• Each story includes investment insights\n"
            "• Smart deduplication removes repetitive news\n"
            "• Content ranked by relevance & importance\n\n"

            "**📰 News Sources:**\n"
            "CoinDesk • CoinTelegraph • Decrypt • CoinMarketCap • CryptoNews\n\n"

            "**🔔 Daily Digest:**\n"
            "Subscribe to receive automated daily summaries at 9 AM UTC with the most important crypto developments!\n\n"

            "**💡 Tips:**\n"
            "• Use /today for instant updates\n"
            "• Check /hot for market sentiment trends\n"
            "• Subscribe for consistent daily insights\n\n"

            "*Questions? Just ask or try any command above!*"
        )

    def format_settings_message(self, user_subscribed=True):
        """Settings and preferences message"""
        subscription_status = "✅ Enabled" if user_subscribed else "❌ Disabled"

        return (
            "⚙️ **YOUR SETTINGS**\n\n"

            "**📅 Daily Digest:**\n"
            f"Status: {subscription_status}\n"
            "Time: 9:00 AM UTC daily\n"
            "Content: Top 10 crypto stories + insights\n\n"

            "**📊 News Sources:**\n"
            "• CoinDesk RSS\n"
            "• CoinTelegraph RSS\n"
            "• Decrypt RSS\n"
            "• CoinMarketCap Headlines\n"
            "• CryptoNews Feed\n\n"

            "**🎯 Content Analysis:**\n"
            "• AI sentiment analysis (VADER)\n"
            "• Investment insight generation\n"
            "• Smart duplicate removal\n"
            "• Relevance-based ranking\n\n"

            "**🔧 Available Actions:**\n"
            "/subscribe - Enable daily digests\n"
            "/unsubscribe - Disable daily digests\n"
            "/today - Get instant digest\n"
            "/hot - View trending sentiment\n\n"

            "*More customization options coming soon!*"
        )

    def format_no_news_message(self):
        """Message when no news is available"""
        return (
            "📈 **CRYPTO DIGEST**\n\n"
            "🤔 No news articles available right now.\n\n"
            "This could mean:\n"
            "• News sources are temporarily unavailable\n"
            "• Very quiet news day in crypto markets\n"
            "• Technical issue fetching latest updates\n\n"
            "💡 **Try again in a few minutes or use:**\n"
            "/hot - Check for trending stories\n"
            "/settings - Verify your preferences"
        )

    def format_error_message(self):
        """Generic error message"""
        return (
            "❌ **Oops! Something went wrong**\n\n"
            "I encountered an error while preparing your digest.\n\n"
            "**Please try:**\n"
            "• Wait a moment and try again\n"
            "• Use /hot for trending news\n"
            "• Contact support if problem persists\n\n"
            "I'm working to fix this quickly! 🔧"
        )

    def format_subscription_success(self):
        """Subscription success message"""
        return (
            "✅ **Successfully Subscribed!**\n\n"
            "🎉 You'll now receive daily crypto digests at **9:00 AM UTC**.\n\n"
            "**What you'll get:**\n"
            "• Top 10 most important crypto stories\n"
            "• AI sentiment analysis for each story\n"
            "• Investment insights and implications\n"
            "• Curated from 5+ trusted sources\n\n"
            "**Want your digest now?** Use /today\n\n"
            "*You can unsubscribe anytime with /unsubscribe*"
        )

    def format_unsubscribe_success(self):
        """Unsubscription success message"""
        return (
            "❌ **Successfully Unsubscribed**\n\n"
            "You won't receive daily digests anymore.\n\n"
            "**You can still:**\n"
            "• Get instant news with /today\n"
            "• Check trending sentiment with /hot\n"
            "• Re-subscribe anytime with /subscribe\n\n"
            "Thanks for using Crypto Investor Sidekick! 👋"
        )