import os
import psycopg2
import hashlib
from datetime import datetime
import streamlit as st


def get_connection():
    """Connects to Neon PostgreSQL using Streamlit Secrets or Environment Variables."""
    if "postgres" in st.secrets:
        db_url = st.secrets["postgres"]["url"]
    else:
        db_url = os.environ.get("DATABASE_URL")

    if not db_url:
        raise ValueError("Database URL missing! Add it to .streamlit/secrets.toml")

    return psycopg2.connect(db_url)


def hash_password(password):
    """Hashes passwords using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    """Initializes PostgreSQL tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        );
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) NOT NULL,
            timestamp VARCHAR(50) NOT NULL,
            daily_kg REAL,
            monthly_kg REAL,
            yearly_kg REAL,
            transport_kg REAL,
            electricity_kg REAL,
            food_kg REAL,
            waste_kg REAL,
            water_kg REAL,
            FOREIGN KEY (username) REFERENCES users (username) ON DELETE CASCADE
        );
    ''')

    conn.commit()
    cursor.close()
    conn.close()


def register_user(username, password):
    """Registers a new user account."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        hashed_pwd = hash_password(password)
        cursor.execute(
            'INSERT INTO users (username, password) VALUES (%s, %s)',
            (username, hashed_pwd)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True, "Account created successfully! Please log in."
    except psycopg2.IntegrityError:
        return False, "Username already exists. Please choose another."
    except Exception as e:
        return False, f"Database error: {str(e)}"


def verify_user(username, password):
    """Verifies login credentials."""
    conn = get_connection()
    cursor = conn.cursor()
    hashed_pwd = hash_password(password)
    cursor.execute(
        'SELECT id FROM users WHERE username = %s AND password = %s',
        (username, hashed_pwd)
    )
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user is not None


def save_record(username, results):
    """Saves footprint record linked to username."""
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    breakdown = results["breakdown"]

    cursor.execute('''
        INSERT INTO history (
            username, timestamp, daily_kg, monthly_kg, yearly_kg,
            transport_kg, electricity_kg, food_kg, waste_kg, water_kg
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
    cursor.close()
    conn.close()


def get_history(username):
    """Retrieves user history logs."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT timestamp, daily_kg, monthly_kg, yearly_kg,
               transport_kg, electricity_kg, food_kg, waste_kg, water_kg
        FROM history
        WHERE username = %s
        ORDER BY id DESC
    ''', (username,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows
