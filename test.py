import sqlite3

DB_PATH = "C:/Users/marka/Desktop/mechanic_lien_app/dealers_and_vins.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT pnumber, dealer_id FROM users")
rows = cursor.fetchall()

print("📋 Users and their dealer_ids:")
for row in rows:
    print(row)

conn.close()
