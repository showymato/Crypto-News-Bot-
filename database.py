import sqlite3
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class UserDatabase:
    def __init__(self, db_path='users.db'):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Initialize database tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    subscribed BOOLEAN DEFAULT True,
                    digest_time TEXT DEFAULT '09:00',
                    timezone TEXT DEFAULT 'UTC',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create index for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_subscribed 
                ON users(subscribed) WHERE subscribed = True
            ''')

            conn.commit()
            logger.info("Database initialized successfully")

        except Exception as e:
            logger.error(f"Database initialization error: {e}")
        finally:
            conn.close()

    def add_user(self, user_id, username=None, first_name=None, last_name=None):
        """Add or update user in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO users 
                (user_id, username, first_name, last_name, subscribed, last_active)
                VALUES (?, ?, ?, ?, True, CURRENT_TIMESTAMP)
            ''', (user_id, username, first_name, last_name))

            conn.commit()
            logger.info(f"User {user_id} added/updated successfully")

        except Exception as e:
            logger.error(f"Error adding user {user_id}: {e}")
        finally:
            conn.close()

    def get_subscribed_users(self):
        """Get all subscribed user IDs"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT user_id FROM users WHERE subscribed = True')
            users = cursor.fetchall()

            user_ids = [user[0] for user in users]
            logger.info(f"Retrieved {len(user_ids)} subscribed users")
            return user_ids

        except Exception as e:
            logger.error(f"Error getting subscribed users: {e}")
            return []
        finally:
            conn.close()

    def update_subscription(self, user_id, subscribed):
        """Update user subscription status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE users 
                SET subscribed = ?, last_active = CURRENT_TIMESTAMP 
                WHERE user_id = ?
            ''', (subscribed, user_id))

            conn.commit()

            if cursor.rowcount > 0:
                logger.info(f"User {user_id} subscription updated to {subscribed}")
                return True
            else:
                logger.warning(f"User {user_id} not found in database")
                return False

        except Exception as e:
            logger.error(f"Error updating subscription for user {user_id}: {e}")
            return False
        finally:
            conn.close()

    def get_user_stats(self):
        """Get user statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM users')
            total_users = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM users WHERE subscribed = True')
            subscribed_users = cursor.fetchone()[0]

            return {
                'total_users': total_users,
                'subscribed_users': subscribed_users,
                'unsubscribed_users': total_users - subscribed_users
            }

        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {'total_users': 0, 'subscribed_users': 0, 'unsubscribed_users': 0}
        finally:
            conn.close()

    def update_last_active(self, user_id):
        """Update user's last active timestamp"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE users 
                SET last_active = CURRENT_TIMESTAMP 
                WHERE user_id = ?
            ''', (user_id,))

            conn.commit()

        except Exception as e:
            logger.error(f"Error updating last active for user {user_id}: {e}")
        finally:
            conn.close()