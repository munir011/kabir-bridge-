import json
import os
import logging
from datetime import datetime
import sqlite3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        # Get database path from environment variable or use default
        db_path = os.getenv('DB_FILE', 'data/smm_bot.db')
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        
        abs_path = os.path.abspath(db_path)
        logger.info(f"Using database at: {abs_path}")
        
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()
        self.migrate_database()
    
    def migrate_database(self):
        """Handle database migrations"""
        cursor = self.conn.cursor()
        try:
            # Check if currency_preference column exists
            cursor.execute('PRAGMA table_info(users)')
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'currency_preference' not in columns:
                logger.info("Adding currency_preference column to users table")
                cursor.execute('ALTER TABLE users ADD COLUMN currency_preference TEXT DEFAULT "USD"')
                self.conn.commit()
                logger.info("Successfully added currency_preference column")
            
            # Check if service_price_overrides table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='service_price_overrides'")
            if not cursor.fetchone():
                logger.info("Creating service_price_overrides table")
                cursor.execute('''
                    CREATE TABLE service_price_overrides (
                        service_id TEXT PRIMARY KEY,
                        original_price REAL,
                        custom_price REAL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_by INTEGER
                    )
                ''')
                self.conn.commit()
                logger.info("Successfully created service_price_overrides table")
                
            # Check if language column exists
            if 'language' not in columns:
                logger.info("Adding language column to users table")
                cursor.execute('ALTER TABLE users ADD COLUMN language TEXT DEFAULT "en"')
                self.conn.commit()
                logger.info("Successfully added language column")
                
            # Check if referred_by column exists
            if 'referred_by' not in columns:
                logger.info("Adding referred_by column to users table")
                cursor.execute('ALTER TABLE users ADD COLUMN referred_by INTEGER DEFAULT NULL')
                self.conn.commit()
                logger.info("Successfully added referred_by column")
                
            # Check if admin_has_replied column exists
            if 'admin_has_replied' not in columns:
                logger.info("Adding admin_has_replied column to users table")
                cursor.execute('ALTER TABLE users ADD COLUMN admin_has_replied INTEGER DEFAULT 0')
                self.conn.commit()
                logger.info("Successfully added admin_has_replied column")
                
            # Check orders table structure
            cursor.execute('PRAGMA table_info(orders)')
            order_columns = [column[1] for column in cursor.fetchall()]
            
            # If orders table exists but has wrong structure, recreate it
            if order_columns and 'order_id' not in order_columns:
                logger.info("Recreating orders table with correct structure")
                cursor.execute('DROP TABLE IF EXISTS orders')
                cursor.execute('''
                    CREATE TABLE orders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        order_id TEXT,
                        service_id TEXT,
                        service_name TEXT,
                        quantity INTEGER,
                        link TEXT,
                        price REAL,
                        status TEXT DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                ''')
                self.conn.commit()
                logger.info("Successfully recreated orders table")
                
            # Check if referrals table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='referrals'")
            if not cursor.fetchone():
                logger.info("Creating referrals table")
                cursor.execute('''
                    CREATE TABLE referrals (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        referrer_id INTEGER,
                        referred_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (referrer_id) REFERENCES users (user_id),
                        FOREIGN KEY (referred_id) REFERENCES users (user_id)
                    )
                ''')
                self.conn.commit()
                logger.info("Successfully created referrals table")
            
            # Check if referral_bonuses table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='referral_bonuses'")
            if not cursor.fetchone():
                logger.info("Creating referral_bonuses table")
                cursor.execute('''
                    CREATE TABLE referral_bonuses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        referral_count INTEGER,
                        bonus_amount REAL,
                        status TEXT DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        processed_at TIMESTAMP,
                        processed_by INTEGER,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                ''')
                self.conn.commit()
                logger.info("Successfully created referral_bonuses table")
                
            # Check if settings table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'")
            if not cursor.fetchone():
                logger.info("Creating settings table")
                cursor.execute('''
                    CREATE TABLE settings (
                        key TEXT PRIMARY KEY,
                        value TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                # Insert default settings
                cursor.execute("INSERT INTO settings (key, value) VALUES ('referral_threshold', '50')")
                cursor.execute("INSERT INTO settings (key, value) VALUES ('bonus_amount', '50.0')")
                self.conn.commit()
                logger.info("Successfully created settings table with default values")
                
        except Exception as e:
            logger.error(f"Error during database migration: {e}")
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Create users table with balance
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                balance REAL DEFAULT 0.0,
                last_activity TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                currency_preference TEXT DEFAULT 'USD',
                language TEXT DEFAULT 'en',
                referred_by INTEGER DEFAULT NULL
            )
        ''')
        
        # Create service price overrides table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS service_price_overrides (
                service_id TEXT PRIMARY KEY,
                original_price REAL,
                custom_price REAL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by INTEGER
            )
        ''')
        
        # Create balance transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS balance_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                type TEXT,  -- 'credit' or 'debit'
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Create orders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                order_id TEXT,
                service_id TEXT,
                service_name TEXT,
                quantity INTEGER,
                link TEXT,
                price REAL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Create referrals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER,
                referred_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (referrer_id) REFERENCES users (user_id),
                FOREIGN KEY (referred_id) REFERENCES users (user_id)
            )
        ''')
        
        self.conn.commit()
    
    def get_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            # Create new user if doesn't exist
            cursor.execute(
                'INSERT INTO users (user_id, balance, last_activity, currency_preference, language, referred_by) VALUES (?, 0.0, ?, ?, ?, NULL)',
                (user_id, datetime.now(), 'USD', 'en')
            )
            self.conn.commit()
            return self.get_user(user_id)
        
        return {
            'user_id': user[0],
            'username': user[1],
            'first_name': user[2],
            'last_name': user[3],
            'balance': user[4],
            'last_activity': user[5],
            'created_at': user[6],
            'currency_preference': user[7] if len(user) > 7 else 'USD',
            'language': user[8] if len(user) > 8 else 'en',
            'referred_by': user[9] if len(user) > 9 else None
        }
    
    def update_user_activity(self, user_id):
        """Update user's last activity timestamp and ensure user exists in database"""
        # First, make sure the user exists
        self.get_user(user_id)
        
        # Then update the activity timestamp
        cursor = self.conn.cursor()
        cursor.execute(
            'UPDATE users SET last_activity = ? WHERE user_id = ?',
            (datetime.now(), user_id)
        )
        self.conn.commit()
    
    def get_balance(self, user_id):
        """Get user's balance"""
        # First, make sure the user exists
        user = self.get_user(user_id)
        
        # Return the balance from the user object
        return user.get('balance', 0.0)
    
    def get_currency_preference(self, user_id):
        """Get user's currency preference"""
        # First, make sure the user exists
        user = self.get_user(user_id)
        
        # Return the currency preference from the user object
        return user.get('currency_preference', 'USD')
    
    def set_currency_preference(self, user_id, currency):
        """Set user's currency preference"""
        cursor = self.conn.cursor()
        cursor.execute(
            'UPDATE users SET currency_preference = ? WHERE user_id = ?',
            (currency, user_id)
        )
        self.conn.commit()
        return True
    
    def add_balance(self, user_id, amount, description="Admin balance addition"):
        cursor = self.conn.cursor()
        try:
            # Start transaction
            cursor.execute('BEGIN TRANSACTION')
            
            # Update user balance
            cursor.execute(
                'UPDATE users SET balance = balance + ? WHERE user_id = ?',
                (amount, user_id)
            )
            
            # Record transaction
            cursor.execute(
                'INSERT INTO balance_transactions (user_id, amount, type, description) VALUES (?, ?, ?, ?)',
                (user_id, amount, 'credit', description)
            )
            
            # Commit transaction
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding balance: {e}")
            cursor.execute('ROLLBACK')
            return False
    
    def deduct_balance(self, user_id, amount, description="Order payment"):
        cursor = self.conn.cursor()
        try:
            # Start transaction
            cursor.execute('BEGIN TRANSACTION')
            
            # Check if user has sufficient balance
            current_balance = self.get_balance(user_id)
            if current_balance < amount:
                cursor.execute('ROLLBACK')
                return False
            
            # Update user balance
            cursor.execute(
                'UPDATE users SET balance = balance - ? WHERE user_id = ?',
                (amount, user_id)
            )
            
            # Record transaction
            cursor.execute(
                'INSERT INTO balance_transactions (user_id, amount, type, description) VALUES (?, ?, ?, ?)',
                (user_id, amount, 'debit', description)
            )
            
            # Commit transaction
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error deducting balance: {e}")
            cursor.execute('ROLLBACK')
            return False
    
    def get_transactions(self, user_id, limit=10):
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT * FROM balance_transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT ?',
            (user_id, limit)
        )
        transactions = cursor.fetchall()
        return [{
            'id': t[0],
            'user_id': t[1],
            'amount': t[2],
            'type': t[3],
            'description': t[4],
            'created_at': t[5]
        } for t in transactions]
    
    def add_order(self, user_id, order_id, service_id, service_name, quantity, link, price):
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                '''INSERT INTO orders 
                   (user_id, order_id, service_id, service_name, quantity, link, price)
                   VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (user_id, order_id, service_id, service_name, quantity, link, price)
            )
            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error adding order: {e}")
            return None
    
    def get_user_orders(self, user_id, limit=5):
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC LIMIT ?',
            (user_id, limit)
        )
        orders = cursor.fetchall()
        return [{
            'id': o[2],  # order_id from the API
            'user_id': o[1],
            'service_id': o[3],
            'service_name': o[4],
            'quantity': o[5],
            'link': o[6],
            'price': o[7],
            'status': o[8],
            'created_at': o[9]
        } for o in orders] if orders else []
    
    def get_order_by_id(self, order_id):
        """Get order details by order_id"""
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT * FROM orders WHERE order_id = ? LIMIT 1',
            (order_id,)
        )
        order = cursor.fetchone()
        if order:
            return {
                'id': order[2],  # order_id from the API
                'user_id': order[1],
                'service_id': order[3],
                'service_name': order[4],
                'quantity': order[5],
                'link': order[6],
                'price': order[7],
                'status': order[8],
                'created_at': order[9]
            }
        return None
    
    def is_admin(self, user_id):
        """Check if a user is an admin"""
        admin_id = os.getenv("ADMIN_USER_ID")
        return str(user_id) == admin_id
    
    def get_language(self, user_id):
        """Get user's language preference"""
        # First, make sure the user exists
        user = self.get_user(user_id)
        
        # Return the language from the user object
        return user.get('language', 'en')
    
    def set_language(self, user_id, language):
        """Set user's language preference"""
        cursor = self.conn.cursor()
        cursor.execute(
            'UPDATE users SET language = ? WHERE user_id = ?',
            (language, user_id)
        )
        self.conn.commit()
        return True

    def update_user_data(self, user_id, data_dict):
        """Update user data with key-value pairs from data_dict"""
        if not data_dict:
            return False
            
        cursor = self.conn.cursor()
        try:
            # Get column names from users table
            cursor.execute('PRAGMA table_info(users)')
            valid_columns = [column[1] for column in cursor.fetchall()]
            
            # Filter out invalid keys
            valid_data = {k: v for k, v in data_dict.items() if k in valid_columns}
            
            if not valid_data:
                logger.warning(f"No valid columns to update for user {user_id}")
                return False
                
            # Build the SQL query
            set_clause = ', '.join([f"{key} = ?" for key in valid_data.keys()])
            values = list(valid_data.values())
            values.append(user_id)
            
            # Execute the update
            cursor.execute(
                f'UPDATE users SET {set_clause} WHERE user_id = ?',
                values
            )
            self.conn.commit()
            logger.info(f"Updated user data for user {user_id}: {valid_data}")
            return True
        except Exception as e:
            logger.error(f"Error updating user data: {e}")
            return False

    # Add referral methods
    def add_referral(self, referrer_id, referred_id):
        """Record a new referral"""
        cursor = self.conn.cursor()
        try:
            # Check if the referred user already has a referrer
            user = self.get_user(referred_id)
            if user.get('referred_by'):
                logger.info(f"User {referred_id} already has a referrer: {user.get('referred_by')}")
                return False
                
            # Start transaction
            cursor.execute('BEGIN TRANSACTION')
            
            # Update the referred user's record
            cursor.execute(
                'UPDATE users SET referred_by = ? WHERE user_id = ?',
                (referrer_id, referred_id)
            )
            
            # Add entry to referrals table
            cursor.execute(
                'INSERT INTO referrals (referrer_id, referred_id) VALUES (?, ?)',
                (referrer_id, referred_id)
            )
            
            # Commit transaction
            self.conn.commit()
            logger.info(f"Successfully recorded referral: {referrer_id} referred {referred_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding referral: {e}")
            cursor.execute('ROLLBACK')
            return False
    
    def get_referrals(self, user_id):
        """Get list of users referred by the given user"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT u.user_id, u.username, u.first_name, u.last_name, r.created_at
            FROM referrals r
            JOIN users u ON r.referred_id = u.user_id
            WHERE r.referrer_id = ?
            ORDER BY r.created_at DESC
        ''', (user_id,))
        
        referrals = []
        for row in cursor.fetchall():
            referrals.append({
                'user_id': row[0],
                'username': row[1],
                'first_name': row[2],
                'last_name': row[3],
                'created_at': row[4]
            })
        
        return referrals
    
    def get_referral_count(self, user_id):
        """Get the number of users referred by the given user"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM referrals WHERE referrer_id = ?', (user_id,))
        return cursor.fetchone()[0]
    
    def get_valid_referral_count(self, user_id):
        """Get the number of valid users (with username) referred by the given user"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) 
            FROM referrals r
            JOIN users u ON r.referred_id = u.user_id
            WHERE r.referrer_id = ? AND u.username IS NOT NULL AND u.username != ''
        ''', (user_id,))
        return cursor.fetchone()[0]
    
    def check_and_create_referral_bonus(self, user_id):
        """Check if user has reached the referral threshold and create a bonus if needed"""
        cursor = self.conn.cursor()
        try:
            # Get referral threshold from settings
            referral_threshold = self.get_setting("referral_threshold", 50)
            
            # Get total valid referral count (only users with username)
            referral_count = self.get_valid_referral_count(user_id)
            
            # Get already processed referrals
            cursor.execute('''
                SELECT SUM(referral_count)
                FROM referral_bonuses
                WHERE user_id = ?
            ''', (user_id,))
            
            processed_count = cursor.fetchone()[0] or 0
            
            # Calculate how many new bonuses to create
            new_bonus_count = (referral_count // referral_threshold) - (processed_count // referral_threshold)
            
            if new_bonus_count <= 0:
                # No new bonuses
                return None
            
            # Create new bonus
            bonus_amount = 50.0  # ETB 50 for each bonus
            
            # Start transaction
            cursor.execute('BEGIN TRANSACTION')
            
            # Insert bonus record
            cursor.execute('''
                INSERT INTO referral_bonuses
                (user_id, referral_count, bonus_amount, status)
                VALUES (?, ?, ?, 'pending')
            ''', (user_id, referral_threshold, bonus_amount))
            
            bonus_id = cursor.lastrowid
            
            # Commit transaction
            self.conn.commit()
            
            # Return bonus info
            return {
                'id': bonus_id,
                'user_id': user_id,
                'referral_count': referral_count,
                'processed_count': processed_count,
                'new_bonus_count': new_bonus_count,
                'bonus_amount': bonus_amount,
                'referral_threshold': referral_threshold
            }
        except Exception as e:
            logger.error(f"Error checking referral bonus: {e}")
            cursor.execute('ROLLBACK')
            return None
    
    def get_pending_referral_bonuses(self, user_id=None):
        """Get pending referral bonuses for a user or all users"""
        cursor = self.conn.cursor()
        
        if user_id:
            cursor.execute('''
                SELECT rb.id, rb.user_id, u.username, u.first_name, u.last_name, 
                       rb.referral_count, rb.bonus_amount, rb.status, rb.created_at
                FROM referral_bonuses rb
                JOIN users u ON rb.user_id = u.user_id
                WHERE rb.user_id = ? AND rb.status = 'pending'
                ORDER BY rb.created_at DESC
            ''', (user_id,))
        else:
            cursor.execute('''
                SELECT rb.id, rb.user_id, u.username, u.first_name, u.last_name, 
                       rb.referral_count, rb.bonus_amount, rb.status, rb.created_at
                FROM referral_bonuses rb
                JOIN users u ON rb.user_id = u.user_id
                WHERE rb.status = 'pending'
                ORDER BY rb.created_at DESC
            ''')
        
        bonuses = []
        for row in cursor.fetchall():
            bonuses.append({
                'id': row[0],
                'user_id': row[1],
                'username': row[2],
                'first_name': row[3],
                'last_name': row[4],
                'referral_count': row[5],
                'bonus_amount': row[6],
                'status': row[7],
                'created_at': row[8]
            })
        
        return bonuses
    
    def get_all_referral_bonuses(self, user_id):
        """Get all referral bonuses for a user"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, referral_count, bonus_amount, status, created_at, processed_at
            FROM referral_bonuses
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))
        
        bonuses = []
        for row in cursor.fetchall():
            bonuses.append({
                'id': row[0],
                'referral_count': row[1],
                'bonus_amount': row[2],
                'status': row[3],
                'created_at': row[4],
                'processed_at': row[5]
            })
        
        return bonuses
    
    def process_referral_bonus(self, bonus_id, status, admin_id):
        """Process a referral bonus (approve or decline)"""
        cursor = self.conn.cursor()
        try:
            # Start transaction
            cursor.execute('BEGIN TRANSACTION')
            
            # Get bonus details
            cursor.execute('SELECT user_id, bonus_amount FROM referral_bonuses WHERE id = ?', (bonus_id,))
            bonus = cursor.fetchone()
            
            if not bonus:
                cursor.execute('ROLLBACK')
                return False
            
            user_id, bonus_amount = bonus
            
            # Update bonus status
            cursor.execute('''
                UPDATE referral_bonuses 
                SET status = ?, processed_at = CURRENT_TIMESTAMP, processed_by = ? 
                WHERE id = ?
            ''', (status, admin_id, bonus_id))
            
            # If approved, add balance to user
            if status == 'approved':
                # Add balance
                cursor.execute('''
                    UPDATE users 
                    SET balance = balance + ? 
                    WHERE user_id = ?
                ''', (bonus_amount, user_id))
                
                # Add transaction record
                cursor.execute('''
                    INSERT INTO balance_transactions 
                    (user_id, amount, type, description) 
                    VALUES (?, ?, 'credit', 'Referral bonus for 50 referrals')
                ''', (user_id, bonus_amount))
            
            # Commit transaction
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error processing referral bonus: {e}")
            cursor.execute('ROLLBACK')
            return False

    def get_setting(self, key, default=None):
        """Get a setting value from the database"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        result = cursor.fetchone()
        
        if result:
            return result[0]
        return default
    
    def set_setting(self, key, value):
        """Set a setting value in the database"""
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)',
            (key, str(value), datetime.now())
        )
        self.conn.commit()
        return True
    
    def update_currency_rate(self, currency, rate):
        """Update the exchange rate for a currency"""
        # Store currency rates in the settings table with a prefix
        key = f"currency_rate_{currency}"
        return self.set_setting(key, rate)
    
    def get_currency_rate(self, currency, default=None):
        """Get the exchange rate for a currency"""
        # Get currency rate from settings table
        key = f"currency_rate_{currency}"
        rate_str = self.get_setting(key)
        
        if rate_str:
            try:
                return float(rate_str)
            except (ValueError, TypeError):
                return default
        return default
    
    def get_all_currency_rates(self):
        """Get all currency exchange rates"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT key, value FROM settings WHERE key LIKE ?', ('currency_rate_%',))
        results = cursor.fetchall()
        
        rates = {}
        for key, value in results:
            currency = key.replace('currency_rate_', '')
            try:
                rates[currency] = float(value)
            except (ValueError, TypeError):
                continue
        
        return rates

    # Add statistics methods
    def get_total_users(self):
        """Get the total number of users"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        return cursor.fetchone()[0]
    
    def get_active_users(self, days=7):
        """Get the number of active users in the last X days"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM users 
            WHERE last_activity >= datetime('now', ?) AND last_activity IS NOT NULL
        ''', (f'-{days} days',))
        return cursor.fetchone()[0]
    
    def get_total_orders(self):
        """Get the total number of orders"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM orders')
        return cursor.fetchone()[0]
    
    def get_recent_orders(self, days=7):
        """Get the number of orders in the last X days"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM orders 
            WHERE created_at >= datetime('now', ?)
        ''', (f'-{days} days',))
        return cursor.fetchone()[0]
    
    def get_all_users_list(self, limit=1000):
        """Get a list of all users with details"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT user_id, username, first_name, last_name, balance, last_activity, created_at
            FROM users
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))
        
        users = []
        for row in cursor.fetchall():
            users.append({
                'user_id': row[0],
                'username': row[1],
                'first_name': row[2],
                'last_name': row[3],
                'balance': row[4],
                'last_activity': row[5],
                'created_at': row[6]
            })
        
        return users
    
    def get_active_users_list(self, days=7, limit=1000):
        """Get a list of active users in the last X days"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT user_id, username, first_name, last_name, balance, last_activity, created_at
            FROM users
            WHERE last_activity >= datetime('now', ?) AND last_activity IS NOT NULL
            ORDER BY last_activity DESC
            LIMIT ?
        ''', (f'-{days} days', limit))
        
        users = []
        for row in cursor.fetchall():
            users.append({
                'user_id': row[0],
                'username': row[1],
                'first_name': row[2],
                'last_name': row[3],
                'balance': row[4],
                'last_activity': row[5],
                'created_at': row[6]
            })
        
        return users
    
    def get_all_orders(self, limit=1000):
        """Get a list of all orders with details"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, user_id, order_id, service_id, service_name, quantity, link, price, status, created_at
            FROM orders
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))
        
        orders = []
        for row in cursor.fetchall():
            orders.append({
                'id': row[0],
                'user_id': row[1],
                'order_id': row[2],
                'service_id': row[3],
                'service_name': row[4],
                'quantity': row[5],
                'link': row[6],
                'price': row[7],
                'status': row[8],
                'created_at': row[9]
            })
        
        return orders
    
    def get_recent_orders_list(self, days=7, limit=1000):
        """Get a list of orders in the last X days"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, user_id, order_id, service_id, service_name, quantity, link, price, status, created_at
            FROM orders
            WHERE created_at >= datetime('now', ?)
            ORDER BY created_at DESC
            LIMIT ?
        ''', (f'-{days} days', limit))
        
        orders = []
        for row in cursor.fetchall():
            orders.append({
                'id': row[0],
                'user_id': row[1],
                'order_id': row[2],
                'service_id': row[3],
                'service_name': row[4],
                'quantity': row[5],
                'link': row[6],
                'price': row[7],
                'status': row[8],
                'created_at': row[9]
            })
        
        return orders

    def set_service_price_override(self, service_id, original_price, custom_price, admin_id):
        """Set a custom price for a service"""
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                '''INSERT OR REPLACE INTO service_price_overrides 
                   (service_id, original_price, custom_price, updated_at, updated_by)
                   VALUES (?, ?, ?, ?, ?)''',
                (service_id, original_price, custom_price, datetime.now(), admin_id)
            )
            self.conn.commit()
            
            # Invalidate services cache
            self.invalidate_services_cache()
            
            return True
        except Exception as e:
            logger.error(f"Error setting service price override: {e}")
            return False
    
    def get_service_price_override(self, service_id):
        """Get the custom price for a service if it exists"""
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT custom_price FROM service_price_overrides WHERE service_id = ?',
            (service_id,)
        )
        result = cursor.fetchone()
        return result[0] if result else None
    
    def get_all_service_price_overrides(self):
        """Get all service price overrides"""
        cursor = self.conn.cursor()
        cursor.execute(
            '''SELECT service_id, original_price, custom_price, updated_at, updated_by 
               FROM service_price_overrides
               ORDER BY updated_at DESC'''
        )
        overrides = cursor.fetchall()
        return [{
            'service_id': o[0],
            'original_price': o[1],
            'custom_price': o[2],
            'updated_at': o[3],
            'updated_by': o[4]
        } for o in overrides]
    
    def delete_service_price_override(self, service_id):
        """Delete a service price override"""
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                'DELETE FROM service_price_overrides WHERE service_id = ?',
                (service_id,)
            )
            self.conn.commit()
            
            # Invalidate services cache
            self.invalidate_services_cache()
            
            return True
        except Exception as e:
            logger.error(f"Error deleting service price override: {e}")
            return False
    
    def update_service_prices_by_range(self, min_price, max_price, percentage, admin_id):
        """Update prices for services within a price range by a percentage"""
        # This will be implemented in the API client
        # We'll just record the range adjustment in the database for reference
        cursor = self.conn.cursor()
        try:
            # Create a record of the bulk update
            cursor.execute(
                '''INSERT INTO settings 
                   (key, value, updated_at) 
                   VALUES (?, ?, ?)''',
                (f"price_range_update_{datetime.now().strftime('%Y%m%d%H%M%S')}", 
                 json.dumps({
                     'min_price': min_price,
                     'max_price': max_price,
                     'percentage': percentage,
                     'admin_id': admin_id,
                     'timestamp': datetime.now().isoformat()
                 }),
                 datetime.now())
            )
            self.conn.commit()
            
            # Invalidate services cache
            self.invalidate_services_cache()
            
            return True
        except Exception as e:
            logger.error(f"Error recording price range update: {e}")
            return False
    
    def invalidate_services_cache(self):
        """Invalidate the services cache to ensure fresh data is fetched"""
        try:
            # Import here to avoid circular imports
            from handlers.services import invalidate_services_cache
            invalidate_services_cache()
            logger.info("Services cache invalidated after price change")
            return True
        except Exception as e:
            logger.error(f"Error invalidating services cache: {e}")
            return False

# Create global database instance
db = Database() 