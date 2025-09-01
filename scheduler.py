from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio
import logging
from datetime import datetime
from config import DIGEST_TIME_HOUR, DIGEST_TIME_MINUTE

logger = logging.getLogger(__name__)

class DigestScheduler:
    def __init__(self, bot, news_processor):
        self.bot = bot
        self.news_processor = news_processor
        self.scheduler = AsyncIOScheduler()
        self.is_running = False

    async def send_daily_digest(self):
        """Send daily digest to all subscribed users"""
        try:
            start_time = datetime.now()
            logger.info("Starting daily digest generation...")

            # Generate digest
            digest_message = await self.news_processor.get_daily_digest()

            if not digest_message:
                logger.error("No digest message generated")
                return

            # Get subscribed users
            from database import UserDatabase
            db = UserDatabase()
            users = db.get_subscribed_users()

            if not users:
                logger.info("No subscribed users found")
                return

            logger.info(f"Sending daily digest to {len(users)} users...")

            # Send to all users with error handling
            success_count = 0
            error_count = 0

            for user_id in users:
                try:
                    await self.bot.send_message(
                        chat_id=user_id,
                        text=digest_message,
                        parse_mode='Markdown',
                        disable_web_page_preview=True
                    )
                    success_count += 1

                    # Rate limiting - small delay between messages
                    await asyncio.sleep(0.2)

                except Exception as e:
                    error_count += 1
                    logger.error(f"Failed to send digest to user {user_id}: {e}")

                    # If user blocked bot, remove from subscriptions
                    if "bot was blocked" in str(e).lower() or "chat not found" in str(e).lower():
                        try:
                            db.update_subscription(user_id, False)
                            logger.info(f"Unsubscribed inactive user {user_id}")
                        except:
                            pass

            # Log results
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            logger.info(f"Daily digest completed in {duration:.1f}s - Success: {success_count}, Errors: {error_count}")

            # Optional: Send admin notification if many errors
            if error_count > success_count * 0.1:  # More than 10% errors
                logger.warning(f"High error rate in daily digest: {error_count}/{len(users)}")

        except Exception as e:
            logger.error(f"Critical error in daily digest: {e}")

    def start(self):
        """Start the scheduler"""
        try:
            if self.is_running:
                logger.warning("Scheduler already running")
                return

            # Schedule daily digest
            self.scheduler.add_job(
                self.send_daily_digest,
                CronTrigger(
                    hour=DIGEST_TIME_HOUR, 
                    minute=DIGEST_TIME_MINUTE,
                    timezone='UTC'  # Always use UTC
                ),
                id='daily_digest',
                max_instances=1,  # Prevent overlapping executions
                coalesce=True,    # Combine missed executions
                misfire_grace_time=900  # Allow 15 minutes grace time
            )

            self.scheduler.start()
            self.is_running = True

            logger.info(f"📅 Scheduler started - Daily digest at {DIGEST_TIME_HOUR:02d}:{DIGEST_TIME_MINUTE:02d} UTC")

        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")

    def stop(self):
        """Stop the scheduler"""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown(wait=True)
            self.is_running = False
            logger.info("Scheduler stopped")

        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")

    def get_next_run_time(self):
        """Get next scheduled run time"""
        try:
            job = self.scheduler.get_job('daily_digest')
            if job:
                return job.next_run_time
            return None

        except Exception as e:
            logger.error(f"Error getting next run time: {e}")
            return None

    def is_scheduler_running(self):
        """Check if scheduler is running"""
        return self.is_running and self.scheduler.running

    async def test_digest(self, chat_id):
        """Test digest generation and send to specific chat (for debugging)"""
        try:
            logger.info(f"Testing digest generation for chat {chat_id}")

            # Generate test digest
            digest_message = await self.news_processor.get_daily_digest()

            if digest_message:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text="🧪 **TEST DIGEST**\n\n" + digest_message,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
                logger.info("Test digest sent successfully")
            else:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text="❌ Test digest failed - no content generated"
                )

        except Exception as e:
            logger.error(f"Test digest error: {e}")
            try:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ Test digest error: {str(e)}"
                )
            except:
                pass