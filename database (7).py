import sqlite3
import config

def dict_factory(cursor, row):
    """تبدیل هر ردیف نتیجه به دیکشنری"""
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

def get_connection():
    """ایجاد اتصال به دیتابیس"""
    conn = sqlite3.connect(config.DATABASE_NAME)
    conn.row_factory = dict_factory
    return conn

def init_db():
    """ایجاد تمام جداول مورد نیاز در دیتابیس"""
    conn = get_connection()
    cur = conn.cursor()

    # ایجاد جدول users
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            phone TEXT,
            coin_balance INTEGER DEFAULT {config.INITIAL_COINS},
            coin_fraction REAL DEFAULT 0,
            warnings INTEGER DEFAULT 0,
            banned INTEGER DEFAULT 0,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    try:
        cur.execute("ALTER TABLE users ADD COLUMN coin_fraction REAL DEFAULT 0;")
    except sqlite3.OperationalError:
        pass

    # ایجاد جدول channels
    cur.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            channel_id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER,
            channel_username TEXT,
            display_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(owner_id, channel_username)
        );
    """)

    # ایجاد جدول subscriber_orders
    cur.execute("""
        CREATE TABLE IF NOT EXISTS subscriber_orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            channel_username TEXT,
            required INTEGER,
            current INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # ایجاد جدول joined_channels
    cur.execute("""
        CREATE TABLE IF NOT EXISTS joined_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            channel_username TEXT,
            join_type TEXT,
            order_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, channel_username, join_type)
        );
    """)

    # ایجاد جدول referrals
    cur.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            referrer_id INTEGER NOT NULL,
            referred_user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (referrer_id, referred_user_id)
        );
    """)

    # ایجاد جدول coin_orders
    cur.execute("""
        CREATE TABLE IF NOT EXISTS coin_orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            quantity INTEGER,
            price REAL,
            receipt_file_id TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            admin_id INTEGER
        );
    """)

    # ایجاد جدول transactions برای گزارش تراکنش‌ها
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            amount REAL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            description TEXT
        );
    """)

    # ایجاد جدول forced_channels برای عضویت اجباری
    cur.execute("""
        CREATE TABLE IF NOT EXISTS forced_channels (
            channel_username TEXT PRIMARY KEY,
            limit_type TEXT CHECK(limit_type IN ('time', 'members')),
            limit_value TEXT,
            current_members INTEGER DEFAULT 0,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # ایجاد جدول settings جهت ذخیره تنظیمات مانند پیام خوش آمدید
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    """)

    conn.commit()
    conn.close()

# ==================== مدیریت کاربران ====================
def get_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cur.fetchone()
    conn.close()
    return user

def add_user(user_id, phone, coin_balance):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users (user_id, phone, coin_balance) VALUES (?, ?, ?)",
                (user_id, phone, coin_balance))
    conn.commit()
    conn.close()

def update_user_coins(user_id, delta):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET coin_balance = coin_balance + ? WHERE user_id = ?",
                (delta, user_id))
    conn.commit()
    conn.close()

def update_coin_balance(user_id, new_balance):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET coin_balance = ? WHERE user_id = ?",
                (new_balance, user_id))
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('new_system_database.db')
    conn.row_factory = sqlite3.Row  # برای دسترسی به ستون‌ها با نام
    return conn
    
def remove_user_channel(owner_id, channel_username):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM channels
        WHERE owner_id = ? AND channel_username = ?
    """, (owner_id, channel_username))
    conn.commit()
    conn.close()

# اجرای کوئری‌ها
def execute_query(query, params=()):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    return cursor

def fetch_query(query, params=()):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    result = cursor.fetchall()
    conn.close()
    return result
def update_user_fraction(user_id, new_fraction):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET coin_fraction = ? WHERE user_id = ?",
                (new_fraction, user_id))
    conn.commit()
    conn.close()

def get_all_users():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users")
    users = cur.fetchall()
    conn.close()
    return users

def search_users(query):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE phone LIKE ? OR CAST(user_id AS TEXT) LIKE ?",
                (f"%{query}%", f"%{query}%"))
    users = cur.fetchall()
    conn.close()
    return users

def ban_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET banned = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def unban_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET banned = 0 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def update_user_warnings(user_id, delta):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET warnings = warnings + ? WHERE user_id = ?", (delta, user_id))
    conn.commit()
    conn.close()

def get_user_warnings(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT warnings FROM users WHERE user_id = ?", (user_id,))
    result = cur.fetchone()
    conn.close()
    if result:
        return result.get("warnings", 0)
    return 0

def get_weighted_orders(collector_id, limit=30):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT *,
            ((100.0 * current / required) * 3 +
             (strftime('%s','now') - strftime('%s', created_at)) / 3600.0 * 2 +
             (required - current) * 1) AS weight
        FROM subscriber_orders
        WHERE user_id != ? AND current < required
        ORDER BY weight DESC
        LIMIT ?
    """, (collector_id, limit))
    rows = cur.fetchall()
    conn.close()
    return rows

