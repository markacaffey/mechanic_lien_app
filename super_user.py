import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect(r"C:\Users\marka\Desktop\mechanic_lien_app\dealers_and_vins.db")
cursor = conn.cursor()

pnumber = '0001'
email = 'admin@mytitleguy.com'
password = 'password123'
hashed = generate_password_hash(password)
role = 'admin'

try:
    cursor.execute("""
        INSERT INTO users (pnumber, email, password_hash, role)
        VALUES (?, ?, ?, ?)
    """, (pnumber, email, hashed, role))
    conn.commit()
    print("✅ Superuser created!")
except Exception as e:
    print("❌ Error:", e)
finally:
    conn.close()
