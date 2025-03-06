import sqlite3

db_path = r"C:\Users\marka\Desktop\dealers_and_vins.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Backup existing data
cursor.execute("SELECT * FROM email_logs")
backup_data = cursor.fetchall()

# Drop the old table
cursor.execute("DROP TABLE IF EXISTS email_logs")

# Recreate the table with correct structure
cursor.execute("""
CREATE TABLE email_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipient TEXT NOT NULL,
    subject TEXT NOT NULL,
    content TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Pending',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# Restore backup data (if it exists)
if backup_data:
    cursor.executemany("""
    INSERT INTO email_logs (recipient, subject, content, status, timestamp)
    VALUES (?, ?, ?, ?, ?)
    """, [(row[1], row[2], row[3], row[4], row[5]) for row in backup_data])

conn.commit()
conn.close()

print("✅ The `email_logs` table has been fixed and recreated successfully!")