def user_has_joined_channel(user_id, channel_username):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 1 FROM joined_channels
        WHERE user_id = ? AND channel_username = ?
    """, (user_id, channel_username))
    result = cur.fetchone()
    conn.close()
    return result is not None

# ==================== مدیریت کانال‌ها ====================
def get_user_channels(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM channels WHERE owner_id = ?", (user_id,))
    channels = cur.fetchall()
    conn.close()
    return channels

def add_channel(owner_id, channel_username, display_name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO channels (owner_id, channel_username, display_name) VALUES (?, ?, ?)",
                (owner_id, channel_username, display_name))
    conn.commit()
    conn.close()

def channel_exists(owner_id, channel_username):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM channels WHERE owner_id = ? AND channel_username = ?",
                (owner_id, channel_username))
    exists = cur.fetchone() is not None
    conn.close()
    return exists

# ==================== مدیریت سفارش‌های جذب اعضا (subscriber_orders) ====================
def create_subscriber_order(user_id, channel_username, required):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO subscriber_orders (user_id, channel_username, required) VALUES (?, ?, ?)",
                (user_id, channel_username, required))
    order_id = cur.lastrowid
    conn.commit()
    conn.close()
    return order_id

def get_available_coin_orders(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM subscriber_orders WHERE user_id = ? AND current < required",
                (user_id,))
    orders = cur.fetchall()
    conn.close()
    return orders

def update_order_current(order_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE subscriber_orders SET current = current + 1 WHERE order_id = ?",
                (order_id,))
    conn.commit()
    conn.close()

def has_active_order(user_id, channel_username):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 1 FROM subscriber_orders
        WHERE user_id = ? AND channel_username = ? AND current < required
    """, (user_id, channel_username))
    exists = cur.fetchone() is not None
    conn.close()
    return exists

# ==================== مدیریت عضویت کانال‌ها (joined_channels) ====================
def get_all_joined_members():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM joined_channels")
    rows = cur.fetchall()
    conn.close()
    return rows

def add_joined_channel(user_id, channel_username, join_type, order_id=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO joined_channels (user_id, channel_username, join_type, order_id)
        VALUES (?, ?, ?, ?)
    """, (user_id, channel_username, join_type, order_id))
    conn.commit()
    conn.close()

def remove_joined_channel(user_id, channel_username, join_type):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM joined_channels
        WHERE user_id = ? AND channel_username = ? AND join_type = ?
    """, (user_id, channel_username, join_type))
    conn.commit()
    conn.close()

def execute_raw_sql(query, params: tuple = ()):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(query, params)
        rows = cur.fetchall()
    except Exception as e:
        print("DB Error:", e)
        rows = None
    conn.commit()
    conn.close()
    return rows

def get_available_orders_for_collector(collector_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM subscriber_orders
        WHERE user_id != ? AND current < required
    """, (collector_id,))
    orders = cur.fetchall()
    conn.close()
    return orders

# ==================== مدیریت سفارش‌های خرید سکه (coin_orders) ====================
def create_coin_order(user_id, quantity, price, receipt_file_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO coin_orders (user_id, quantity, price, receipt_file_id, status)
        VALUES (?, ?, ?, ?, 'pending')
    """, (user_id, quantity, price, receipt_file_id))
    order_id = cur.lastrowid
    conn.commit()
    conn.close()
    return order_id

