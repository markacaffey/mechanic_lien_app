import sqlite3

DB_PATH = r"C:\Users\marka\Desktop\mechanic_lien_app\dealers_and_vins.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Add new columns (if they don't exist already)
cursor.execute("ALTER TABLE dealers ADD COLUMN account_status TEXT DEFAULT 'active'")
cursor.execute("ALTER TABLE dealers ADD COLUMN stripe_customer_id TEXT")
cursor.execute("ALTER TABLE dealers ADD COLUMN stripe_subscription_id TEXT")
cursor.execute("ALTER TABLE dealers ADD COLUMN billing_type TEXT DEFAULT 'monthly'")  # or 'annual'
conn.commit()
conn.close()

print("✅ Dealers table updated!")
