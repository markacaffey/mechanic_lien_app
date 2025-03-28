import sqlite3

conn = sqlite3.connect("dealers_and_vins.db")
cursor = conn.cursor()

print("🔍 Fetching all users in 'dealers_and_vins.db'...")
cursor.execute("SELECT id, pnumber, email, role FROM users")
rows = cursor.fetchall()

if rows:
    print("✅ Users found:")
    for row in rows:
        print(row)
else:
    print("❌ No users found in users table.")

conn.close()
