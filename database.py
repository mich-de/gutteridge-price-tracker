"""
Database module for Gutteridge Price Tracker
Handles SQLite database operations for storing products and price history
"""

import sqlite3
from datetime import datetime
import os

DB_PATH = 'gutteridge_tracker.db'

def get_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            image_url TEXT,
            category TEXT,
            current_price REAL,
            original_price REAL,
            currency TEXT DEFAULT 'EUR',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Price history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            price REAL NOT NULL,
            original_price REAL,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    
    # Price alerts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            target_price REAL NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            triggered_at TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully")

def add_product(url, name, image_url=None, category=None, current_price=None, original_price=None):
    """Add a new product to track"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO products (url, name, image_url, category, current_price, original_price, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (url, name, image_url, category, current_price, original_price, datetime.now()))
        
        product_id = cursor.lastrowid
        
        # Add initial price record
        if current_price:
            cursor.execute('''
                INSERT INTO price_history (product_id, price, original_price, recorded_at)
                VALUES (?, ?, ?, ?)
            ''', (product_id, current_price, original_price, datetime.now()))
        
        conn.commit()
        return product_id
    except sqlite3.IntegrityError:
        # Product already exists
        cursor.execute('SELECT id FROM products WHERE url = ?', (url,))
        result = cursor.fetchone()
        return result['id'] if result else None
    finally:
        conn.close()

def update_product_price(product_id, current_price, original_price=None):
    """Update product price and add to history"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Update current price
    cursor.execute('''
        UPDATE products 
        SET current_price = ?, original_price = ?, updated_at = ?
        WHERE id = ?
    ''', (current_price, original_price, datetime.now(), product_id))
    
    # Add to price history
    cursor.execute('''
        INSERT INTO price_history (product_id, price, original_price, recorded_at)
        VALUES (?, ?, ?, ?)
    ''', (product_id, current_price, original_price, datetime.now()))
    
    conn.commit()
    conn.close()

def get_all_products():
    """Get all tracked products"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products ORDER BY updated_at DESC')
    products = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return products

def get_product(product_id):
    """Get a specific product by ID"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    product = cursor.fetchone()
    conn.close()
    return dict(product) if product else None

def get_product_by_url(url):
    """Get a product by URL"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products WHERE url = ?', (url,))
    product = cursor.fetchone()
    conn.close()
    return dict(product) if product else None

def get_price_history(product_id, limit=100):
    """Get price history for a product"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM price_history 
        WHERE product_id = ? 
        ORDER BY recorded_at DESC 
        LIMIT ?
    ''', (product_id, limit))
    history = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return history

def delete_product(product_id):
    """Delete a product and its price history"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM price_history WHERE product_id = ?', (product_id,))
    cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()

def get_price_stats(product_id):
    """Get price statistics for a product"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            MIN(price) as min_price,
            MAX(price) as max_price,
            AVG(price) as avg_price,
            COUNT(*) as record_count
        FROM price_history 
        WHERE product_id = ?
    ''', (product_id,))
    stats = dict(cursor.fetchone())
    conn.close()
    return stats

if __name__ == '__main__':
    init_db()
