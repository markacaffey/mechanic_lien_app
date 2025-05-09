import sqlite3
import html

db_path = r"C:\Users\marka\Desktop\dealers_and_vins.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Retrieve all email logs
cursor.execute("SELECT id, recipient, subject, content, status, sent_at FROM email_logs ORDER BY sent_at DESC")
email_logs = cursor.fetchall()

conn.close()

# Print logs with formatted HTML
if email_logs:
    print("✅ Email Logs Found:\n")
    for log in email_logs:
        log_id, recipient, subject, content, status, sent_at = log
        formatted_content = html.unescape(content)  # Fix newline issues in HTML

        print(f"📩 **Email ID:** {log_id}")
        print(f"📤 **To:** {recipient}")
        print(f"📌 **Subject:** {subject}")
        print(f"📅 **Sent At:** {sent_at}")
        print(f"📜 **Status:** {status}")
        print(f"📄 **Content:**\n{formatted_content}")
        print("=" * 80, "\n")  # Divider for readability
else:
    print("❌ No email logs found.")
