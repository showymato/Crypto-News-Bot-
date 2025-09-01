import asyncio
import logging
import os
import sys
from datetime import datetime

from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
from telegram.error import TelegramError, NetworkError, TimedOut

from config import TELEGRAM_BOT_TOKEN, PORT, RENDER_URL
from database import UserDatabase
from news_aggregator import NewsAggregator
from ai_processor import AIProcessor
from digest_formatter import DigestFormatter
from scheduler import DigestScheduler

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Reduce noise from external libraries
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.WARNING)
logging.getLogger('apscheduler').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

class CryptoNewsBot:
    def __init__(self):
        logger.info("🚀 Initializing Crypto News Bot V2.0...")

        try:
            self.db = UserDatabase()
            self.news_aggregator = NewsAggregator()
            self.ai_processor = AIProcessor()
            self.formatter = DigestFormatter()
            self.scheduler = None

            logger.info("✅ All components initialized successfully")

        except Exception as e:
            logger.error(f"❌ Failed to initialize bot components: {e}")
            raise

    async def process_news_articles(self, articles):
        """Process articles with AI analysis"""
        if not articles:
            return []

        processed = []

        logger.info(f"Processing {len(articles)} articles with AI...")

        for i, article in enumerate(articles, 1):
            try:
                processed_article = self.ai_processor.process_article(article)

                if processed_article:
                    processed.append(processed_article)

                    # Progress logging for large batches
                    if i % 10 == 0:
                        logger.info(f"Processed {i}/{len(articles)} articles")

            except Exception as e:
                logger.error(f"Error processing article {i}: {e}")
                continue

        logger.info(f"✅ Successfully processed {len(processed)} articles")
        return processed

    async def get_daily_digest(self):
        """Generate the daily news digest"""
        try:
            start_time = datetime.now()
            logger.info("📰 Generating daily digest...")

            # Fetch latest news
            articles = self.news_aggregator.get_latest_news()

            if not articles:
                logger.warning("No articles fetched from news sources")
                return self.formatter.format_no_news_message()

            logger.info(f"Fetched {len(articles)} articles from news sources")

            # Process with AI
            processed_articles = await self.process_news_articles(articles)

            if not processed_articles:
                logger.warning("No articles successfully processed")
                return self.formatter.format_no_news_message()

            # Format digest
            digest_message = self.formatter.format_daily_digest(processed_articles)

            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Daily digest generated in {duration:.1f}s")

            return digest_message

        except Exception as e:
            logger.error(f"Error generating daily digest: {e}")
            return self.formatter.format_error_message()

    async def get_trending_news(self):
        """Get trending news by sentiment"""
        try:
            logger.info("📊 Generating trending news...")

            articles = self.news_aggregator.get_latest_news()
            processed_articles = await self.process_news_articles(articles)

            return self.formatter.format_trending_news(processed_articles)

        except Exception as e:
            logger.error(f"Error generating trending news: {e}")
            return "❌ Sorry, couldn't fetch trending news right now. Please try again!"

# Initialize bot instance
try:
    bot_instance = CryptoNewsBot()
except Exception as e:
    logger.error(f"Failed to initialize bot: {e}")
    sys.exit(1)

