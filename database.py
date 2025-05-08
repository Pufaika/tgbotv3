import sqlite3
import random
import string

DB_FILE = "data.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            short_id TEXT UNIQUE,
            category TEXT,
            size TEXT,
            location TEXT,
            description TEXT,
            photos TEXT,
            message_id INTEGER,
            available INTEGER DEFAULT 1
        )
    ''')
    conn.commit()
    conn.close()

def generate_short_id(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def add_item(category, size, location, description, photo_ids, message_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    short_id = generate_short_id()
    photo_str = ','.join(photo_ids)
    c.execute('''
        INSERT INTO items (short_id, category, size, location, description, photos, message_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (short_id, category, size, location, description, photo_str, message_id))
    conn.commit()
    conn.close()
    return short_id

def get_item_counts_by_category(category):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        SELECT size, COUNT(*) FROM items
        WHERE category = ? AND available = 1
        GROUP BY size
    ''', (category,))
    results = {size: count for size, count in c.fetchall()}
    conn.close()
    return results

def get_random_item(category, size):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        SELECT id, category, size, location, photos
        FROM items
        WHERE category = ? AND size = ? AND available = 1
        ORDER BY RANDOM()
        LIMIT 1
    ''', (category, size))
    result = c.fetchone()
    conn.close()
    return result

def mark_item_unavailable(item_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('UPDATE items SET available = 0 WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()

def delete_item_by_message_id(message_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM items WHERE message_id = ?', (message_id,))
    conn.commit()
    conn.close()
