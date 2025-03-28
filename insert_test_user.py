import sqlite3

DB_PATH = "C:/Users/marka/Desktop/mechanic_lien_app/dealers_and_vins.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Set dealer_id 10 for user P51777 (update this ID if needed)
cursor.execute("UPDATE users SET dealer_id = 10 WHERE pnumber = 'P51777'")
conn.commit()
conn.close()

print("✅ dealer_id set for P51777")
