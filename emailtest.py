import smtplib
from email.mime.text import MIMEText

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "markacaffey@gmail.com"
EMAIL_PASSWORD = "zggb kioj fdcx kwvf"

def test_email():
    try:
        msg = MIMEText("This is a test email from Python.")
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = "markacaffey@gmail.com"
        msg["Subject"] = "Test Email"

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, "markacaffey@gmail.com", msg.as_string())
        server.quit()

        print("✅ Email sent successfully!")

    except Exception as e:
        print(f"❌ Email sending failed: {e}")

test_email()
