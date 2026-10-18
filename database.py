import sqlite3
import hashlib
from datetime import datetime

DB_NAME = "emissions_history.db"


def hash_password(password):
    """Hashes passwords using SHA-256 for secure storage."""
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    """Initializes SQLite database tables for users and calculation logs."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    # History Table with Username column
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            daily_kg REAL,
            monthly_kg REAL,
            yearly_kg REAL,
            transport_kg REAL,
            electricity_kg REAL,
            food_kg REAL,
            waste_kg REAL,
            water_kg REAL,
            FOREIGN KEY (username) REFERENCES users (username)
        )
    ''')
    conn.commit()
    conn.close()


def register_user(username, password):
    """Registers a new user account with hashed password."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        hashed_pwd = hash_password(password)
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_pwd))
        conn.commit()
        conn.close()
        return True, "Account created successfully! Please log in."
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Username already exists. Please choose a different one."


def verify_user(username, password):
    """Verifies user login credentials."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    hashed_pwd = hash_password(password)
    cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, hashed_pwd))
    user = cursor.fetchone()
    conn.close()
    return user is not None


def save_record(username, results):
    """Saves a calculation entry linked to a specific username."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    breakdown = results["breakdown"]
    
    cursor.execute('''
        INSERT INTO history (
            username, timestamp, daily_kg, monthly_kg, yearly_kg, 
            transport_kg, electricity_kg, food_kg, waste_kg, water_kg
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        username,
        now,
        results["daily_kg"],
        results["monthly_kg"],
        results["yearly_kg"],
        breakdown["Transportation"],
        breakdown["Electricity"],
        breakdown["Food & Diet"],
        breakdown["Household Waste"],
        breakdown["Water Usage"]
    ))
    
    conn.commit()
    conn.close()


def get_history(username):
    """Retrieves history entries specific to the logged-in user."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT timestamp, daily_kg, monthly_kg, yearly_kg, 
               transport_kg, electricity_kg, food_kg, waste_kg, water_kg 
        FROM history 
        WHERE username = ?
        ORDER BY id DESC
    ''', (username,))
    rows = cursor.fetchall()
    conn.close()
    return rows