# Command Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    try:
        user = update.effective_user
        logger.info(f"👋 New user started: {user.id} (@{user.username})")

        # Add user to database
        bot_instance.db.add_user(
            user.id, 
            user.username, 
            user.first_name, 
            user.last_name
        )

        # Send welcome message
        welcome_msg = bot_instance.formatter.format_welcome_message()

        await update.message.reply_text(
            welcome_msg,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )

    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await update.message.reply_text(
            "👋 Welcome! I'm your crypto news assistant. Use /help to see what I can do!"
        )

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /today command"""
    user_id = update.effective_user.id

    try:
        # Update user activity
        bot_instance.db.update_last_active(user_id)

        # Send loading message
        loading_msg = await update.message.reply_text("📊 Generating your crypto digest... Please wait!")

        # Generate digest
        digest = await bot_instance.get_daily_digest()

        # Split long messages if needed
        if len(digest) > 4000:
            # Split into parts
            parts = []
            current_part = ""

            for line in digest.split('\n\n'):
                if len(current_part + line + '\n\n') > 4000:
                    if current_part:
                        parts.append(current_part.strip())
                    current_part = line + '\n\n'
                else:
                    current_part += line + '\n\n'

            if current_part:
                parts.append(current_part.strip())

            # Delete loading message
            await loading_msg.delete()

            # Send parts
            for i, part in enumerate(parts):
                await update.message.reply_text(
                    part,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True
                )

                # Small delay between parts
                if i < len(parts) - 1:
                    await asyncio.sleep(1)
        else:
            # Delete loading message and send digest
            await loading_msg.delete()
            await update.message.reply_text(
                digest,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )

        logger.info(f"📰 Digest sent to user {user_id}")

    except Exception as e:
        logger.error(f"Error in today command for user {user_id}: {e}")
        try:
            await loading_msg.delete()
        except:
            pass

        await update.message.reply_text(
            "❌ Sorry, I encountered an error generating your digest. Please try again in a moment!"
        )

async def hot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /hot command"""
    user_id = update.effective_user.id

    try:
        bot_instance.db.update_last_active(user_id)

        loading_msg = await update.message.reply_text("🔥 Analyzing trending sentiment...")

        trending = await bot_instance.get_trending_news()

        await loading_msg.delete()
        await update.message.reply_text(
            trending,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )

        logger.info(f"📊 Trending news sent to user {user_id}")

    except Exception as e:
        logger.error(f"Error in hot command for user {user_id}: {e}")
        try:
            await loading_msg.delete()
        except:
            pass

        await update.message.reply_text(
            "❌ Sorry, couldn't fetch trending news right now!"
        )

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /settings command"""
    user_id = update.effective_user.id

    try:
        bot_instance.db.update_last_active(user_id)

        # Check subscription status (simplified - assume subscribed by default)
        settings_msg = bot_instance.formatter.format_settings_message(True)

        await update.message.reply_text(
            settings_msg,
            parse_mode=ParseMode.MARKDOWN
        )

    except Exception as e:
        logger.error(f"Error in settings command for user {user_id}: {e}")
        await update.message.reply_text(
            "⚙️ Settings temporarily unavailable. Please try again!"
        )

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /subscribe command"""
    user_id = update.effective_user.id

    try:
        success = bot_instance.db.update_subscription(user_id, True)

        if success:
            message = bot_instance.formatter.format_subscription_success()
        else:
            # User not in database, add them
            user = update.effective_user
            bot_instance.db.add_user(user.id, user.username, user.first_name, user.last_name)
            message = bot_instance.formatter.format_subscription_success()

        await update.message.reply_text(
            message,
            parse_mode=ParseMode.MARKDOWN
        )

        logger.info(f"✅ User {user_id} subscribed to daily digest")

    except Exception as e:
        logger.error(f"Error subscribing user {user_id}: {e}")
        await update.message.reply_text(
            "❌ Sorry, there was an error with your subscription. Please try again!"
        )

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /unsubscribe command"""
    user_id = update.effective_user.id

    try:
        bot_instance.db.update_subscription(user_id, False)

        message = bot_instance.formatter.format_unsubscribe_success()

        await update.message.reply_text(
            message,
            parse_mode=ParseMode.MARKDOWN
        )

        logger.info(f"❌ User {user_id} unsubscribed from daily digest")

    except Exception as e:
        logger.error(f"Error unsubscribing user {user_id}: {e}")
        await update.message.reply_text(
            "❌ Sorry, there was an error. Please try again!"
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    try:
        bot_instance.db.update_last_active(update.effective_user.id)

        help_msg = bot_instance.formatter.format_help_message()

        await update.message.reply_text(
            help_msg,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )

    except Exception as e:
        logger.error(f"Error in help command: {e}")
        await update.message.reply_text(
            "ℹ️ Help is temporarily unavailable. Try /today for news or /settings for preferences!"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular text messages"""
    try:
        message_text = update.message.text.lower() if update.message.text else ""
        user_id = update.effective_user.id

        bot_instance.db.update_last_active(user_id)

        # Smart responses based on message content
        if any(word in message_text for word in ['hi', 'hello', 'hey', 'start', 'help']):
            response = (
                "👋 Hi there! I'm your crypto news assistant.\n\n"
                "**Try these commands:**\n"
                "• /today - Get today's digest\n"
                "• /hot - Trending sentiment\n"
                "• /help - Full command list"
            )
        elif any(word in message_text for word in ['news', 'crypto', 'bitcoin', 'ethereum', 'digest']):
            response = (
                "📰 **Want crypto news?**\n\n"
                "• /today - Today's top 10 digest\n"
                "• /hot - Trending by sentiment\n"
                "• /subscribe - Daily auto-delivery"
            )
        elif any(word in message_text for word in ['subscribe', 'daily', 'automatic']):
            response = (
                "🔔 **Daily Digest Subscription:**\n\n"
                "Use /subscribe to enable daily crypto news at 9 AM UTC!\n"
                "Or try /today for instant news."
            )
        else:
            response = (
                "🤖 I'm here to help with crypto news!\n\n"
                "**Popular commands:**\n"
                "• /today - Latest crypto digest\n"
                "• /hot - Trending news\n"
                "• /help - All commands"
            )

        await update.message.reply_text(
            response,
            parse_mode=ParseMode.MARKDOWN
        )

    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await update.message.reply_text(
            "🤖 Use /help to see what I can do, or /today for crypto news!"
        )

