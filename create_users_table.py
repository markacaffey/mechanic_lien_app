import sqlite3

# Update path if needed
DB_PATH = r"C:\Users\marka\Desktop\mechanic_lien_app\dealers_and_vins.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# ✅ Create users table if it doesn't exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pnumber TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'dealer'
)
""")

conn.commit()
conn.close()

print("✅ Users table created successfully.")
