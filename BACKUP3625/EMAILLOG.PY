import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Database connection
db_path = r"C:\Users\marka\Desktop\dealers_and_vins.db"

# SMTP Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "MARKACAFFEY@gmail.com"
EMAIL_PASSWORD = "zggb kioj fdcx kwvf"  # Use an App Password for Gmail

# Function to send email and log it in the database
def send_email(recipient, subject, message):
    try:
        # Format email
        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(message, "html"))

        # Connect to SMTP server and send email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, recipient, msg.as_string())
        server.quit()

        status = "Sent"
        print(f"✅ Email sent to {recipient}")

    except Exception as e:
        status = "Failed"
        print(f"❌ Email failed: {e}")

    # Log email status in the database
    log_email(recipient, subject, message, status)

# Function to log emails in the database
def log_email(recipient, subject, message, status):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO email_logs (recipient, subject, content, status)
    VALUES (?, ?, ?, ?)
    """, (recipient, subject, message, status))

    conn.commit()
    conn.close()

# Example Usage
send_email("markacaffey@gmail.com", "🚗 VIN Update - 6211962", "<p>This is a test email.</p>")