async def set_bot_commands(application):
    """Set bot command menu"""
    commands = [
        BotCommand("today", "📊 Get today's crypto digest"),
        BotCommand("hot", "🔥 Trending news by sentiment"),
        BotCommand("subscribe", "🔔 Enable daily digests"),
        BotCommand("settings", "⚙️ Manage preferences"),
        BotCommand("help", "ℹ️ Show help menu"),
    ]

    try:
        await application.bot.set_my_commands(commands)
        logger.info("✅ Bot commands menu set successfully")
    except Exception as e:
        logger.error(f"Failed to set bot commands: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")

    # Try to inform user about the error
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ Sorry, I encountered an error. Please try again or use /help for assistance."
            )
        except:
            pass

def main():
    """Main function to run the bot"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN not found in environment variables!")
        sys.exit(1)

    logger.info(f"🤖 Starting Crypto News Bot V2.0...")
    logger.info(f"🔗 Webhook URL: {RENDER_URL}")
    logger.info(f"🌐 Port: {PORT}")

    try:
        # Create application
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("today", today))
        application.add_handler(CommandHandler("hot", hot))
        application.add_handler(CommandHandler("settings", settings))
        application.add_handler(CommandHandler("subscribe", subscribe))
        application.add_handler(CommandHandler("unsubscribe", unsubscribe))
        application.add_handler(CommandHandler("help", help_command))

        # Handle regular messages
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        # Error handler
        application.add_error_handler(error_handler)

        # Set bot commands menu
        application.post_init = set_bot_commands

        # Initialize scheduler
        try:
            bot_instance.scheduler = DigestScheduler(application.bot, bot_instance)
            bot_instance.scheduler.start()
            logger.info("✅ Scheduler started successfully")
        except Exception as e:
            logger.error(f"❌ Failed to start scheduler: {e}")

        # Run bot
        if RENDER_URL and "render" in RENDER_URL:
            # Production: Use webhook on Render
            logger.info("🚀 Starting bot with webhook (Production)")
            application.run_webhook(
                listen="0.0.0.0",
                port=PORT,
                webhook_url=f"{RENDER_URL}/",
                allowed_updates=Update.ALL_TYPES
            )
        else:
            # Development: Use polling
            logger.info("🚀 Starting bot with polling (Development)")
            application.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()