import sqlite3
from datetime import datetime

DB_NAME = "emissions_history.db"


def init_db():
    """Initializes the SQLite database table for storing calculation logs."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            daily_kg REAL,
            monthly_kg REAL,
            yearly_kg REAL,
            transport_kg REAL,
            electricity_kg REAL,
            food_kg REAL,
            waste_kg REAL,
            water_kg REAL
        )
    ''')
    conn.commit()
    conn.close()


def save_record(results):
    """Saves a calculation entry into the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    breakdown = results["breakdown"]
    
    cursor.execute('''
        INSERT INTO history (
            timestamp, daily_kg, monthly_kg, yearly_kg, 
            transport_kg, electricity_kg, food_kg, waste_kg, water_kg
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
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


def get_history():
    """Retrieves all past entries sorted by most recent first."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT timestamp, daily_kg, monthly_kg, yearly_kg, 
               transport_kg, electricity_kg, food_kg, waste_kg, water_kg 
        FROM history 
        ORDER BY id DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return rows
