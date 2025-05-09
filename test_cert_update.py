import sqlite3
from datetime import datetime
import os

# 🔁 Point this to your actual DB path
DB_PATH = os.path.join(os.getcwd(), "dealers_and_vins.db")
print(f"📁 Using database: {DB_PATH}")

# 🛠 Change this to a valid rowid from your vins table
vin_rowid = 452
status_field = "cert1_status"
new_status = f"Delivered - {datetime.today().strftime('%Y-%m-%d')}"

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 🔁 Update
    cursor.execute(f"UPDATE vins SET {status_field} = ? WHERE rowid = ?", (new_status, vin_rowid))
    conn.commit()
    print(f"✅ Rows affected: {cursor.rowcount}")

    # 🔍 Confirm
    cursor.execute(f"SELECT vin, {status_field} FROM vins WHERE rowid = ?", (vin_rowid,))
    row = cursor.fetchone()
    if row:
        print(f"🔎 VIN: {row[0]}")
        print(f"📌 {status_field}: {row[1]}")
    else:
        print("❌ VIN not found.")

except Exception as e:
    print("❌ Error:", e)

finally:
    conn.close()
