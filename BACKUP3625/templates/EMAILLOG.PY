import sqlite3

# ✅ Database Path
DB_PATH = r"C:\Users\marka\Desktop\dealers_and_vins.db"

# ✅ Connect to the Database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# ✅ Create `email_logs` Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS email_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dealer_id INTEGER,
    vin_id TEXT,
    subject TEXT,
    body TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

conn.commit()
conn.close()

print("✅ email_logs table created successfully!")
