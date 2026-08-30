import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "procurement.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Farmers table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS farmers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aadhaar_hash TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        mobile TEXT NOT NULL,
        state TEXT NOT NULL,
        district TEXT NOT NULL,
        crop_type TEXT NOT NULL,
        land_hectares REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Mandis table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS mandis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT UNIQUE NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        max_daily_capacity INTEGER NOT NULL,
        current_capacity INTEGER DEFAULT 0,
        city TEXT NOT NULL,
        state TEXT NOT NULL
    )
    ''')

    # Slots table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS slots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        farmer_id INTEGER NOT NULL,
        mandi_id INTEGER NOT NULL,
        slot_date TEXT NOT NULL,
        hour_slot TEXT NOT NULL,
        allocated_crop_qty REAL NOT NULL,
        crop_type TEXT NOT NULL,
        token_code TEXT UNIQUE NOT NULL,
        status TEXT DEFAULT 'BOOKED',
        predicted_wait_minutes INTEGER DEFAULT 15,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (farmer_id) REFERENCES farmers (id),
        FOREIGN KEY (mandi_id) REFERENCES mandis (id)
    )
    ''')

    # Tokens table (Geofenced Token Activation)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slot_id INTEGER NOT NULL,
        token_number TEXT NOT NULL,
        is_active INTEGER DEFAULT 0,
        is_geofenced INTEGER DEFAULT 0,
        distance_to_mandi_meters REAL DEFAULT 9999.0,
        activated_at TIMESTAMP,
        FOREIGN KEY (slot_id) REFERENCES slots (id)
    )
    ''')

    # Quality Grading table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS quality_gradings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slot_id INTEGER NOT NULL,
        gross_weight REAL NOT NULL,
        tare_weight REAL NOT NULL,
        net_weight REAL NOT NULL,
        moisture_pct REAL NOT NULL,
        foreign_matter_pct REAL NOT NULL,
        grade TEXT NOT NULL,
        rate_per_quintal REAL NOT NULL,
        total_payout REAL NOT NULL,
        graded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (slot_id) REFERENCES slots (id)
    )
    ''')

    # PFMS Transactions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pfms_transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slot_id INTEGER NOT NULL,
        farmer_id INTEGER NOT NULL,
        pfms_ref_no TEXT UNIQUE NOT NULL,
        amount REAL NOT NULL,
        status TEXT DEFAULT 'INITIATED',
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (slot_id) REFERENCES slots (id),
        FOREIGN KEY (farmer_id) REFERENCES farmers (id)
    )
    ''')

    # Grievances table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS grievances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id TEXT UNIQUE NOT NULL,
        farmer_id INTEGER NOT NULL,
        category TEXT NOT NULL,
        description TEXT NOT NULL,
        status TEXT DEFAULT 'SUBMITTED',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (farmer_id) REFERENCES farmers (id)
    )
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully at:", DB_PATH)
