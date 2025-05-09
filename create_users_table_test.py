import sqlite3
import os

DB_PATH = r"C:\Users\marka\Desktop\mechanic_lien_app\dealers_and_vins.db"

def create_users_table():
    print(f"Using database: {DB_PATH}")
    if not os.path.exists(DB_PATH):
        print("❌ Database not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pnumber TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('dealer', 'admin'))
        )
    """)
    conn.commit()
    conn.close()
    print("✅ Table 'users' created (or already exists).")

if __name__ == "__main__":
    create_users_table()
