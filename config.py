"""
Configuration settings for Gutteridge Price Tracker
"""

import os

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Database
DATABASE_PATH = os.path.join(BASE_DIR, 'data', 'gutteridge_tracker.db')

# Flask settings
SECRET_KEY = os.urandom(24).hex()
DEBUG = True
HOST = '0.0.0.0'
PORT = 5000

# Scraper settings
BASE_URL = 'https://www.gutteridge.com'
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3

# Scheduler settings
PRICE_UPDATE_INTERVAL_HOURS = 6

# Logging
LOG_DIR = os.path.join(BASE_DIR, 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'app.log')
LOG_LEVEL = 'INFO'

# Ensure directories exist
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
