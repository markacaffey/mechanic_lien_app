import sqlite3

DB_PATH = "C:/Users/marka/Desktop/mechanic_lien_app/dealers_and_vins.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE users ADD COLUMN dealer_id INTEGER")
    conn.commit()
    print("✅ dealer_id column added to users table.")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("⚠️ dealer_id column already exists. You're good.")
    else:
        print("❌ Failed to add dealer_id:", e)
finally:
    conn.close()