def get_coin_order(order_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM coin_orders WHERE order_id = ?", (order_id,))
    order = cur.fetchone()
    conn.close()
    return order

def update_coin_order_status(order_id, status, admin_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE coin_orders
        SET status = ?, admin_id = ?
        WHERE order_id = ?
    """, (status, admin_id, order_id))
    conn.commit()
    conn.close()

# ==================== مدیریت ارجاعات (referrals) ====================
def check_referral_exists_db(referrer_id, referred_user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 1 FROM referrals
        WHERE referrer_id = ? AND referred_user_id = ?
    """, (referrer_id, referred_user_id))
    exists = cur.fetchone() is not None
    conn.close()
    return exists

def register_referral_db(referrer_id, referred_user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO referrals (referrer_id, referred_user_id)
        VALUES (?, ?)
    """, (referrer_id, referred_user_id))
    conn.commit()
    conn.close()

_referrals = {}
def check_referral_exists(referrer_id, referred_user_id):
    return referred_user_id in _referrals.get(referrer_id, set())

def register_referral(referrer_id, referred_user_id):
    if referrer_id in _referrals:
        _referrals[referrer_id].add(referred_user_id)
    else:
        _referrals[referrer_id] = {referred_user_id}
    print(f"Referral registered: {referrer_id} -> {referred_user_id}")

def get_referral_keyboard():
    from telegram import ReplyKeyboardMarkup
    return ReplyKeyboardMarkup([["✅ تایید زیرمجموعه"]], resize_keyboard=True)

# ==================== تنظیمات (settings) ====================
def update_welcome_message(message):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO settings (key, value)
        VALUES ('welcome_message', ?)
    """, (message,))
    conn.commit()
    conn.close()

def get_welcome_message():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key = 'welcome_message'")
    result = cur.fetchone()
    conn.close()
    if result:
        return result.get("value", "خوش آمدید!")
    return "خوش آمدید!"

# ==================== مدیریت تراکنش‌ها (transactions) ====================
def add_transaction(tx_type, amount, description=""):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO transactions (type, amount, description)
        VALUES (?, ?, ?)
    """, (tx_type, amount, description))
    conn.commit()
    conn.close()

def get_transactions(limit=5):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM transactions ORDER BY date DESC LIMIT ?", (limit,))
    transactions = cur.fetchall()
    conn.close()
    return transactions

# ==================== مدیریت عضویت اجباری ====================
def add_forced_channel(channel_username, limit_type, limit_value):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO forced_channels (channel_username, limit_type, limit_value, current_members)
        VALUES (?, ?, ?, 0)
    """, (channel_username, limit_type, str(limit_value)))
    conn.commit()
    conn.close()

def get_active_forced_channels():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM forced_channels")
    rows = cur.fetchall()
    conn.close()
    return rows

def remove_forced_channel(channel_username):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM forced_channels WHERE channel_username = ?", (channel_username,))
    conn.commit()
    conn.close()

def increment_forced_channel_count(channel_username):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE forced_channels SET current_members = current_members + 1 WHERE channel_username = ?", (channel_username,))
    conn.commit()
    conn.close()

def is_user_joined_forced_channel(user_id, channel_username):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 1 FROM joined_channels
        WHERE user_id = ? AND channel_username = ? AND join_type = 'forced'
    """, (user_id, channel_username))
    result = cur.fetchone()
    conn.close()
    return result is not None

# ==================== تابع اختیاری برای دریافت آیدی ادمین ====================
def get_admin_id():
    # مقدار آیدی ادمین را به طور ثابت یا از منبع دلخواه برگردانید.
    return config.ADMIN_ID

# ==================== توابع جدید انتخاب سفارش برای جمع‌آوری سکه ====================
import random

def get_random_orders(collector_id, limit=10):
    orders = get_available_orders_for_collector(collector_id)
    random.shuffle(orders)
    return orders[:limit]

def get_recent_orders(collector_id, limit=10):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM subscriber_orders
        WHERE user_id != ? AND current < required
        ORDER BY created_at DESC
        LIMIT ?
    """, (collector_id, limit))
    recent_orders = cur.fetchall()
    conn.close()
    return recent_orders

def get_ending_orders(collector_id, limit=10):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT *, (current * 1.0 / required) AS progress
        FROM subscriber_orders
        WHERE user_id != ? AND current < required
        ORDER BY progress DESC
        LIMIT ?
    """, (collector_id, limit))
    ending_orders = cur.fetchall()
    conn.close()
    return ending_orders