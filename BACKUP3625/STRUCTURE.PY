import sqlite3

db_path = r"C:\Users\marka\Desktop\dealers_and_vins.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check table structure
cursor.execute("PRAGMA table_info(email_logs)")
columns = cursor.fetchall()

conn.close()

# Print column names
print("✅ Current `email_logs` Table Structure:")
for col in columns:
    print(col)
