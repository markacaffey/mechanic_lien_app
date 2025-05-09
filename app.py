from dotenv import load_dotenv
load_dotenv()
import os
# stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
db_path = os.path.join(os.getcwd(), "dealers_and_vins.db")
print("📁 DB file path:", db_path)
print("📄 DB file inode:", os.stat(db_path).st_ino)
# delete the above if this works
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, request, redirect, url_for, render_template, flash, session, send_file, current_app
import os
from dotenv import load_dotenv
load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")

SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))

import stripe
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
stripe.api_key = STRIPE_SECRET_KEY


app = Flask(__name__)
DB_PATH = "C:/Users/marka/Desktop/mechanic_lien_app/dealers_and_vins.db"

def get_available_credits(dealer_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(quantity - used), 0)
        FROM lien_credits
        WHERE dealer_id = ?
    """, (dealer_id,))
    available = cursor.fetchone()[0]
    conn.close()

    print(f"📊 [get_available_credits] Dealer {dealer_id}: Available = {available}")
    return max(0, available)

def decrement_lien_credit(dealer_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Find a lien_credits row with unused credit
    cursor.execute("""
        SELECT id, quantity, COALESCE(used, 0) AS used
        FROM lien_credits
        WHERE dealer_id = ? AND COALESCE(used, 0) < quantity
        ORDER BY id ASC
        LIMIT 1
    """, (dealer_id,))
    row = cursor.fetchone()

    if row:
        credit_id = row["id"]
        used = row["used"] + 1
        cursor.execute("UPDATE lien_credits SET used = ? WHERE id = ?", (used, credit_id))
        conn.commit()
        conn.close()
        return True
    else:
        conn.close()
        return False

# Toggle this to False when ready to email real dealers
TESTING_MODE = False

# from dotenv import load_dotenv
import os

# load_dotenv()  # This will load the .env file

# print("Public key:", os.getenv("STRIPE_PUBLIC_KEY"))
# print("Secret key:", os.getenv("STRIPE_SECRET_KEY"))


import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import fitz  # PyMuPDF for PDF generation

# Database path
DB_PATH = os.path.join(os.getcwd(), "dealers_and_vins.db")
print("🚨 Using DB from:", DB_PATH)

# Initialize Flask app
app = Flask(__name__)

# NEW SECTION FOR LOGIN
def create_users_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pnumber TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('dealer', 'admin'))
        )
    """)
    conn.commit()
    conn.close()
    print("✅ users table checked/created.")

# Call function to create the users table
create_users_table()

# Email-related imports (you might move these to where email logic is written)
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
# --------------- SENDING EMAILS -----------------------------------------------

import sqlite3

# Set Stripe API key
# stripe.api_key = os.getenv("STRIPE_SECRET_KEY")  # Ensure this variable is set in your environment

# Database path
print("📁 DB file path:", DB_PATH)
print("📄 DB file inode:", os.stat(DB_PATH).st_ino)



# 🔹 Extra Lien Pricing by Plan
EXTRA_LIEN_PRICING = {
    "prod_S5UkBvabSnSyT0": 10000,  # Flex: $100 per lien
    "prod_S5o6uwMUHoVEwt": 7500,   # Starter: $75 per extra lien
    "prod_S5o7tXn3FY1Eq1": 5000,   # Pro: $50 per extra lien
    "prod_S5oBIn40Hf1AES": 4000,   # Enterprise: $40 per extra lien
}


# Initialize Flask app
app = Flask(__name__)

#EMAIL LINKS FOR FILE DOWNLOADING
import smtplib
from email.message import EmailMessage

def email_forms_with_attachments(files, to_email, vin="", dealer_name="Dealer"):
    msg = EmailMessage()
    msg["Subject"] = f"📎 Forms for {vin} - My Title Guy"
    msg["From"] = SMTP_USER
    msg["To"] = to_email

    form_list_html = "".join(f"<li>{os.path.basename(f[0]).replace('_', ' ')}</li>" for f in files)
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
        <h2 style="color: #2E86C1;">📄 Your Mechanic Lien Forms Are Attached</h2>
        <p>Hello {dealer_name},</p>
        <p>Your requested forms for VIN <strong>{vin}</strong> are attached:</p>
        <ul>{form_list_html}</ul>
        <p>
            If you have any questions, feel free to reach out to us at 
            <a href="mailto:markacaffey@gmail.com">markacaffey@gmail.com</a>.
        </p>
        <p style="margin-top: 30px;">Warm regards,<br>
        <strong>The Mechanic Lien App Team at My Title Guy</strong><br>
        <em>Mechanic Liens Made Easy</em></p>
        <hr style="margin-top: 40px;">
        <small style="color: #888;">This email was sent automatically. Please do not reply to this message.</small>
        </div>
        </body>
    </html>
    """
    msg.set_content("Your forms are ready. Please open the attached files.")
    msg.add_alternative(html_body, subtype="html")

    for filename, filepath in files:
        with open(filepath, "rb") as f:
            msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename=filename)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(SMTP_USER, SMTP_PASS)
            smtp.send_message(msg)
        print(f"✅ Email sent to {to_email} with {len(files)} attachment(s).")
    except Exception as e:
        print(f"❌ Error sending email with attachments: {e}")

    # Optional: log the event
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO email_logs (dealer_id, email, subject, attachments, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (
            session.get("dealer_id", 0),
            to_email,
            msg["Subject"],
            ", ".join(f[0] for f in files),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()
        conn.close()
    except Exception as log_error:
        print("❌ Failed to log email:", log_error)


# ✅ NEW SECTION FOR LOGIN

def create_users_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pnumber TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('dealer', 'admin'))
        )
    """)
    conn.commit()
    conn.close()
    print("✅ users table checked/created.")

def create_payments_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dealer_id INTEGER NOT NULL,
            product_id TEXT NOT NULL,
            amount_cents INTEGER NOT NULL,
            purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print("✅ payments table checked/created.")

def create_lien_credits_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lien_credits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dealer_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            used INTEGER NOT NULL DEFAULT 0,
            source TEXT DEFAULT 'stripe',
            purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print("✅ lien_credits table checked/created.")


def add_lien_credits(dealer_id, credits):
    import sqlite3
    import time

    for attempt in range(3):
        try:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO lien_credits (dealer_id, quantity, used)
                VALUES (?, ?, 0)
            """, (dealer_id, credits))
            conn.commit()
            conn.close()
            print("✅ Lien credits added in add_lien_credits()")
            break
        except sqlite3.OperationalError as e:
            print("⏳ Retrying due to DB lock...", e)
            time.sleep(0.5)
        finally:
            try:
                conn.close()
            except:
                pass


# Call these on app startup
create_users_table()
create_payments_table()
create_lien_credits_table()



# ✅ SMTP Configuration
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


app = Flask(__name__)
# DB_PATH = r"C:\Users\marka\Desktop\dealers_and_vins.db"

# SMTP Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "markacaffey@gmail.com"
EMAIL_PASSWORD = "zggb kioj fdcx kwvf"  # App-specific password for Gmail

def send_email(recipient, subject, message):
    try:
        print(f"📧 Attempting to send email to: {recipient}")
        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(message, "html"))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.set_debuglevel(1)  # Enable debugging output
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, recipient, msg.as_string())
        server.quit()
        print(f"✅ Email successfully sent to {recipient}")
    except Exception as e:
        print(f"❌ Email failed to send: {e}")

def send_dealer_email(recipient, subject, message, attachment_link=None, force_test=False):
    """
    Send email to a dealer or to a test address if force_test is True or TESTING_MODE is enabled.
    """
    final_recipient = "markacaffey@gmail.com" if force_test or TESTING_MODE else recipient

    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = final_recipient
        msg["Subject"] = subject

        if attachment_link:
            message += f"<br><br><a href='{attachment_link}' target='_blank'>📄 Click here to download the PDF</a>"

        msg.attach(MIMEText(message, "html"))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, final_recipient, msg.as_string())
        server.quit()

        print(f"✅ Email sent to {final_recipient}")
    except Exception as e:
        print(f"❌ Email sending failed: {e}")



# @app.route("/add_vin", methods=["GET", "POST"])
def add_vin():
    role = session.get("role")
    dealer_id = session.get("dealer_id")

    if role != "dealer" or not dealer_id:
        flash("Unauthorized access. Please log in as a dealer.", "danger")
        return redirect(url_for("login"))

    available_credits = get_available_credits(dealer_id)
    if available_credits <= 0:
        flash("❌ You are out of lien credits. Please buy more to add a new VIN.", "danger")

        # 🔔 Send credit alert email if none left
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT name, email FROM dealers WHERE dealer_id = ?", (dealer_id,))
        dealer = cursor.fetchone()
        conn.close()

        if dealer and dealer["email"]:
            subject = "⚠️ You’re Out of Lien Credits"
            html_body = render_template("email_templates/low_credit_warning.html", dealer_name=dealer["name"])
            send_email(dealer["email"], subject, html_body)
            print(f"📧 Credit alert sent to {dealer['email']}")

        return redirect(url_for("buy_credits"))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM dealers WHERE dealer_id = ?", (dealer_id,))
    dealer = cursor.fetchone()

    if not dealer:
        flash("⚠ Dealer not found!", "danger")
        conn.close()
        return redirect(url_for("view_dealers"))

    if request.method == "POST":
        vin_data = {key: request.form.get(key, "").strip() for key in request.form}
        vin_data["dealer_id"] = dealer_id

        required_fields = [
            "vin", "year", "make", "model", "body", "color", "plate", "weight", "cweight", "odometer",
            "owner", "owner_address1", "owner_address2", "renewal", "renewal_address1", "renewal_address2",
            "lein_holder", "lein_holder_address1", "lein_holder_address2", "person_left", "person_left_address1", "person_left_address2",
            "county", "repair_amount", "ready_to_title", "status_downtown", "date_sent_downtown", "lien_canceled",
            "date_canceled", "transferred_harris_county", "cert1", "cert2", "cert3", "cert4", "cert5", "cert6",
            "cert1_status", "cert2_status", "cert3_status", "cert4_status", "cert5_status", "cert6_status",
            "date_left", "date_completed", "date_notified", "sale_date"
        ]

        for field in required_fields:
            vin_data.setdefault(field, "N/A")

        cursor.execute("""
            INSERT INTO vins (
                vin, year, make, model, body, color, plate, weight, 
                cweight, odometer, owner, owner_address1, owner_address2, 
                renewal, renewal_address1, renewal_address2, 
                lein_holder, lein_holder_address1, lein_holder_address2, 
                person_left, person_left_address1, person_left_address2,
                county, repair_amount, ready_to_title, status_downtown, 
                date_sent_downtown, lien_canceled, date_canceled, transferred_harris_county,
                cert1, cert2, cert3, cert4, cert5, cert6, 
                cert1_status, cert2_status, cert3_status, cert4_status, cert5_status, cert6_status,
                date_left, date_completed, date_notified, sale_date, dealer_id
            ) VALUES (
                :vin, :year, :make, :model, :body, :color, :plate, :weight, 
                :cweight, :odometer, :owner, :owner_address1, :owner_address2, 
                :renewal, :renewal_address1, :renewal_address2, 
                :lein_holder, :lein_holder_address1, :lein_holder_address2, 
                :person_left, :person_left_address1, :person_left_address2,
                :county, :repair_amount, :ready_to_title, :status_downtown, 
                :date_sent_downtown, :lien_canceled, :date_canceled, :transferred_harris_county,
                :cert1, :cert2, :cert3, :cert4, :cert5, :cert6, 
                :cert1_status, :cert2_status, :cert3_status, :cert4_status, :cert5_status, :cert6_status,
                :date_left, :date_completed, :date_notified, :sale_date, :dealer_id
            )
        """, vin_data)

        conn.commit()
        decrement_lien_credit(dealer_id)

        # Optional: warn dealer when only 1 credit left
        remaining_credits = get_available_credits(dealer_id)
        if remaining_credits == 1:
            send_low_credit_email(dealer["name"], dealer["email"])

        # ✅ Add safe defaults for optional fields used in email template
        optional_fields = [
            "cert2", "cert3", "cert4", "cert5", "cert6",
            "cert2_status", "cert3_status", "cert4_status", "cert5_status", "cert6_status"
        ]
        for field in optional_fields:
            vin_data.setdefault(field, "N/A")

        # ✅ Send notification email
        dealer_name = dealer["name"]
        email_1 = dealer.get("email")
        email_2 = dealer.get("email2")
        subject = f"🚗 New Lien Added - {vin_data['vin']}"
        html_body = render_template("email_templates/new_vin_added.html", dealer_name=dealer_name, vin_data=vin_data)

        for email in [email_1, email_2]:
            if email:
                send_email(email, subject, html_body)
                print(f"📧 Sent to {email}")

        flash("✅ VIN added successfully!", "success")
        conn.close()
        return redirect(url_for("dashboard"))

    return render_template("add_vin.html", dealer=dealer)


def combine_address(name, address1, address2):
    """Helper function to format an address by combining name, address1, and address2."""
    parts = [name, address1, address2]
    return ", ".join(filter(None, parts))

app = Flask(__name__)
app.secret_key = "6a973f13b8c14b5eb4b90f78f4c25792e7abff5631e74203ab56a56fe9e8c521"

# Define database path
# DB_PATH = r"C:\Users\marka\Desktop\dealers_and_vins.db"

app.secret_key = os.getenv("SECRET_KEY", "fallback_dev_key")


# Define database path

mechanic_lien_template_path = r"C:\Users\marka\Desktop\mechanic_lien_app\forms\letter_new_new.pdf"


# Define paths
import fitz
import os
from datetime import datetime


# ✅ Ensure the correct export folder exists
export_folder = r"C:\Users\marka\Desktop\Mechanic Lien Work Space"
# Update PDF template directory
pdf_template_path = r"C:\Users\marka\Desktop\mechanic_lien_app\forms"



import fitz  # PyMuPDF
from datetime import datetime


# ✅ Helper Function: Combine Address
def combine_address(name, address1, address2):
    """Formats address fields properly."""
    return f"{name}, {address1}, {address2}".strip(", ")

def generate_mechanic_letter(vin_data, file_path, pdf_template=None):
    """Generates a Mechanic Lien Letter PDF with proper X, Y coordinate placement."""

    if not vin_data:
        flash("⚠ No VIN data provided!", "danger")
        return

    # ✅ Set default template path if not provided
    if pdf_template is None:
        pdf_template = r"C:\Users\marka\Desktop\mechanic_lien_app\static\forms\MechanicLetter.pdf"

    # ✅ Ensure template file exists
    if not os.path.exists(pdf_template):
        flash(f"❌ Error: Mechanic Lien template not found at {pdf_template}", "danger")
        print(f"❌ Error: Mechanic Lien template not found at {pdf_template}")
        return

    # ✅ Open the existing PDF template
    pdf_writer = fitz.open(pdf_template)
    page = pdf_writer[0]  # Use the first page of the PDF

    # ✅ Insert Current Date
    system_date = datetime.now().strftime("%A, %B %d, %Y")
    page.insert_text((57, 185), system_date, fontsize=12)

    # ✅ Dealer Information
    dealer_name = vin_data.get('dealer_name', 'Unknown Dealer')
    dealer_address = vin_data.get('dealer_address', 'Unknown Address')
    dealer_city = vin_data.get('dealer_city', 'Unknown City')
    dealer_state = vin_data.get('dealer_state', 'Unknown State')
    dealer_zip = vin_data.get('dealer_zip', 'Unknown ZIP')
    dealer_phone = vin_data.get('dealer_phone', 'Unknown Phone')

    # ✅ Insert Dealer Details (Header Section)
    page.insert_text((57, 70), dealer_name, fontsize=14)
    page.insert_text((57, 80), dealer_address, fontsize=10)
    page.insert_text((57, 90), f"{dealer_city}, {dealer_state}, {dealer_zip}", fontsize=10)
    page.insert_text((57, 100), dealer_phone, fontsize=10)

    # ✅ Insert Dealer Details (Footer Section)
    page.insert_text((57, 610), dealer_name, fontsize=12)
    page.insert_text((57, 620), dealer_address, fontsize=10)
    page.insert_text((57, 630), f"{dealer_city}, {dealer_state}, {dealer_zip}", fontsize=10)
    page.insert_text((57, 640), dealer_phone, fontsize=10)

    # ✅ Vehicle Details
    vin = vin_data.get('vin', 'Unknown VIN')
    year = vin_data.get('year', 'Unknown Year')
    make = vin_data.get('make', 'Unknown Make')
    model = vin_data.get('model', 'Unknown Model')
    color = vin_data.get('color', 'Unknown Color')
    plate = vin_data.get('plate', 'Unknown Plate')
    repair_amount = f"${float(vin_data['repair_amount']):,.2f}" if vin_data.get('repair_amount') else "N/A"

    page.insert_text((180, 250), vin, fontsize=12)
    page.insert_text((180, 270), f"{year} / {make}", fontsize=12)
    page.insert_text((180, 290), model, fontsize=12)
    page.insert_text((180, 305), color, fontsize=12)
    page.insert_text((180, 325), plate, fontsize=12)
    page.insert_text((180, 342), repair_amount, fontsize=12)

    # ✅ Owner Details
    owner_full = combine_address(
        vin_data.get('owner', 'Unknown Owner'),
        vin_data.get('owner_address1', 'Unknown Address'),
        vin_data.get('owner_address2', '')
    )
    page.insert_text((190, 420), owner_full, fontsize=10)

    # ✅ Renewal Name & Address
    renewal_full = combine_address(
        vin_data.get('renewal', 'Unknown Renewal Name'),
        vin_data.get('renewal_address1', 'Unknown Renewal Address'),
        vin_data.get('renewal_address2', '')
    )
    page.insert_text((190, 445), renewal_full, fontsize=10)

    # ✅ Lien Holder Name & Address
    lien_holder_full = combine_address(
        vin_data.get('lein_holder', 'Unknown Lien Holder'),
        vin_data.get('lein_holder_address1', 'Unknown Lien Address'),
        vin_data.get('lein_holder_address2', '')
    )
    page.insert_text((190, 470), lien_holder_full, fontsize=10)

    # ✅ Person Left Name & Address
    person_left_full = combine_address(
        vin_data.get('person_left', 'Unknown Person'),
        vin_data.get('person_left_address1', 'Unknown Address'),
        vin_data.get('person_left_address2', '')
    )
    page.insert_text((190, 495), person_left_full, fontsize=10)

    # ✅ Certs1 - Certs6 Proper Positioning
    certs = [
        vin_data.get('cert1', ''), vin_data.get('cert2', ''),
        vin_data.get('cert3', ''), vin_data.get('cert4', ''),
        vin_data.get('cert5', ''), vin_data.get('cert6', '')
    ]
    cert_positions = [(370, 250), (370, 270), (370, 290), (370, 310), (370, 330), (370, 350)]

    for i, cert in enumerate(certs):
        if cert:
            page.insert_text(cert_positions[i], cert, fontsize=12)

    # ✅ Save the Completed PDF
    pdf_writer.save(file_path)
    pdf_writer.close()
    print(f"✅ Mechanic Lien Letter saved: {file_path}")
    flash(f"✅ Mechanic Lien Letter saved at: {file_path}", "success")


# -------------------- Home Page --------------------

# -------------------- Dealer Management --------------------
@app.route("/view_dealers")
def view_dealers():
    role = session.get("role")
    dealer_id = session.get("dealer_id")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()


    # Check user role and fetch appropriate data
    if session.get("role") == "dealer":
        cursor.execute("SELECT * FROM dealers WHERE dealer_id = ?", (session.get("dealer_id"),))
    else:
        cursor.execute("SELECT * FROM dealers ORDER BY name ASC")  # Admin sees all

    if role == "dealer" and dealer_id:
        cursor.execute("SELECT * FROM dealers WHERE dealer_id = ?", (dealer_id,))
    else:  # admin
        cursor.execute("SELECT * FROM dealers ORDER BY name")


    dealers = cursor.fetchall()
    conn.close()

    return render_template("view_dealers.html", dealers=dealers)

@app.route("/add_dealer", methods=["GET", "POST"])
def add_dealer():
    # Only allow admin to access
    if session.get("role") != "admin":
        flash("❌ Unauthorized access. Admins only.", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        dealer_data = {key: request.form.get(key, "") for key in request.form}
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO dealers 
            (name, pnumber, address, city, state, zip, phone, email, email2, associate1, associate1tdl, associate2, associate2cell, expdate) 
            VALUES (:name, :pnumber, :address, :city, :state, :zip, :phone, :email, :email2, :associate1, :associate1tdl, :associate2, :associate2cell, :expdate)
        """, dealer_data)
        conn.commit()
        conn.close()
        flash("✅ Dealer added successfully!")
        return redirect(url_for("view_dealers"))

    return render_template("add_dealer.html")

@app.route("/edit_dealer/<int:dealer_id>", methods=["GET", "POST"])
def edit_dealer(dealer_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == "POST":
        dealer_data = {key: request.form.get(key, "") for key in request.form}
        dealer_data["dealer_id"] = dealer_id

        cursor.execute("""
            UPDATE dealers SET 
                name = :name, pnumber = :pnumber, address = :address, city = :city, state = :state, zip = :zip, 
                phone = :phone, email = :email, email2 = :email2, associate1 = :associate1, associate1tdl = :associate1tdl, 
                associate2 = :associate2, associate2cell = :associate2cell, expdate = :expdate
            WHERE dealer_id = :dealer_id
        """, dealer_data)

        conn.commit()
        conn.close()
        flash("✅ Dealer updated successfully!")
        return redirect(url_for("view_dealers"))

    cursor.execute("SELECT * FROM dealers WHERE dealer_id = ?", (dealer_id,))
    dealer = cursor.fetchone()
    conn.close()

    return render_template("edit_dealer.html", dealer=dealer)

# -------------------- VIN Management --------------------
@app.route("/search_vin", methods=["GET", "POST"])
def search_vin():
    """Search for a VIN by the last 4 digits and retrieve Dealer info."""
    vins = []
    if request.method == "POST":
        last_4_vin = request.form.get("last_4_vin").strip()
        if last_4_vin:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 🔹 Fetch VIN details and associated Dealer
            cursor.execute("""
    SELECT vins.*, dealers.name AS dealer_name, dealers.address AS dealer_address, 
            dealers.city AS dealer_city, dealers.state AS dealer_state, dealers.zip AS dealer_zip, 
            dealers.phone AS dealer_phone
    FROM vins
    LEFT JOIN dealers ON vins.dealer_id = dealers.dealer_id
    WHERE vins.vin LIKE ?
""", ('%' + last_4_vin,))


            vins = cursor.fetchall()
            conn.close()

            if not vins:
                flash("⚠ No matching VIN found!", "danger")

    return render_template("search_vin.html", vins=vins)

@app.route("/select_vin/<int:vin_id>")
def select_vin(vin_id):
    """Select a VIN and store the entire record in session, including dealer info."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 🔹 Fetch VIN details along with Dealer information
    cursor.execute("""
    SELECT vins.*, dealers.name AS dealer_name, dealers.address AS dealer_address, 
            dealers.city AS dealer_city, dealers.state AS dealer_state, dealers.zip AS dealer_zip, 
            dealers.phone AS dealer_phone, dealers.pnumber, dealers.associate1, dealers.associate1tdl, dealers.associate2
    FROM vins
    LEFT JOIN dealers ON vins.dealer_id = dealers.dealer_id
    WHERE vins.rowid = ?
""", (vin_id,))


    selected_vin = cursor.fetchone()
    conn.close()

    if not selected_vin:
        flash("⚠ VIN not found!", "danger")
        return redirect(url_for("search_vin"))  # ✅ Ensures redirection happens in case of an error

    # ✅ Store entire VIN + Dealer info in session
    session["selected_vin"] = dict(selected_vin)
    session["dealer_details"] = {
        "name": selected_vin["dealer_name"],
        "address": selected_vin["dealer_address"],
        "city": selected_vin["dealer_city"],
        "state": selected_vin["dealer_state"],
        "zip": selected_vin["dealer_zip"],
        "phone": selected_vin["dealer_phone"],
        "associate1": selected_vin["associate1"],
        "associate1tdl": selected_vin["associate1tdl"],
        "associate2": selected_vin["associate2"],
    }

    # Debugging
    print(f"✅ Stored VIN & Dealer Data in Session: {session['selected_vin']}")
    print(f"✅ Stored Dealer Details in Session: {session['dealer_details']}")

    flash(f"✅ Selected VIN: {selected_vin['vin']} ({selected_vin['year']} {selected_vin['make']} {selected_vin['model']})", "success")

    return redirect(url_for("select_forms"))  # ✅ Now properly redirects to form selection

@app.route("/edit_vin/<vin_id>", methods=["GET", "POST"])
def edit_vin(vin_id):
    """Allows editing of a VIN record and updating it in the database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == "POST":

        # ✅ Capture form data (including status)
        vin = request.form.get("vin", "").strip()
        year = request.form.get("year", "").strip()
        make = request.form.get("make", "").strip()
        model = request.form.get("model", "").strip()
        body = request.form.get("body", "").strip()
        color = request.form.get("color", "").strip()
        plate = request.form.get("plate", "").strip()
        weight = request.form.get("weight", "").strip()
        cweight = request.form.get("cweight", "").strip()
        odometer = request.form.get("odometer", "").strip()
        repair_amount = request.form.get("repair_amount", "").strip()
        county = request.form.get("county", "").strip()
        owner = request.form.get("owner", "").strip()
        owner_address1 = request.form.get("owner_address1", "").strip()
        owner_address2 = request.form.get("owner_address2", "").strip()
        renewal = request.form.get("renewal", "").strip()
        renewal_address1 = request.form.get("renewal_address1", "").strip()
        renewal_address2 = request.form.get("renewal_address2", "").strip()
        lein_holder = request.form.get("lein_holder", "").strip()
        lein_holder_address1 = request.form.get("lein_holder_address1", "").strip()
        lein_holder_address2 = request.form.get("lein_holder_address2", "").strip()
        person_left = request.form.get("person_left", "").strip()
        person_left_address1 = request.form.get("person_left_address1", "").strip()
        person_left_address2 = request.form.get("person_left_address2", "").strip()
        date_left = request.form.get("date_left", "").strip()
        date_completed = request.form.get("date_completed", "").strip()
        date_notified = request.form.get("date_notified", "").strip()
        sale_date = request.form.get("sale_date", "").strip()
        status = request.form.get("status", "").strip()  # ✅ Capture the status

        # ✅ Update the database
        cursor.execute("""

        vin_data = {key: request.form.get(key, "") for key in request.form}

        # Handle cert status updates
        cert_status_fields = [request.form.get(f"cert{i}_status", "").strip() for i in range(1, 7)]

        cursor.execute(f"""

            UPDATE vins SET
                vin = ?, year = ?, make = ?, model = ?, body = ?, color = ?, 
                plate = ?, weight = ?, cweight = ?, odometer = ?, repair_amount = ?, 
                county = ?, owner = ?, owner_address1 = ?, owner_address2 = ?, 
                renewal = ?, renewal_address1 = ?, renewal_address2 = ?, 
                lein_holder = ?, lein_holder_address1 = ?, lein_holder_address2 = ?, 
                person_left = ?, person_left_address1 = ?, person_left_address2 = ?, 
                date_left = ?, date_completed = ?, date_notified = ?, sale_date = ?, 

                status = ?
            WHERE vin = ?
        """, (
            vin, year, make, model, body, color, plate, weight, cweight, odometer,
            repair_amount, county, owner, owner_address1, owner_address2, renewal, 
            renewal_address1, renewal_address2, lein_holder, lein_holder_address1, 
            lein_holder_address2, person_left, person_left_address1, person_left_address2, 
            date_left, date_completed, date_notified, sale_date, status, vin_id

                status = ?, 
                cert1_status = ?, cert2_status = ?, cert3_status = ?, 
                cert4_status = ?, cert5_status = ?, cert6_status = ?
            WHERE vin = ?
        """, (
            vin_data["vin"], vin_data["year"], vin_data["make"], vin_data["model"], vin_data["body"], vin_data["color"],
            vin_data["plate"], vin_data["weight"], vin_data["cweight"], vin_data["odometer"],
            vin_data["repair_amount"], vin_data["county"], vin_data["owner"], vin_data["owner_address1"],
            vin_data["owner_address2"], vin_data["renewal"], vin_data["renewal_address1"], vin_data["renewal_address2"],
            vin_data["lein_holder"], vin_data["lein_holder_address1"], vin_data["lein_holder_address2"],
            vin_data["person_left"], vin_data["person_left_address1"], vin_data["person_left_address2"],
            vin_data["date_left"], vin_data["date_completed"], vin_data["date_notified"], vin_data["sale_date"],
            vin_data["status"], *cert_status_fields, vin_id

        ))

        conn.commit()
        conn.close()


        # ✅ Redirect to view the updated record
        return redirect(url_for("view_vin", vin_id=vin_id))

    # ✅ Fetch VIN data for GET request (displaying the form)

        flash("✅ VIN updated successfully!")
        return redirect(url_for("dashboard"))

    # ✅ Get the record to populate the form

    cursor.execute("SELECT * FROM vins WHERE vin = ?", (vin_id,))
    vin = cursor.fetchone()
    conn.close()


    return render_template("view_vin.html", vin=vin)  # ✅ View & Edit in same page

    if vin:
        return render_template("edit_vin.html", vin=vin)
    else:
        flash("❌ VIN not found.")
        return redirect(url_for("dashboard"))



# -------------------- Mechanic Lien Letter Generation --------------------
@app.route("/select_dealer_for_vin")
def select_dealer_for_vin():
    """Displays the list of dealers to select for adding a VIN."""

    role = session.get("role")
    dealer_id = session.get("dealer_id")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if role == "dealer" and dealer_id:
        # Only show the dealer's own info
        cursor.execute("SELECT * FROM dealers WHERE dealer_id = ?", (dealer_id,))
    else:
        # Admins can see all
        cursor.execute("SELECT * FROM dealers ORDER BY name ASC")

    dealers = cursor.fetchall()
    conn.close()

    return render_template("select_dealer_for_vin.html", dealers=dealers)



from werkzeug.utils import secure_filename
import smtplib
from email.message import EmailMessage

# ✅ Place this somewhere in your config
TESTING_MODE = False
STATIC_FORMS_PATH = os.path.join("static", "forms")

from flask import current_app
from datetime import datetime

@app.route("/generate_forms", methods=["GET", "POST"])
def generate_forms():
    if "selected_vin" not in session or "selected_forms" not in session:
        flash("⚠ Missing VIN or form selection. Start over!", "danger")
        return redirect(url_for("search_vin"))

    vin_data = session["selected_vin"]
    selected_forms = session["selected_forms"]
    dealer_name = vin_data.get("dealer_name", "UnknownDealer").replace(" ", "_")
    vin = vin_data.get("vin", "UnknownVIN")

    form_templates_dir = r"C:\Users\marka\Desktop\mechanic_lien_app\static\forms"
    static_forms_dir = os.path.join(current_app.root_path, STATIC_FORMS_PATH)
    os.makedirs(static_forms_dir, exist_ok=True)

    generated_forms = []

    for form in selected_forms:
        filename = f"{dealer_name}_{vin}_{form}.pdf"
        safe_filename = secure_filename(filename)
        form_path = os.path.join(static_forms_dir, safe_filename)
        template_filename = f"{form.replace('-', '').replace(' ', '')}.pdf"
        pdf_template = os.path.join(form_templates_dir, template_filename)

        if not os.path.exists(pdf_template):
            flash(f"❌ Error: Form template not found at {pdf_template}", "danger")
            continue

        try:
            if form == "130-U":
                generate_130u_form(vin_data, form_path, pdf_template)
            elif form == "MV-265-M-2":
                generate_mv265m2_form(vin_data, form_path, pdf_template)
            elif form == "VTR-265-FM":
                generate_vtr265fm_form(vin_data, form_path, pdf_template)
            elif form == "TS-5a":
                generate_ts5a_form(vin_data, form_path, pdf_template)
            elif form == "TS-12":
                generate_ts12_form(vin_data, form_path, pdf_template)
            elif form == "POPO":
                generate_popo_form(vin_data, form_path, pdf_template)
            elif form == "VTR-34":
                generate_vtr34_form(vin_data, form_path, pdf_template)
            elif form == "VTR-270":
                generate_vtr270_form(vin_data, form_path, pdf_template)
            elif form == "VTR-130-SOF":
                generate_bonded_title_form(vin_data, form_path, pdf_template)
            elif form == "Mechanic Letter":
                generate_mechanic_letter(vin_data, form_path, pdf_template)
            else:
                flash(f"⚠ Unknown form selected: {form}", "warning")
                continue

            generated_forms.append((safe_filename, form_path))

        except Exception as e:
            flash(f"❌ Error generating {form}: {e}", "danger")

    # ✅ Email generated forms as attachments
    if generated_forms:
        role = session.get("role")
        if TESTING_MODE or role == "admin":
            recipient_email = "markacaffey@gmail.com"
        else:
            recipient_email = vin_data.get("dealer_email")
            if not recipient_email:
                # fallback: query dealer
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                cur.execute("SELECT email FROM dealers WHERE dealer_id = ?", (vin_data["dealer_id"],))
                row = cur.fetchone()
                recipient_email = row[0] if row else None
                conn.close()

        if recipient_email:
            try:
                email_forms_with_attachments(
                    generated_forms,
                    recipient_email,
                    vin=vin,
                    dealer_name=vin_data.get("dealer_name", "Dealer")
                )
                flash(f"✅ Forms emailed to {recipient_email}", "info")
            except Exception as e:
                print("❌ Email send error:", e)
                flash("⚠ Email failed to send.", "warning")
        else:
            flash("⚠ No dealer email found. Could not send email.", "warning")

        flash(f"✅ Forms generated: {', '.join([f[0] for f in generated_forms])}", "success")
    else:
        flash("⚠ No forms were successfully generated.", "warning")

    session.pop("selected_vin", None)
    session.pop("selected_forms", None)
    return redirect(url_for("search_vin"))



@app.route("/clear_session")
def clear_session():
    """Clear session data."""
    session.clear()
    return "Session cleared!"

@app.route("/select_forms", methods=["GET", "POST"])
def select_forms():
    """Allow the user to select forms to generate for the selected VIN."""
    if "selected_vin" not in session:
        flash("⚠ No VIN selected. Please search for a VIN first!", "danger")
        return redirect(url_for("search_vin"))

    # ✅ Ensure all forms are listed
    available_forms = [
        "Mechanic Letter", "130-U", "MV-265-M-2", "VTR-265-FM",
        "TS-5a", "TS-12", "POPO", "VTR-34", "VTR-130-SOF"  # ✅ Add Bonded Title Form
    ]

    if request.method == "POST":
        selected_forms = request.form.getlist("forms")

        if not selected_forms:
            flash("⚠ Please select at least one form!", "warning")
            return redirect(url_for("select_forms"))

        session["selected_forms"] = selected_forms
        return redirect(url_for("generate_forms"))

    return render_template("select_forms.html", available_forms=available_forms)





@app.route("/dealer/add_vin", methods=["GET", "POST"])
def dealer_add_vin():
    """Dealer route to add VIN using their own session dealer ID."""

    role = session.get("role")
    dealer_id = session.get("dealer_id")

    if role != "dealer" or not dealer_id:
        flash("Unauthorized access. Please log in.", "danger")
        return redirect(url_for("login"))

    return redirect(url_for("add_vin", dealer_id=dealer_id))

#------------------FIND CERTIFIED LETTERS AND SEND EMAIL ----------------------------------------------
import sqlite3
from datetime import datetime

import sqlite3
from datetime import datetime

# Define database path

# DB_PATH = r"C:\Users\marka\Desktop\dealers_and_vins.db"




# ✅ Fix: Define the missing function
def get_db_connection():
    """Establish and return a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Allows fetching rows as dictionaries
    return conn


import sqlite3
from flask import request, redirect, url_for, flash, render_template
from datetime import datetime

@app.route("/certify_tracking", methods=["GET", "POST"])
def certify_tracking():

    """Processes certified letter tracking and updates cert1_status through cert6_status upon sending an email."""


    """Update certified letter status and notify dealer."""


    vin_data_list = []
    selected_vin_data = None
    status_field = None
    full_cert = None

    conn = None  

    new_status = None
    conn = None


    if request.method == "POST":
        cert_last6 = request.form.get("cert_last6", "").strip()
        confirm_cert = request.form.get("confirm_cert") == "1"
        selected_vin = request.form.get("selected_vin", "")
        print(f"🧩 confirm_cert checkbox value: {confirm_cert}")
        print(f"🔍 Searching for Certified Letter ending in: {cert_last6}")

        try:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT vins.*, vins.rowid AS rowid FROM vins 
                WHERE substr(cert1, -6) = ? OR substr(cert2, -6) = ? OR substr(cert3, -6) = ? 
                        OR substr(cert4, -6) = ? OR substr(cert5, -6) = ? OR substr(cert6, -6) = ?
            """, (cert_last6,) * 6)

            rows = cursor.fetchall()
            for row in rows:
                vin_dict = dict(row)
                vin_dict["rowid"] = row["rowid"]
                vin_data_list.append(vin_dict)

            for vin in vin_data_list:
                if selected_vin and vin["vin"] != selected_vin:
                    continue
                for i in range(1, 7):
                    cert_key = f"cert{i}"
                    if vin.get(cert_key, "").endswith(cert_last6):
                        selected_vin_data = vin
                        full_cert = vin[cert_key]
                        status_field = f"cert{i}_status"
                        break
                if selected_vin_data:
                    break

            if not selected_vin_data or not status_field:
                flash("❌ Certified number not linked to any VIN field.", "danger")
                return render_template("certify_tracking.html", vin_data_list=vin_data_list)

            vin_id = selected_vin_data.get("rowid")
            new_status = f"Delivered - {datetime.today().strftime('%Y-%m-%d')}"
            print(f"🧪 About to update rowid {vin_id} | {status_field} = '{new_status}'")

            if confirm_cert and vin_id and status_field:
                cursor.execute(f"UPDATE vins SET {status_field} = ? WHERE rowid = ?", (new_status, vin_id))
                conn.commit()


                        if confirm_cert and full_cert and selected_vin and status_field:
                            new_status = f"DELIVERED ON {datetime.today().strftime('%Y-%m-%d')}"
                            update_query = f"UPDATE vins SET {status_field} = ? WHERE vin = ?"

                            try:
                                cursor.execute(update_query, (new_status, selected_vin))
                                conn.commit()

                                cursor.execute(
                                    f"SELECT vin, {status_field} FROM vins WHERE vin = ?",
                                    (selected_vin,)
                                )
                                updated_record = cursor.fetchone()

                # Confirm update
                cursor.execute("SELECT vins.*, vins.rowid AS rowid FROM vins WHERE rowid = ?", (vin_id,))
                updated_row = cursor.fetchone()
                if updated_row and updated_row[status_field] == new_status:
                    flash("✅ Certification updated successfully!", "success")
                    selected_vin_data = dict(updated_row)
                    selected_vin_data["rowid"] = updated_row["rowid"]
                else:
                    flash("❌ Database update verification failed.", "danger")
                    return render_template("certify_tracking.html", vin_data_list=vin_data_list)

            # Email notification
            dealer_id = selected_vin_data.get("dealer_id")
            cursor.execute("SELECT name, email, email2 FROM dealers WHERE dealer_id = ?", (dealer_id,))
            dealer_row = cursor.fetchone()
            dealer_row = dict(dealer_row) if dealer_row else {}
            dealer_name = dealer_row.get("name", "Dealer")

            cert_table_rows = "".join(
                f"<tr><td>Cert{i}</td><td>{selected_vin_data.get(f'cert{i}', '')}</td>"
                f"<td>{selected_vin_data.get(f'cert{i}_status', '')}</td></tr>"
                for i in range(1, 7) if selected_vin_data.get(f'cert{i}')
            )


            subject = f"Mechanic Lien Update: {selected_vin_data['vin']}"
            email_body = render_template(
                "email_templates/lien_update.html",
                vin_data=selected_vin_data,
                dealer_name=dealer_name,
                cert_table_rows=cert_table_rows,
                new_status=new_status or "No update made"
            )

            dealer_emails = [dealer_row.get("email"), dealer_row.get("email2")]
            dealer_emails = [e for e in dealer_emails if e]

            for email in dealer_emails:
                print(f"📧 Sending email to: {email}")
                send_email(email, subject, email_body)

            flash(f"✅ Email successfully sent to {len(dealer_emails)} recipient(s).", "success")
            return redirect(url_for("certify_tracking"))

        except sqlite3.Error as e:
            flash(f"❌ Database error: {e}", "danger")
            print(f"❌ SQLite error: {e}")
        finally:
            if conn:
                conn.close()

    return render_template("certify_tracking.html", vin_data_list=vin_data_list)



@app.route("/update_cert_status", methods=["POST"])
def update_cert_status():
    """Updates the certified letter status as delivered and notifies the dealer."""

    vin_id = request.form.get("vin_id")
    matched_status_field = request.form.get("matched_status_field")
    matched_cert = request.form.get("matched_cert")

    if not vin_id or not matched_status_field or not matched_cert:
        flash("⚠ Missing information for update!", "danger")
        return redirect(url_for("certify_tracking"))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # ✅ Update the status to "Delivered - {current date}"
    system_date = datetime.now().strftime("%Y-%m-%d")
    update_query = f"UPDATE vins SET {matched_status_field} = ? WHERE id = ?"
    cursor.execute(update_query, (f"Delivered - {system_date}", vin_id))
    conn.commit()

    # ✅ Fetch updated VIN and Dealer in the same connection
    cursor.execute("SELECT * FROM vins WHERE id = ?", (vin_id,))
    vin_record = cursor.fetchone()

    dealer = None
    if vin_record and vin_record["dealer_id"]:
        cursor.execute("SELECT * FROM dealers WHERE dealer_id = ?", (vin_record["dealer_id"],))
        dealer = cursor.fetchone()

    conn.close()  # ✅ Close only after you're done

    # ✅ Send email
    if dealer and dealer["email"]:
        subject = f"📜 Certified Letter Delivered - VIN {vin_record['vin']}"
        body = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Certified Letter Delivered</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: auto; background: #ffffff; padding: 20px; border-radius: 10px; border: 1px solid #ddd;">

                <div style="background: #28a745; color: #ffffff; padding: 15px; text-align: center; font-size: 20px; border-radius: 10px 10px 0 0;">
                    📜 Certified Letter Delivered
                </div>

                <div style="padding: 15px;">
                    <p>Dear <strong>{dealer['name']}</strong>,</p>
                    <p>The following certified letter has been successfully delivered:</p>

                    <div class="card border-primary">
                        <div class="card-header bg-primary text-white"><strong>📜 Certification Details</strong></div>
                        <div class="card-body">
                            <table class="table table-bordered">
                                <tr><th>VIN</th><td>{vin_record['vin']}</td></tr>
                                <tr><th>Full Cert Number</th><td>{matched_cert}</td></tr>
                                <tr><th>Delivered On</th><td>{system_date}</td></tr>
                            </table>
                        </div>
                    </div>

                    <p>Best Regards,<br><strong>The Mechanic Lien Team</strong></p>
                </div>
            </div>
        </body>
        </html>
        """

        send_dealer_email(dealer["email"], subject, body)

@app.route("/certified_log")
def certified_log():
    """Show Certified Tracking Log."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT vin, year, make, model, dealer_id, cert1, cert1_status, cert2, cert2_status, 
                cert3, cert3_status, cert4, cert4_status, cert5, cert5_status, cert6, cert6_status
        FROM vins
        ORDER BY date_notified DESC
    """)
    vins = cursor.fetchall()
    conn.close()

    vin_data_list = []
    for vin in vins:
        for i in range(1, 7):
            cert = vin[f"cert{i}"]
            status = vin[f"cert{i}_status"]
            if cert:
                vin_data_list.append({
                    "vin": vin["vin"],
                    "year": vin["year"],
                    "make": vin["make"],
                    "model": vin["model"],
                    "cert": cert,
                    "status": status,
                    "dealer_id": vin["dealer_id"]
                })

    return render_template("certified_log.html", vin_data_list=vin_data_list)


@app.route("/update_cert_status", methods=["POST"])
def update_cert_status():
    if session.get("role") != "admin":
        flash("Unauthorized access.", "danger")
        return redirect(url_for("login"))

    if cert_number not in range(1, 7):
        flash("Invalid certification number. Must be between 1–6.", "danger")
        return redirect(url_for("dashboard"))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()


    # Step 1: Get VIN record
    cursor.execute("SELECT * FROM vins WHERE rowid = ?", (vin_id,))
    vin_row = cursor.fetchone()
    if not vin_row:
        flash("⚠ VIN not found.", "danger")
        return redirect(url_for("dashboard"))

    vin = dict(vin_row)
    status_field = f"cert{cert_number}_status"
    today = datetime.today().strftime("%Y-%m-%d")
    new_status = f"Returned - {today}"

    # Step 2: Update cert status in DB and commit
    cursor.execute(f"""
        UPDATE vins SET {status_field} = ? WHERE rowid = ?
    """, (new_status, vin_id))
    conn.commit()

    # Step 3: Re-fetch updated VIN to confirm
    cursor.execute("SELECT * FROM vins WHERE rowid = ?", (vin_id,))
    vin = dict(cursor.fetchone())
    print(f"🧪 Confirmed DB value for {status_field}: {vin[status_field]}")

    # Step 4: Fetch dealer info
    cursor.execute("SELECT * FROM dealers WHERE dealer_id = ?", (vin["dealer_id"],))
    dealer_row = cursor.fetchone()
    conn.close()

    if not dealer_row:
        flash("⚠ Dealer not found for this VIN.", "danger")
        return redirect(url_for("dashboard"))

    dealer = dict(dealer_row)

    # Step 5: Email body with formatted table
    subject = f"📬 Certified Letter Returned - VIN {vin['vin']}"
    body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background-color: #fff; border-radius: 8px; padding: 20px; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
        <h2 style="background-color: #dc3545; color: white; padding: 10px; border-radius: 5px; text-align: center;">📬 Certified Letter Returned</h2>

        <p>Dear <strong>{dealer['name']}</strong>,</p>

        <p>The following certified letter has been returned for one of your active lien records:</p>

        <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
            <tr style="background-color: #f0f0f0;">
                <th style="padding: 8px; border: 1px solid #ddd;">VIN</th>
                <th style="padding: 8px; border: 1px solid #ddd;">Certification</th>
                <th style="padding: 8px; border: 1px solid #ddd;">Status</th>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">{vin['vin']}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">cert{cert_number}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{vin[status_field]}</td>
            </tr>
        </table>

        <p style="margin-top: 20px;">Please log in to your dashboard to take any required action.</p>

        <p>Thank you,<br><strong>The Mechanic Lien Team</strong></p>
        </div>
        </body>
    </html>
    """

    # Step 6: Send to both emails
    emails = [dealer.get("email"), dealer.get("email2")]
    print(f"📨 Attempting to send to: {emails}")

    for email in emails:
        if email:
            try:
                send_dealer_email(email, subject, body)
                print(f"✅ Return email sent to {email}")
            except Exception as e:
                print(f"❌ Failed to send to {email}: {e}")
        else:
            print("⚠ Skipped empty email slot.")

    flash(f"✅ Simulated cert{cert_number} returned and email sent.", "success")
    return redirect(url_for("dashboard"))



#------------FORMS----------------------------------------------------------------------

import fitz

import os
import fitz  # PyMuPDF

def generate_mv265m2_form(vin_data, file_path, pdf_template):
    """Generates the MV-265-M-2 form using the correct X, Y coordinates."""

    # Ensure the template exists
    if not os.path.exists(pdf_template):
        flash(f"❌ Error: Form template not found at {pdf_template}", "danger")
        print(f"❌ Error: Form template not found at {pdf_template}")
        return

    # Open the template PDF
    pdf_writer = fitz.open(pdf_template)
    page = pdf_writer[0]  # Use the first page of the form

    # Define X, Y coordinates for required fields
    field_positions = {
        'vin': (130, 160),
        'year': (130, 190),
        'make': (180, 190),
        'date_notified': (420, 160),
        'date_completed': (420, 190),
        'sale_date': (420, 220),
        'name': (130, 220)  # 'name' should be dealer_name
    }

    # Insert data into the PDF
    for field, position in field_positions.items():
        if field == "name":  # Fetch dealer name instead of VIN data
            value = vin_data.get("dealer_name", "Unknown Dealer")
        else:
            value = vin_data.get(field, "N/A")
        page.insert_text(position, value, fontsize=12)

    # Save the completed form
    pdf_writer.save(file_path)
    pdf_writer.close()

    flash(f"✅ MV-265-M-2 Form saved: {file_path}", "success")
    print(f"✅ [DEBUG] MV-265-M-2 form generated at {file_path}")

import os
import fitz  # PyMuPDF
import time


def generate_130u_form(vin_data, file_path, pdf_template):
    """Generates the 130-U form with the correct X, Y coordinates and prevents permission issues."""

    # ✅ Ensure the template exists
    if not os.path.exists(pdf_template):
        flash(f"❌ Error: 130-U template not found at {pdf_template}", "danger")
        print(f"❌ Error: 130-U template not found at {pdf_template}")
        return

    try:
        # ✅ Open the template PDF
        pdf_writer = fitz.open(pdf_template)
        page = pdf_writer[0]  # Use the first page of the form

        # ✅ Extract dealer details
        dealer_name = vin_data.get("dealer_name", "Unknown Dealer")
        dealer_address = vin_data.get("dealer_address", "Unknown Address")
        dealer_city = vin_data.get("dealer_city", "Unknown City")
        dealer_state = vin_data.get("dealer_state", "Unknown State")
        dealer_zip = vin_data.get("dealer_zip", "Unknown ZIP")

        # ✅ Extract `pnumber` from Dealer Data
        pnumber = vin_data.get("pnumber", "N/A")  # Check if `pnumber` exists
        print(f"✅ Debug: Extracted pnumber: {pnumber}")  # Debugging print

        # ✅ Combine dealer address
        combined_dealer_address = f"{dealer_address}, {dealer_city}, {dealer_state} {dealer_zip}"

        # ✅ Combine second dealer name + city + state
        combined_dealer_name_city_state = f"{dealer_name}, {dealer_city}, {dealer_state}"

        # ✅ Define X, Y coordinates for required fields
        field_positions = {
            'vin': (50, 105),
            'year': (250, 105),
            'make': (300, 105),
            'model': (430, 105),
            'body': (380, 105),
            'color': (480, 105),
            'odometer': (140, 130),
            'plate': (50, 130),
            'weight': (430, 130),
            'cweight': (350, 120),
            'repair_amount': (250, 550),
            'county': (495, 280),

            # ✅ PNUMBER FIELDS
            'pnumber': (400, 305),  # First Dealer PNumber
            'pnumber_dup': (500, 503),  # Second Dealer PNumber (Duplicate)

            # ✅ Dealer Name & Address Fields
            'name': (50, 225),  # Dealer Name
            'combined_dealer_address': (50, 280),  # Combined Dealer Address
            'combined_dealer_name_city_state': (50, 305),  # Second Dealer Name + City + State

            'associate1': (300, 730),
            'associate1tdl': (430, 158),
            'associate2': (300, 700)
        }

        # ✅ Insert Data into the PDF
        for field, position in field_positions.items():
            if field == "combined_dealer_address":  
                value = combined_dealer_address  # ✅ First Combined Address
            elif field == "combined_dealer_name_city_state":
                value = combined_dealer_name_city_state  # ✅ Second Dealer Name + City + State
            elif field in ["pnumber", "pnumber_dup"]:  
                value = pnumber  # ✅ Ensure both pnumber fields are filled
            elif field == "name":
                value = dealer_name  # ✅ Dealer Name
            else:
                value = vin_data.get(field, "N/A")

            print(f"✅ Debug: Writing {field} -> {value} at {position}")  # Debugging print
            page.insert_text(position, value, fontsize=12)

        # ✅ **Ensure the PDF file is closed before saving**
        pdf_writer.save(file_path)
        pdf_writer.close()

        # ✅ **Wait for a small delay to ensure the file is released (optional)**
        time.sleep(0.5)

        flash(f"✅ 130-U Form saved at {file_path}", "success")
        print(f"✅ [DEBUG] 130-U form generated at {file_path}")

    except Exception as e:
        flash(f"❌ Error generating 130-U: {e}", "danger")
        print(f"❌ Error generating 130-U: {e}")


def generate_ts5a_form(vin_data, file_path, pdf_template):
    """Generates the TS-5a form with correct X, Y coordinates."""

    if not os.path.exists(pdf_template):
        flash(f"❌ Error: Form template not found at {pdf_template}", "danger")
        return

    pdf_writer = fitz.open(pdf_template)  # ✅ Open the TS-5a form template
    page = pdf_writer[0]  # First page of the PDF

    # 🔹 Define the X, Y coordinates for TS-5a form fields
    form_fields = {
        'sale_date': (450, 165),
        'plate': (420, 190),
        'vin': (350, 210),
        'name': (70, 270),  # Dealer Name
        'address': (75, 297),  # Dealer Address
        'combined_city_state_zip': (55, 325)  # Dealer City, State, ZIP
    }

    # 🔹 Fetch required data
    dealer_name = vin_data.get('dealer_name', 'N/A')
    dealer_address = vin_data.get('dealer_address', 'N/A')
    dealer_city = vin_data.get('dealer_city', 'N/A')
    dealer_state = vin_data.get('dealer_state', 'N/A')
    dealer_zip = vin_data.get('dealer_zip', 'N/A')

    # 🔹 Format City, State, ZIP into a single line
    combined_city_state_zip = f"{dealer_city}, {dealer_state} {dealer_zip}"

    # 🔹 Insert data into the form
    page.insert_text(form_fields['sale_date'], vin_data.get('sale_date', 'N/A'), fontsize=12)
    page.insert_text(form_fields['plate'], vin_data.get('plate', 'N/A'), fontsize=12)
    page.insert_text(form_fields['vin'], vin_data.get('vin', 'N/A'), fontsize=12)
    page.insert_text(form_fields['name'], dealer_name, fontsize=12)  # Dealer Name
    page.insert_text(form_fields['address'], dealer_address, fontsize=12)  # Dealer Address
    page.insert_text(form_fields['combined_city_state_zip'], combined_city_state_zip, fontsize=12)  # City, State, ZIP

    # ✅ Save the completed form
    pdf_writer.save(file_path)
    pdf_writer.close()

    flash(f"✅ TS-5a Form saved: {file_path}", "success")
    print(f"✅ TS-5a Form successfully written to {file_path}")

def generate_vtr265fm_form(vin_data, file_path, pdf_template):
    """Generates the VTR-265-FM form with correct X, Y coordinate placement."""

    if not vin_data:
        flash("⚠ No VIN data provided!", "danger")
        return

    # Open the existing VTR-265-FM PDF template
    try:
        pdf_writer = fitz.open(pdf_template)
        page = pdf_writer[0]  # Use the first page of the PDF
    except Exception as e:
        flash(f"❌ Error opening VTR-265-FM form template: {e}", "danger")
        return

    # Define coordinates for fields
    field_coordinates = {
        'vin': (50, 130),
        'year': (270, 130),
        'make': (350, 130),
        'body': (425, 130),
        'model': (500, 130),
        'plate': (50, 152),
        'owner': (270, 152),
        'name': (50, 200),
        'address': (50, 225),
        'city': (250, 225),
        'state': (380, 225),
        'zip': (420, 225),
        'pnumber': (430, 200),  # Ensure this is correct
        'leftname': (290, 300),
        'person_left_add_combined': (50, 275),
        'date_left': (106, 322),
        'date_completed': (230, 322),
        'repair_amount': (350, 322),
        'repair_amount_dup': (510, 392),
        'date_notified': (106, 372),
        'sale_date': (106, 392),
        'odometer': (280, 523),
        'associate1_dup': (375, 695),
        'associate2_dup': (280, 660),
        'person_left': (50, 250),
        'name_dup': (106, 416),
        'combined_dealer_address': (106, 440),
        'combined_dealer_address_2': (200, 395),
    }

    # Extract dealer details
    dealer_name = vin_data.get('dealer_name', 'Unknown Dealer')
    dealer_address = vin_data.get('dealer_address', 'Unknown Address')
    dealer_city = vin_data.get('dealer_city', 'Unknown City')
    dealer_state = vin_data.get('dealer_state', 'Unknown State')
    dealer_zip = vin_data.get('dealer_zip', 'Unknown ZIP')
    dealer_phone = vin_data.get('dealer_phone', 'Unknown Phone')

    # Associate Information
    associate1 = vin_data.get('associate1', 'Unknown Associate1')
    associate1tdl = vin_data.get('associate1tdl', 'Unknown TDL')
    associate2 = vin_data.get('associate2', 'Unknown Associate2')

    # Combined dealer address fields
    combined_dealer_address = f"{dealer_address}, {dealer_city}, {dealer_state} {dealer_zip}"

    # Extract pnumber (Ensure it's printed for debugging)
    pnumber = vin_data.get('pnumber', 'N/A')
    print(f"🔹 Debug: pnumber = {pnumber}")  # Check if this prints correctly

    # Data Mapping
    form_data = {
        'vin': vin_data.get('vin', ''),
        'year': vin_data.get('year', ''),
        'make': vin_data.get('make', ''),
        'body': vin_data.get('body', ''),
        'model': vin_data.get('model', ''),
        'plate': vin_data.get('plate', ''),
        'owner': vin_data.get('owner', ''),
        'name': dealer_name,
        'address': dealer_address,
        'city': dealer_city,
        'state': dealer_state,
        'zip': dealer_zip,
        'pnumber': pnumber,  # Ensure this gets set correctly
        'leftname': vin_data.get('person_left', ''),
        'person_left_add_combined': f"{vin_data.get('person_left_address1', '')}, {vin_data.get('person_left_address2', '')}",
        'date_left': vin_data.get('date_left', ''),
        'date_completed': vin_data.get('date_completed', ''),
        'repair_amount': f"${float(vin_data['repair_amount']):,.2f}" if vin_data.get('repair_amount') else "N/A",
        'repair_amount_dup': f"${float(vin_data['repair_amount']):,.2f}" if vin_data.get('repair_amount') else "N/A",
        'date_notified': vin_data.get('date_notified', ''),
        'sale_date': vin_data.get('sale_date', ''),
        'odometer': vin_data.get('odometer', ''),
        'associate1_dup': associate1,
        'associate2_dup': associate2,
        'person_left': vin_data.get('person_left', ''),
        'name_dup': dealer_name,
        'combined_dealer_address': combined_dealer_address,
        'combined_dealer_address_2': combined_dealer_address,
    }

    # Insert text into the PDF at the correct coordinates
    for field, coordinates in field_coordinates.items():
        text = form_data.get(field, '')
        if text:
            page.insert_text(coordinates, text, fontsize=12)

    # Save the Completed PDF
    pdf_writer.save(file_path)
    pdf_writer.close()

    flash(f"✅ VTR-265-FM Form saved: {file_path}", "success")
    print(f"✅ Debug: VTR-265-FM Form successfully generated at {file_path}")

def generate_ts12_form(vin_data, file_path, pdf_template):
    """Generates the TS-12 form with the correct X, Y coordinates."""

    # ✅ Ensure the template exists
    if not os.path.exists(pdf_template):
        flash(f"❌ Error: TS-12 template not found at {pdf_template}", "danger")
        print(f"❌ Error: TS-12 template not found at {pdf_template}")
        return

    try:
        # ✅ Open the template PDF
        pdf_writer = fitz.open(pdf_template)
        page = pdf_writer[0]  

        # ✅ Extract Dealer Info
        dealer_name = vin_data.get("dealer_name", "Unknown Dealer")
        dealer_address = vin_data.get("dealer_address", "Unknown Address")
        dealer_city = vin_data.get("dealer_city", "Unknown City")
        dealer_state = vin_data.get("dealer_state", "Unknown State")
        dealer_zip = vin_data.get("dealer_zip", "Unknown ZIP")

        # ✅ Combine Dealer Address
        combined_dealer_address = f"{dealer_address}, {dealer_city}, {dealer_state} {dealer_zip}"

        # ✅ Debugging prints
        print(f"✅ Debug: Inserting Dealer Name: {dealer_name}")
        print(f"✅ Debug: Inserting Combined Dealer Address: {combined_dealer_address}")

        # ✅ Define Field Positions
        field_positions = {
            'name': (70, 135),  # ✅ First Dealer Name
            'combined_dealer_address': (70, 375),  # ✅ Combined Dealer Address
            'pnumber': (340, 350),  # ✅ PNumber
            'year': (70, 500),
            'make': (300, 500),
            'body': (450, 500),
            'vin': (70, 530),
            'associate1': (70, 600),
            'name_dup': (70, 350),  # ✅ Second Dealer Name
        }

        # ✅ Insert Data into the PDF
        for field, position in field_positions.items():
            if field == "name":
                value = dealer_name  # ✅ First Dealer Name
            elif field == "combined_dealer_address":
                value = combined_dealer_address  # ✅ First Dealer Address
            elif field == "name_dup":
                value = dealer_name  # ✅ Second Dealer Name
            else:
                value = vin_data.get(field, "N/A")

            print(f"✅ Debug: Writing {field} -> {value} at {position}")
            page.insert_text(position, value, fontsize=12)

        # ✅ Save & Close PDF
        pdf_writer.save(file_path)
        pdf_writer.close()

        flash(f"✅ TS-12 Form saved at {file_path}", "success")
        print(f"✅ [DEBUG] TS-12 form generated at {file_path}")

    except Exception as e:
        flash(f"❌ Error generating TS-12: {e}", "danger")
        print(f"❌ Error generating TS-12: {e}")

import fitz
import os

def generate_popo_form(vin_data, file_path, pdf_template):
    """Generates the POPO form using the correct X, Y coordinates."""

    # Ensure the template exists
    if not os.path.exists(pdf_template):
        flash(f"❌ Error: POPO template not found at {pdf_template}", "danger")
        print(f"❌ Error: POPO template not found at {pdf_template}")
        return

    # Open the template PDF
    pdf_writer = fitz.open(pdf_template)
    page = pdf_writer[0]  # Use the first page

    # Define X, Y coordinates for required fields
    field_positions = {
        'model': (120, 280),
        'year': (200, 280),
        'make': (270, 280),
        'vin': (340, 280)
    }

    # Insert data into the PDF
    for field, position in field_positions.items():
        value = vin_data.get(field, "N/A")
        page.insert_text(position, value, fontsize=12)

    # Save the completed form
    pdf_writer.save(file_path)
    pdf_writer.close()

    flash(f"✅ POPO Form saved at {file_path}", "success")
    print(f"✅ [DEBUG] POPO form generated at {file_path}")

def generate_vtr34_form(vin_data, file_path, pdf_template):
    """Generates the VTR-34 form using the correct X, Y coordinates."""

    # Ensure the template exists
    if not os.path.exists(pdf_template):
        flash(f"❌ Error: VTR-34 template not found at {pdf_template}", "danger")
        print(f"❌ Error: VTR-34 template not found at {pdf_template}")
        return

    # Open the template PDF
    pdf_writer = fitz.open(pdf_template)
    page = pdf_writer[0]

    # Define X, Y coordinates for required fields
    field_positions = {
        'vin': (60, 405),
        'year': (310, 405),
        'make': (370, 405),
        'body': (450, 405),
        'model': (515, 405),

    }

    # Insert data into the PDF
    for field, position in field_positions.items():
        if field == "name":
            value = vin_data.get("dealer_name", "Unknown Dealer")
        elif field == "combined_dealer_address":
            value = f"{vin_data.get('dealer_address', '')}, {vin_data.get('dealer_city', '')}, {vin_data.get('dealer_state', '')} {vin_data.get('dealer_zip', '')}"
        else:
            value = vin_data.get(field, "N/A")

        page.insert_text(position, value, fontsize=12)

    # Save the completed form
    pdf_writer.save(file_path)
    pdf_writer.close()

    flash(f"✅ VTR-34 Form saved at {file_path}", "success")
    print(f"✅ [DEBUG] VTR-34 form generated at {file_path}")

import fitz  # PyMuPDF for PDF manipulation
import os

def generate_bonded_title_form(vin_data, file_path, pdf_template):
    """Generates the VTR-130-SOF (Bonded Title) form with correct X, Y coordinates."""

    # Ensure the template exists
    if not os.path.exists(pdf_template):
        flash(f"❌ Error: VTR-130-SOF template not found at {pdf_template}", "danger")
        print(f"❌ Error: VTR-130-SOF template not found at {pdf_template}")
        return

    try:
        # Open the template PDF
        pdf_writer = fitz.open(pdf_template)
        page = pdf_writer[0]  # Use the first page of the form

        # Define field coordinates
        field_positions = {
            "VIN": (50, 130),
            "Year": (320, 130),
            "Make": (400, 130),
            "Body": (450, 130),
            "Model": (520, 130),
            "DealerName": (50, 195),  # ✅ Replacing "Buyer" with Dealer Name
            "DealerFullAddress": (50, 245),  # ✅ Replacing "FullAddress" with Dealer's full address
            "Odometer": (320, 150),  # New position for odometer
        }

        # Extract vehicle data
        vin = vin_data.get("vin", "N/A")
        year = vin_data.get("year", "N/A")
        make = vin_data.get("make", "N/A")
        body = vin_data.get("body", "N/A")
        model = vin_data.get("model", "N/A")
        odometer = vin_data.get("odometer", "N/A")

        # ✅ Extract dealer details
        dealer_name = vin_data.get("dealer_name", "Unknown Dealer")
        dealer_address = vin_data.get("dealer_address", "Unknown Address")
        dealer_city = vin_data.get("dealer_city", "Unknown City")
        dealer_state = vin_data.get("dealer_state", "Unknown State")
        dealer_zip = vin_data.get("dealer_zip", "Unknown ZIP")

        # ✅ Combine Dealer Address
        dealer_full_address = f"{dealer_address}, {dealer_city}, {dealer_state} {dealer_zip}"

        # ✅ Insert data into the PDF
        page.insert_text(field_positions["VIN"], vin, fontsize=12)
        page.insert_text(field_positions["Year"], year, fontsize=12)
        page.insert_text(field_positions["Make"], make, fontsize=12)
        page.insert_text(field_positions["Body"], body, fontsize=12)
        page.insert_text(field_positions["Model"], model, fontsize=12)
        page.insert_text(field_positions["Odometer"], odometer, fontsize=12)

        # ✅ Insert Dealer Name & Combined Address (Replacing Buyer Fields)
        page.insert_text(field_positions["DealerName"], dealer_name, fontsize=12)  # ✅ Dealer Name
        page.insert_text(field_positions["DealerFullAddress"], dealer_full_address, fontsize=12)  # ✅ Dealer Full Address

        # Save the completed form
        pdf_writer.save(file_path)
        pdf_writer.close()

        flash(f"✅ VTR-130-SOF Form saved at {file_path}", "success")
        print(f"✅ [DEBUG] VTR-130-SOF form generated at {file_path}")

    except Exception as e:
        flash(f"❌ Error generating VTR-130-SOF: {e}", "danger")
        print(f"❌ Error generating VTR-130-SOF: {e}")

import fitz  # PyMuPDF
import os

def generate_vtr270_form(vin_data, file_path, pdf_template):
    """Generates the VTR-270 form using the correct X, Y coordinates."""

    # Ensure the template exists
    if not os.path.exists(pdf_template):
        flash(f"❌ Error: VTR-270 template not found at {pdf_template}", "danger")
        print(f"❌ Error: VTR-270 template not found at {pdf_template}")
        return

    # Open the template PDF
    pdf_writer = fitz.open(pdf_template)
    page = pdf_writer[0]  

    # Extract Dealer Information
    dealer_name = vin_data.get("dealer_name", "Unknown Dealer")
    dealer_address = vin_data.get("dealer_address", "Unknown Address")
    dealer_city = vin_data.get("dealer_city", "Unknown City")
    dealer_state = vin_data.get("dealer_state", "Unknown State")
    dealer_zip = vin_data.get("dealer_zip", "Unknown ZIP")

    # Combine Dealer Address
    combined_dealer_address = f"{dealer_address}, {dealer_city}, {dealer_state} {dealer_zip}"

    # Extract VIN Data
    vin = vin_data.get("vin", "N/A")
    year = vin_data.get("year", "N/A")
    make = vin_data.get("make", "N/A")
    body = vin_data.get("body", "N/A")
    model = vin_data.get("model", "N/A")

    # Define Field Positions
    field_positions = {
        "VIN": (60, 460),
        "Year": (310, 460),
        "Make": (370, 460),
        "Body": (450, 460),
        "Model": (520, 460),
        "Dealer": (60, 533),  # Dealer Name
        "CombinedAddress": (60, 583),  # Combined Address (Address, City, State, ZIP)
    }

    # Insert Data into the PDF
    form_data = {
        "VIN": vin,
        "Year": year,
        "Make": make,
        "Body": body,
        "Model": model,
        "Dealer": dealer_name,
        "CombinedAddress": combined_dealer_address,
    }

    for field, position in field_positions.items():
        value = form_data.get(field, "N/A")
        print(f"✅ Writing {field} -> {value} at {position}")
        page.insert_text(position, value, fontsize=12)

    # Save the completed form
    pdf_writer.save(file_path)
    pdf_writer.close()

    flash(f"✅ VTR-270 Form saved at {file_path}", "success")
    print(f"✅ [DEBUG] VTR-270 form generated at {file_path}")

# TEST MECHANIC LIEN LETTER
@app.route("/generate_mechanic_lien", methods=["GET", "POST"])
def generate_mechanic_lien():
    """Generate a Mechanic Lien Letter separately."""

    if "selected_vin" not in session:
        flash("⚠ Missing VIN data. Start over!", "danger")
        return redirect(url_for("search_vin"))

    vin_data = session["selected_vin"]
    dealer_name = vin_data.get("dealer_name", "UnknownDealer").replace(" ", "_")
    vin = vin_data.get("vin", "UnknownVIN")

    # Define file paths
    form_templates_dir = r"C:\Users\marka\Desktop\mechanic_lien_app\forms"
    file_name = f"{dealer_name}_{vin}_Mechanic_Lien.pdf"
    form_path = os.path.join(r"C:\Users\marka\Desktop\Mechanic Lien Work Space", file_name)
    pdf_template = os.path.join(form_templates_dir, "letter_new_new.pdf")  # Ensure correct filename

    print(f"🔍 Generating Mechanic Lien using template: {pdf_template}")

    if not os.path.exists(pdf_template):
        print(f"❌ ERROR: Mechanic Lien template not found at {pdf_template}")
        flash(f"❌ ERROR: Template not found at {pdf_template}", "danger")
        return redirect(url_for("search_vin"))

    try:
        generate_mechanic_letter(vin_data, form_path)
        print(f"✅ Mechanic Lien Letter saved at {file_path}")
        flash(f"✅ Mechanic Lien Letter generated: {file_name}", "success")

    except Exception as e:
        flash(f"❌ Error generating Mechanic Lien: {e}", "danger")
        print(f"❌ ERROR: Exception while generating Mechanic Lien: {e}")

    return redirect(url_for("search_vin"))

from flask import send_file

import os
import csv
import sqlite3

# Set DB path
DB_PATH = os.path.join(os.path.dirname(__file__), "dealers_and_vins.db")

def get_desktop_path():
    """Returns the path to the user's desktop."""
    return os.path.join(os.path.expanduser("~"), "Desktop")


def export_vin_records(last_4_vin, db_path, output_filename="vin_records.csv"):
    """
    Exports VIN records to a CSV file based on the last 4 digits of the VIN.

    Args:
        last_4_vin (str): The last 4 characters of the VIN to search for.
        db_path (str): Path to the SQLite database.
        output_filename (str): Name of the output CSV file.

    Returns:
        str or None: The full path to the CSV file or None if no data found or error occurs.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        query = """
            SELECT vin, year, make, model, 
                    owner, owner_address1, owner_address2,
                    renewal, renewal_address1, renewal_address2,
                    lein_holder, lein_holder_address1, lein_holder_address2,
                    person_left, person_left_address1, person_left_address2
            FROM vins
            WHERE vin LIKE ?
        """
        cursor.execute(query, ('%' + last_4_vin,))
        records = cursor.fetchall()

        if not records:
            print(f"No records found with VIN ending in {last_4_vin}")
            return None

        headers = ['VIN', 'Last 4 VIN', 'Type', 'Name', 'Address1', 'Address2']
        desktop_path = get_desktop_path()
        csv_path = os.path.join(desktop_path, output_filename)

        with open(csv_path, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)

            for record in records:
                vin, year, make, model = record[:4]
                last_4 = vin[-4:]

                data_entries = [
                    ('Owner', record[4:7]),
                    ('Renewal', record[7:10]),
                    ('Lien Holder', record[10:13]),
                    ('Person Left', record[13:16])
                ]

                for label, (name, addr1, addr2) in data_entries:
                    if name and name.strip():
                        writer.writerow([
                            vin,
                            last_4,
                            label,
                            name.strip(),
                            addr1.strip() if addr1 else '',
                            addr2.strip() if addr2 else ''
                        ])

        conn.close()
        return csv_path

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return None

import os

# Make sure DB_PATH is declared globally somewhere above this route:
DB_PATH = os.path.join(os.path.dirname(__file__), "dealers_and_vins.db")

@app.route("/export_vin/<string:last_4_vin>", methods=["GET"])
def export_vin(last_4_vin):

#  db_path = r"C:\Users\marka\Desktop\dealers_and_vins.db"
    output_filename = r"C:\Users\marka\Desktop\vin_records.csv"  # ✅ Always use the same file name

    """
    Exports VIN records matching the last 4 digits to a CSV file and prompts download.
    """
    output_filename = os.path.join(os.path.expanduser("~"), "Desktop", "vin_records.csv")


    # ✅ Overwrite file if it already exists
    if os.path.exists(output_filename):
        os.remove(output_filename)

    # ✅ Use the utility function to create the CSV
    file_path = export_vin_records(last_4_vin, DB_PATH, output_filename)

    if file_path and os.path.exists(file_path):
        flash(f"✅ VIN records exported successfully: {file_path}", "success")
        return send_file(file_path, as_attachment=True)
    else:
        flash(f"❌ No records found for VIN ending in {last_4_vin}", "danger")
        return redirect(url_for("search_vin"))  # Make sure 'search_vin' is a valid route


@app.route("/dashboard")
def dashboard():

    """Displays the dashboard with updated lien information."""

    print("🧪 Session contents:", dict(session))

    dealer_id = session.get("dealer_id")
    role = session.get("role")

    if not role:
        flash("Unauthorized access. Please log in.", "danger")
        return redirect(url_for("login"))
    role = session.get("role")
    dealer_id = session.get("dealer_id")
    status_filter = request.args.get("status_filter", "All")


    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()


    status_filter = request.args.get("status", "All")

    # ✅ Total Liens
    if role == "admin":
        cursor.execute("SELECT COUNT(*) FROM vins")
    else:
        cursor.execute("SELECT COUNT(*) FROM vins WHERE dealer_id = ?", (dealer_id,))
    total_liens = cursor.fetchone()[0]

    # ✅ Open Liens
    if role == "admin":
        cursor.execute("""
            SELECT vins.*, dealers.name AS dealer_name
            FROM vins
            LEFT JOIN dealers ON vins.dealer_id = dealers.dealer_id
            WHERE vins.sale_date IS NULL 
                AND (vins.lien_canceled IS NULL OR vins.lien_canceled = '' OR vins.lien_canceled = 'N/A')
            ORDER BY vins.date_notified DESC
        """)
    else:
        cursor.execute("""
            SELECT vins.*, dealers.name AS dealer_name
            FROM vins
            LEFT JOIN dealers ON vins.dealer_id = dealers.dealer_id
            WHERE vins.dealer_id = ?
                AND vins.sale_date IS NULL 
                AND (vins.lien_canceled IS NULL OR vins.lien_canceled = '' OR vins.lien_canceled = 'N/A')
            ORDER BY vins.date_notified DESC
        """, (dealer_id,))
    open_liens = cursor.fetchall()

    # ✅ Liens In Process
    if role == "admin":
        cursor.execute("SELECT COUNT(*) FROM vins WHERE status = 'In Process'")
    else:
        cursor.execute("SELECT COUNT(*) FROM vins WHERE status = 'In Process' AND dealer_id = ?", (dealer_id,))
    liens_in_process = cursor.fetchone()[0]

    # ✅ Completed Liens
    if role == "admin":
        cursor.execute("""
            SELECT COUNT(*) FROM vins
            WHERE sale_date IS NOT NULL OR lien_canceled != 'N/A'
        """)
    else:
        cursor.execute("""
            SELECT COUNT(*) FROM vins
            WHERE dealer_id = ? AND (sale_date IS NOT NULL OR lien_canceled != 'N/A')
        """, (dealer_id,))
    liens_finished = cursor.fetchone()[0]

    # ✅ Recent Liens (with filter)
    if role == "admin":
        if status_filter == "All":
            cursor.execute("""
                SELECT vins.*, dealers.name AS dealer_name
                FROM vins
                LEFT JOIN dealers ON vins.dealer_id = dealers.dealer_id
                ORDER BY vins.date_notified DESC
            """)
        else:
            cursor.execute("""
                SELECT vins.*, dealers.name AS dealer_name
                FROM vins
                LEFT JOIN dealers ON vins.dealer_id = dealers.dealer_id
                WHERE vins.status = ?
                ORDER BY vins.date_notified DESC
            """, (status_filter,))
    else:
        if status_filter == "All":
            cursor.execute("""
                SELECT vins.*, dealers.name AS dealer_name
                FROM vins
                LEFT JOIN dealers ON vins.dealer_id = dealers.dealer_id
                WHERE vins.dealer_id = ?
                ORDER BY vins.date_notified DESC
            """, (dealer_id,))
        else:
            cursor.execute("""
                SELECT vins.*, dealers.name AS dealer_name
                FROM vins
                LEFT JOIN dealers ON vins.dealer_id = dealers.dealer_id
                WHERE vins.dealer_id = ? AND vins.status = ?
                ORDER BY vins.date_notified DESC
            """, (dealer_id, status_filter))

    recent_liens = cursor.fetchall()
    conn.close()

    # ✅ Debug Output

    if role == "dealer":
        # Recalculate and store available credits in session
        available_credits = get_available_credits(dealer_id)
        session["available_credits"] = available_credits

        # Dealer-specific counts
        cursor.execute("SELECT COUNT(*) FROM vins WHERE dealer_id = ?", (dealer_id,))
        total_liens = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM vins WHERE dealer_id = ? AND status = 'Canceled'", (dealer_id,))
        liens_canceled = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM vins WHERE dealer_id = ? AND status = 'In Process'", (dealer_id,))
        liens_in_process = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM vins WHERE dealer_id = ? AND status = 'Finished'", (dealer_id,))
        liens_finished = cursor.fetchone()[0]

        if status_filter == "All":
            cursor.execute("""
                SELECT vins.*, dealers.name AS dealer_name
                FROM vins
                LEFT JOIN dealers ON vins.dealer_id = dealers.dealer_id
                WHERE vins.dealer_id = ?
                ORDER BY vins.date_notified DESC
            """, (dealer_id,))
        else:
            cursor.execute("""
                SELECT vins.*, dealers.name AS dealer_name
                FROM vins
                LEFT JOIN dealers ON vins.dealer_id = dealers.dealer_id
                WHERE vins.dealer_id = ? AND vins.status = ?
                ORDER BY vins.date_notified DESC
            """, (dealer_id, status_filter))

    else:  # admin
        available_credits = 0  # Admin doesn't use credits

        cursor.execute("SELECT COUNT(*) FROM vins")
        total_liens = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM vins WHERE status = 'Canceled'")
        liens_canceled = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM vins WHERE status = 'In Process'")
        liens_in_process = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM vins WHERE status = 'Finished'")
        liens_finished = cursor.fetchone()[0]

        if status_filter == "All":
            cursor.execute("""
                SELECT vins.*, dealers.name AS dealer_name
                FROM vins
                LEFT JOIN dealers ON vins.dealer_id = dealers.dealer_id
                ORDER BY vins.date_notified DESC
            """)
        else:
            cursor.execute("""
                SELECT vins.*, dealers.name AS dealer_name
                FROM vins
                LEFT JOIN dealers ON vins.dealer_id = dealers.dealer_id
                WHERE vins.status = ?
                ORDER BY vins.date_notified DESC
            """, (status_filter,))

    filtered_liens = cursor.fetchall()
    conn.close()

    # Debug printouts

    print("📌 Total Liens:", total_liens)
    print("📌 Canceled Liens:", liens_canceled)
    print("📌 Liens In Process:", liens_in_process)

    print("📌 Completed Liens:", liens_finished)
    print("📌 Recent Liens Count:", len(recent_liens))
    print("📌 Selected Filter:", status_filter)

    print("📌 Finished Liens:", liens_finished)
    print("📌 Filtered Liens Count:", len(filtered_liens))
    print("💳 Available Credits (session):", session.get("available_credits"))


    return render_template(
        "dashboard.html",
        total_liens=total_liens,
        liens_canceled=liens_canceled,
        liens_in_process=liens_in_process,
        liens_finished=liens_finished,

        recent_liens=recent_liens,
        status_filter=status_filter

        filtered_liens=filtered_liens,
        status_filter=status_filter,
        available_credits=available_credits

    )


@app.route("/update_lien_status/<string:vin>", methods=["POST"])
def update_lien_status(vin):
    """Updates the status of a lien based on sale date and canceled flag."""

    sale_date = request.form.get("sale_date")  # Get sale date from form
    canceled = request.form.get("canceled")  # Get canceled checkbox (if checked)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Determine new status
        if sale_date:
            new_status = "Completed"
        elif canceled:
            new_status = "Canceled"
        else:
            new_status = "Open"

        # ✅ Update lien status in the database
        cursor.execute("UPDATE vins SET status = ?, sale_date = ?, canceled = ? WHERE vin = ?",
                        (new_status, sale_date, bool(canceled), vin))
        conn.commit()
        flash(f"✅ Lien status updated to {new_status}!", "success")
    except sqlite3.Error as e:
        flash(f"❌ Database error: {e}", "danger")
    finally:
        conn.close()

    return redirect(url_for("dashboard"))

@app.route("/view_vin/<string:vin_id>")
def view_vin(vin_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if session.get("role") == "dealer":
        # Only fetch the VIN if it belongs to the logged-in dealer
        cursor.execute("SELECT * FROM vins WHERE vin = ? AND dealer_id = ?", (vin_id, session.get("dealer_id")))
    else:
        # Admins and superusers can view all
        cursor.execute("SELECT * FROM vins WHERE vin = ?", (vin_id,))

    vin = cursor.fetchone()
    conn.close()

    if not vin:
        flash("⚠ VIN not found or access denied.", "danger")
        return redirect(url_for("dashboard"))

    return render_template("view_vin.html", vin=vin)

@app.route("/view_dealer/<int:dealer_id>")
def view_dealer(dealer_id):
    """Displays details for a specific dealer."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM dealers WHERE dealer_id = ?", (dealer_id,))
    dealer = cursor.fetchone()
    conn.close()

    if not dealer:
        flash("⚠ Dealer not found!", "danger")
        return redirect(url_for("view_dealers"))

    return render_template("view_dealer.html", dealer=dealer)

@app.route("/reports")
def reports():
    return render_template("reports.html")

@app.route("/report/lien_summary")
def lien_summary_report():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Total Liens
    cursor.execute("SELECT COUNT(*) FROM vins")
    total_liens = cursor.fetchone()[0]

    # Status Breakdown
    cursor.execute("SELECT status, COUNT(*) FROM vins GROUP BY status")
    status_counts = {row[0]: row[1] for row in cursor.fetchall()}

    # Individual Status Counts
    in_process_liens = status_counts.get("In-Process", 0)
    completed_liens = status_counts.get("Completed", 0)
    canceled_liens = status_counts.get("Canceled", 0)

    # Liens in the last 30 days
    cursor.execute("SELECT COUNT(*) FROM vins WHERE date_notified >= date('now', '-30 days')")
    liens_last_30_days = cursor.fetchone()[0]

    # Completed in last 30 days
    cursor.execute("SELECT COUNT(*) FROM vins WHERE sale_date >= date('now', '-30 days')")
    liens_completed_last_30_days = cursor.fetchone()[0]

    conn.close()

    return render_template("lien_summary.html",
                            total_liens=total_liens,
                            liens_by_status=status_counts.items(),
                            in_process_liens=in_process_liens,
                            completed_liens=completed_liens,
                            canceled_liens=canceled_liens,
                            liens_last_30_days=liens_last_30_days,
                            liens_completed_last_30_days=liens_completed_last_30_days)


@app.route("/report/dealer_performance")
def dealer_performance_report():
    """Shows dealer performance based on lien completion and counts."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Dealers with the most liens
    cursor.execute("""
        SELECT dealers.name, COUNT(vins.vin) AS lien_count 
        FROM dealers 
        JOIN vins ON dealers.dealer_id = vins.dealer_id 
        GROUP BY dealers.name 
        ORDER BY lien_count DESC 
        LIMIT 10
    """)
    top_dealers = cursor.fetchall()

    conn.close()

    return render_template("dealer_performance.html", top_dealers=top_dealers)

@app.route("/report/pending_actions")
def pending_actions_report():
    """Generates a report of all pending actions for mechanic liens."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # ✅ Fetch results as dictionaries instead of tuples
    cursor = conn.cursor()

    # Fetch all pending liens (where sale_date is NULL)
    cursor.execute("""
        SELECT vins.vin, vins.year, vins.make, vins.model, vins.date_notified, 
                dealers.name AS dealer_name, dealers.dealer_id
        FROM vins
        JOIN dealers ON vins.dealer_id = dealers.dealer_id
        WHERE vins.sale_date IS NULL
        ORDER BY vins.date_notified DESC
    """)
    pending_actions = cursor.fetchall()  # ✅ This now returns dictionaries, not tuples

    conn.close()

    return render_template("pending_actions_report.html", pending_actions=pending_actions)

@app.route("/report/revenue")
def revenue_report():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Fetch total revenue
    cursor.execute("SELECT SUM(amount) FROM payments")  # Ensure `amount` exists
    total_revenue = cursor.fetchone()[0] or 0  # Handle None case

    # Fetch revenue from last 30 days
    cursor.execute("SELECT SUM(amount) FROM payments WHERE date >= date('now', '-30 days')")
    revenue_last_30_days = cursor.fetchone()[0] or 0  # Handle None case

    # Fetch pending payments
    cursor.execute("SELECT SUM(amount) FROM payments WHERE status = 'Pending'")
    pending_revenue = cursor.fetchone()[0] or 0  # Handle None case

    conn.close()

    revenue_data = {
        "total_revenue": total_revenue,
        "revenue_last_30_days": revenue_last_30_days,
        "pending_revenue": pending_revenue
    }

    return render_template("revenue_report.html", revenue_data=revenue_data)

@app.route("/report/certified_letter_tracking")
def certified_letter_tracking_report():
    """Generates a report for certified letters sent and their delivery status with filters."""
    status_filter = request.args.get("status", "All")  # Get status filter from query parameters
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  
    cursor = conn.cursor()

    # ✅ Fetch all necessary data including Owner, Renewal, Lien Holder, and Person Left
    cursor.execute("""
        SELECT vin, owner, renewal, lein_holder, person_left, date_notified, status, 
                cert1, cert1_status, cert2, cert2_status, cert3, cert3_status, 
                cert4, cert4_status, cert5, cert5_status, cert6, cert6_status
        FROM vins
        ORDER BY vin ASC
    """)
    raw_certified_letters = cursor.fetchall()

    certified_letters = []

    for row in raw_certified_letters:
        cert_details = []  # Stores certification numbers & statuses
        sent_status = False  # Tracks if at least one cert was sent

        for i in range(1, 7):
            cert_number = row[f"cert{i}"]
            cert_status = row[f"cert{i}_status"]

            if cert_number and cert_number.strip() not in ('', 'N/A', None):
                sent_status = True  # ✅ At least one cert was sent

            cert_details.append({
                "cert_number": cert_number if cert_number else "N/A",
                "status": cert_status if cert_status else "Not Sent"
            })

        # ✅ Use `date_notified` if at least one letter was sent
        sent_date = row["date_notified"] if sent_status else "Not Sent"

        # ✅ Check if any cert status is 'Delivered'
        delivered_status = any(c["status"] == "Delivered" for c in cert_details)

        # ✅ Set final status
        if delivered_status:
            final_status = "Delivered"
        elif sent_status:
            final_status = "In Transit"
        else:
            final_status = "Not Sent"

        # ✅ Append cleaned-up row
        certified_letters.append({
            "vin": row["vin"],
            "owner": row["owner"],
            "renewal": row["renewal"] if row["renewal"] else "N/A",
            "lein_holder": row["lein_holder"] if row["lein_holder"] else "N/A",
            "person_left": row["person_left"] if row["person_left"] else "N/A",
            "status": row["status"],  
            "sent": "Yes" if sent_status else "No",
            "sent_date": sent_date,
            "letter_status": final_status,
            "cert_details": cert_details  # ✅ Store cert numbers & statuses as a list
        })

    conn.close()

    # ✅ Apply filter if not "All"
    if status_filter != "All":
        certified_letters = [letter for letter in certified_letters if letter["letter_status"] == status_filter]

    return render_template(
        "certified_letter_tracking_report.html", 
        certified_letters=certified_letters, 
        status_filter=status_filter
    )

@app.route('/export_lien_summary')
def export_lien_summary():
    liens = get_lien_data()  # Replace this with your function to fetch lien data

    def generate():
        data = [
            ['VIN', 'Dealer Name', 'Status', 'Date Notified', 'Sale Date']
        ]
        for lien in liens:
            status = 'Completed' if lien['sale_date'] else ('Canceled' if lien['lien_canceled'] != 'N/A' else 'Open')
            data.append([lien['vin'], lien['dealer_name'], status, lien['date_notified'], lien['sale_date'] or 'Pending'])

        output = csv.StringIO()
        writer = csv.writer(output)
        writer.writerows(data)
        return output.getvalue()

    response = Response(generate(), mimetype="text/csv")
    response.headers.set("Content-Disposition", "attachment", filename="lien_summary.csv")
    return response

def get_lien_data():
    """Fetches all lien records from the database."""
    liens = db.session.query(Lien).all()  # Ensure 'Lien' is your model
    return liens

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        pnumber = request.form["pnumber"].strip().upper()
        email = request.form["email"]
        password = request.form["password"]
        hashed_pw = generate_password_hash(password)

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()


        # Step 1: Look for existing dealer in your main app DB
        cursor.execute("SELECT dealer_id FROM dealers WHERE pnumber = ?", (pnumber,))

        # ✅ Check for duplicate email
        cursor.execute("SELECT COUNT(*) FROM users WHERE email = ?", (email,))
        if cursor.fetchone()[0]:
            flash("❌ This email is already registered.", "danger")
            return redirect(url_for("register"))

        # ✅ Check if dealer exists by pnumber
        cursor.execute("SELECT dealer_id, name FROM dealers WHERE pnumber = ?", (pnumber,))

        dealer = cursor.fetchone()

        if dealer:
            dealer_id = dealer["dealer_id"]

        else:
            # Step 2: Pull info from TexasDealerships.db
            texas_conn = sqlite3.connect("C:/Users/marka/Desktop/mechanic_lien_app/TexasDealerships.db")
            texas_conn.row_factory = sqlite3.Row
            texas_cursor = texas_conn.cursor()

            texas_cursor.execute("SELECT * FROM dealers WHERE pnumber = ?", (pnumber,))
            dealer_info = texas_cursor.fetchone()
            texas_conn.close()

            if dealer_info:
                cursor.execute("""
                    INSERT INTO dealers (pnumber, name, address, city, state, zip)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    dealer_info["pnumber"],
                    dealer_info["name"],
                    dealer_info["address"],
                    dealer_info["city"],
                    dealer_info["state"],
                    dealer_info["zip"]
                ))
                dealer_id = cursor.lastrowid
                print(f"✅ Imported dealer from Texas DB: {pnumber} → dealer_id {dealer_id}")
            else:
                flash("❌ P number not found in Texas Dealerships database.", "danger")
                return redirect(url_for("register"))

        # Step 3: Register the user with the found or created dealer_id
        cursor.execute("""
            INSERT INTO users (pnumber, email, password_hash, role, dealer_id)
            VALUES (?, ?, ?, 'dealer', ?)
        """, (pnumber, email, hashed_pw, dealer_id))

            dealer_name = dealer["name"]
            print(f"✅ Found dealer: {dealer_name}")
        else:
            # ✅ Add new dealer with just pnumber for now
            dealer_name = f"Dealer {pnumber}"
            cursor.execute("INSERT INTO dealers (pnumber, name) VALUES (?, ?)", (pnumber, dealer_name))
            dealer_id = cursor.lastrowid
            print(f"🆕 Created new dealer with P#: {pnumber} → ID: {dealer_id}")

        # ✅ Register user
        cursor.execute("""
            INSERT INTO users (name, pnumber, email, password_hash, role, dealer_id)
            VALUES (?, ?, ?, ?, 'dealer', ?)
        """, (dealer_name, pnumber, email, hashed_pw, dealer_id))


        conn.commit()
        conn.close()


        flash("✅ Registration successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


        # ✅ Set session
        session["dealer_id"] = dealer_id
        session["pnumber"] = pnumber
        session["email"] = email
        session["role"] = "dealer"

        flash("✅ Registration successful! Please select a plan.", "success")
        return redirect(url_for("pricing_select_plan"))

    return render_template("register.html")





@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        pnumber = request.form["pnumber"].strip().upper()
        password = request.form["password"]

        print(f"🔎 Input pnumber: '{pnumber}' | length: {len(pnumber)} | hex: {pnumber.encode().hex().upper()}")
        print(f"📁 DB file path: {DB_PATH}")

        conn = sqlite3.connect(f"file:{DB_PATH}?mode=rw", uri=True)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        print(f"📊 Total rows in users table (Flask): {total_users}")

        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        print("📋 users table columns:")
        for col in columns:
            print(dict(col))


        # ⬇️ Includes account_status explicitly
        cursor.execute("SELECT id, pnumber, email, password_hash, role, dealer_id, account_status FROM users")

        cursor.execute("SELECT id, pnumber, email, password_hash, role, dealer_id, account_status, name FROM users")

        all_users = cursor.fetchall()

        user = None
        print("🔍 Brute-forcing user match...")
        for row in all_users:
            row_pnumber = row["pnumber"].strip().upper()
            print(f"🔁 Comparing '{pnumber}' to '{row_pnumber}'")
            if row_pnumber == pnumber:
                print("✅ MATCH FOUND!")
                user = dict(row)
                print("🧪 Fetched user row:", user)
                break

        conn.close()

        if user:
            print(f"✅ User found: {user['pnumber']}, role: {user['role']}")
            if check_password_hash(user["password_hash"], password):
                if user.get("account_status", "active") != "active":
                    flash("⚠ Your account is inactive. Please contact support.", "danger")
                    return redirect(url_for("login"))


                # ✅ Store session data

                session["user_id"] = user["id"]
                session["pnumber"] = user["pnumber"]
                session["role"] = user["role"]
                session["dealer_id"] = user.get("dealer_id")

                session["username"] = user.get("name", "")

                # ✅ NEW: Calculate and store credits for dealers
                if user["role"] == "dealer" and user.get("dealer_id"):
                    session["available_credits"] = get_available_credits(user["dealer_id"])
                    print(f"💳 Set session available_credits: {session['available_credits']}")


                print("🔐 SET SESSION dealer_id:", session.get("dealer_id"))
                flash(f"✅ Welcome back, {user['pnumber']}!", "success")


                # ✅ Ensure redirect works by returning a proper route
                if user["role"] == "admin":
                    return redirect(url_for("dashboard"))
                else:

                # ✅ Redirects
                if user["role"] == "admin":
                    return redirect(url_for("dashboard"))
                else:
                    if not user.get("selected_plan"):
                        return redirect(url_for("pricing_select_plan"))

                    return redirect(url_for("select_dealer_for_vin"))
            else:
                flash("❌ Incorrect password.", "danger")
        else:
            print("❌ User not found in database")

            flash("❌ User not found.", "danger")

            flash("❌ User not found. Please register.", "danger")
            return redirect(url_for("register"))


    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("👋 You've been logged out.", "info")
    return redirect(url_for("login"))

@app.route("/pricing")
def pricing():
    return render_template("pricing.html")

import stripe
from flask import redirect

stripe.api_key = "your_stripe_secret_key"  # Replace with your actual key

@app.route("/create-checkout-session/<product_id>")
def create_checkout_session(product_id):
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product": product_id,
                        "unit_amount": 10000,  # amount in cents (example only)
                        "recurring": {"interval": "month"}  # if subscription
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",  # or "subscription"
            success_url=url_for('checkout_success', _external=True),
            cancel_url=url_for('checkout_cancel', _external=True),
        )
        return redirect(session.url, code=303)
    except Exception as e:
        return str(e)

@app.route("/checkout_success")
def checkout_success():
    return "✅ Payment successful! Thank you."

@app.route("/checkout_cancel")
def checkout_cancel():
    return "❌ Payment canceled. Please try again."

import stripe

@app.route("/pricing", methods=["GET", "POST"])
def pricing_select_plan():
    if request.method == "POST":
        selected_plan = request.form.get('plan')

        if selected_plan:
            # Save the selected plan (you can store it in the session or database)
            session['selected_plan'] = selected_plan
            flash(f"You've selected the {selected_plan} plan.", "success")

            # Update the user's plan in the database
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE users
                SET selected_plan = ?
                WHERE user_id = ?
            """, (selected_plan, session["user_id"]))
            conn.commit()
            conn.close()

            return redirect(url_for("login"))  # Redirect to login after selecting a plan
        else:
            flash("❌ Please select a plan.", "danger")

    return render_template("pricing_tiers.html")  # Pricing page where user can select a plan


def get_price_for_product(product_id):
    product_prices = {
        "prod_S4Nzuy0qEerKT0": 10000,   # Flex - $100.00
        "prod_S1QBDNEaIzGh56": 19900,   # Starter - $199.00
        "prod_S1QCRPghaGFaooM": 37500,  # Pro - $375.00
        "prod_S1QDvVcnd8SaPf": 69900,   # Enterprise - $699.00
    }
    return product_prices.get(product_id, 5000)  # Default fallback: $50


@app.route("/create-checkout-session/<product_id>")
def create_checkout_session(product_id):
    session["last_product_id"] = product_id

    # ✅ Product configuration: price ID and billing mode
    PRODUCT_CONFIG = {
        "prod_S5UkBvabSnSyT0": {  # Flex (one-time)
            "price_id": "price_1RBJkkGyZwKSDCtwAegB2BPH",
            "mode": "payment"
        },
        "prod_S5o6uwMUHoVEwt": {  # Starter (subscription)
            "price_id": "price_1RBcTxGyZwKSDCtwEhgokgWK",
            "mode": "subscription"
        },
        "prod_S5o7tXn3FY1Eq1": {  # Pro (subscription)
            "price_id": "price_1RBcVgGyZwKSDCtwXCk99A9w",
            "mode": "subscription"
        },
        "prod_S5oBIn40Hf1AES": {  # Enterprise (subscription)
            "price_id": "price_1RBcYeGyZwKSDCtwQonmHEHX",
            "mode": "subscription"
        }
    }

    plan = PRODUCT_CONFIG.get(product_id)
    if not plan:
        flash("❌ Invalid plan selected.", "danger")
        return redirect(url_for("pricing_select_plan"))

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": plan["price_id"], "quantity": 1}],
            mode=plan["mode"],
            success_url=url_for("checkout_success", _external=True),
            cancel_url=url_for("pricing_select_plan", _external=True),
            metadata={
                "dealer_id": session.get("dealer_id", "UNKNOWN"),
                "pnumber": session.get("pnumber", "UNKNOWN"),
                "email": session.get("email", "UNKNOWN"),
                "product_id": product_id
            }
        )

        session["stripe_session_id"] = checkout_session.id
        return redirect(checkout_session.url, code=303)

    except Exception as e:
        print(f"❌ Error creating checkout session: {e}")
        return f"Error: {e}"

@app.route("/checkout_success")
def checkout_success():
    dealer_id = session.get("dealer_id")
    product_id = session.get("last_product_id")
    stripe_session_id = session.get("stripe_session_id")

    print("🔍 Session Data:", dealer_id, product_id, stripe_session_id)

    if not dealer_id or not stripe_session_id:
        flash("⚠️ Missing session data. Please contact support.", "warning")
        return redirect(url_for("dashboard"))

    try:
        checkout_session = stripe.checkout.Session.retrieve(stripe_session_id)
        print("✅ Stripe Checkout Session:", checkout_session)

        is_subscription = checkout_session.get("mode") == "subscription"
        stripe_customer_id = checkout_session.get("customer") if is_subscription else "n/a"
        stripe_subscription_id = checkout_session.get("subscription") if is_subscription else "n/a"

        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO subscriptions (dealer_id, product_id, stripe_customer_id, stripe_subscription_id)
            VALUES (?, ?, ?, ?)
        """, (dealer_id, product_id, stripe_customer_id, stripe_subscription_id))
        print("📥 Subscription record inserted")

        amount_total = checkout_session.get("amount_total", 0)
        cursor.execute("""
            INSERT INTO payments (dealer_id, product_id, amount_cents)
            VALUES (?, ?, ?)
        """, (dealer_id, product_id, amount_total))
        print("💳 Payment record inserted: Amount =", amount_total)

        conn.commit()
        conn.close()
        print("✅ Committed to DB")

        # ✅ Assign credits
        metadata = checkout_session.get("metadata", {})
        is_extra_credit = metadata.get("source") == "extra_lien_purchase"

        if is_extra_credit:
            add_lien_credits(dealer_id, 1)
            print("✅ 1 extra lien credit added (single purchase).")
        elif product_id == "prod_S5UkBvabSnSyT0":  # Flex Pay-as-you-go
            qty = amount_total // 10000  # $100 per credit
            if qty > 0:
                add_lien_credits(dealer_id, qty)
                print(f"✅ {qty} Flex lien credit(s) purchased.")
        else:
            product_id_to_credits = {
                "prod_S5o6uwMUHoVEwt": 3,     # Starter
                "prod_S5o7tXn3FY1Eq1": 10,    # Pro
                "prod_S5oBIn40Hf1AES": 25   # Enterprise
            }
            credits = product_id_to_credits.get(product_id, 0)
            if credits > 0:
                add_lien_credits(dealer_id, credits)
                print(f"✅ {credits} subscription credits added.")

        flash("✅ Payment successful and credits added.", "success")
        return redirect(url_for("dashboard"))

    except Exception as e:
        print("❌ Error in checkout_success:", e)
        flash("❌ There was a problem processing your payment. Please contact support.", "danger")
        return redirect(url_for("dashboard"))

@app.route("/checkout_cancel")
def checkout_cancel():
    flash("⚠️ Payment canceled. You can try again anytime.", "warning")
    return redirect(url_for("pricing_select_plan"))



from flask import request

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")  # We'll get this in the next step


@app.route('/stripe/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('stripe-signature')

from flask import request

# Keep this in environment variables ideally
endpoint_secret = "your_webhook_secret"  # Keep this in environment variables


####CHOOSE PLAN ########
@app.route('/choose-plan', methods=['GET', 'POST'])
def choose_plan():
    if request.method == 'POST':
        plan = request.form['plan']
        dealer_id = session.get('dealer_id')

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE dealers SET subscription_plan = ? WHERE dealer_id = ?", (plan, dealer_id))
        conn.commit()
        conn.close()

        return redirect(url_for('create_checkout_session', plan=plan))

    return render_template('choose_plan.html')  # Create this template

@app.route('/')
def index():
    if 'dealer_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.context_processor
def inject_available_credits():
    dealer_id = session.get("dealer_id")
    role = session.get("role")
    credits = None

    if role == "dealer" and dealer_id:
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(quantity) FROM lien_credits WHERE dealer_id = ?", (dealer_id,))
            result = cursor.fetchone()
            credits = result[0] if result and result[0] is not None else 0
            conn.close()
        except Exception as e:
            print(f"❌ Error fetching credits: {e}")
            credits = 0

    return {"available_credits": credits}

def send_low_credit_email(dealer_name, recipient_email):
    subject = "🔔 Low Lien Credits – Time to Top Up!"
    message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="max-width: 600px; margin: auto; border: 1px solid #ccc; padding: 25px; border-radius: 8px;">
        <h2 style="color: #0056b3;">⚠️ You're Almost Out of Lien Credits</h2>
        <p>Hi <strong>{dealer_name}</strong>,</p>
        <p>We noticed you're down to <strong>1 lien credit</strong> in your account. To avoid interruptions, consider topping up now.</p>
        <p style="text-align: center; margin: 30px 0;">
        <a href="http://localhost:5000/pricing" style="
            background-color: #28a745;
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            font-size: 16px;
            border-radius: 6px;">💳 Buy More Credits</a>
        </p>
        <p>Thanks for choosing the Mechanic Lien App!</p>
        <p>– The My Title Guy Team</p>
        <hr>
        <small>This is an automated message. Please do not reply directly.</small>
        </div>
    </body>
    </html>
    """
    send_dealer_email(recipient_email, subject, message)

def decrement_lien_credit(dealer_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE lien_credits
        SET quantity = quantity - 1
        WHERE dealer_id = ? AND quantity > 0
    """, (dealer_id,))
    conn.commit()
    conn.close()
    print(f"🔻 1 credit used for dealer {dealer_id}")

# DELETE AFTER TEST IS COMPLETE
def send_test_low_credit_email():
    dealer_name = "Randall Reeds Planet Ford"
    dealer_email = "markacaffey@gmail.com"  # ← Your email

    subject = "⚠️ Low Lien Credit Warning"

    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f8f9fa; padding: 30px;">
        <div style="max-width: 600px; margin: auto; background: #fff; border-radius: 10px; padding: 20px; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
            <h2 style="color: #C0392B;">⚠️ You're Down to 1 Lien Credit!</h2>
            <p>Hi <strong>{dealer_name}</strong>,</p>
            <p>This is just a friendly reminder that you have only <strong>1 lien credit</strong> remaining in your account.</p>
            <p>To avoid any disruption in service, we recommend topping up your credits now.</p>

            <a href="http://localhost:5000/pricing" target="_blank"
                style="display: inline-block; padding: 12px 20px; background-color: #28a745; color: white; border-radius: 6px; text-decoration: none; font-weight: bold;">
                💳 Buy More Credits
            </a>

            <p style="margin-top: 30px;">Thanks for being a valued user of <strong>The Mechanic Lien App</strong>!</p>
            <p style="color: #888; font-size: 12px;">This is an automated message. If you have questions, reply to markacaffey@gmail.com.</p>
        </div>
    </body>
    </html>
    """

    try:
        msg = EmailMessage()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = dealer_email
        msg["Subject"] = subject
        msg.set_content("You have only 1 lien credit left. Please use an HTML-compatible email viewer.")
        msg.add_alternative(html_message, subtype="html")

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)

        print("✅ Test low-credit email sent.")
    except Exception as e:
        print(f"❌ Failed to send test email: {e}")

@app.route("/send-test-credit-alert")
def send_test_credit_alert():
    send_test_low_credit_email()
    return "✅ Test low credit email sent to markacaffey@gmail.com"

@app.route("/buy_credits", methods=["GET", "POST"])
def buy_credits():
    if "dealer_id" not in session:
        flash("Please log in to purchase credits.", "warning")
        return redirect(url_for("login"))

    dealer_id = session["dealer_id"]

    # Map of plan to Stripe product ID → used to determine pricing
    EXTRA_LIEN_PRICING = {
        "prod_S9fgpXltWktW6f": 10000,  # Flex: $100 per lien
        "prod_S9fhwMQDjKeRsd": 7500,   # Starter: $75 per lien
        "prod_S9fhtPZogI4bdo": 5000,   # Pro: $50 per lien
        "prod_S9fiSEwbe3ORtZ": 4000,   # Enterprise: $40 per lien
    }

    # Retrieve the dealer's plan from the database
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT current_plan FROM dealers WHERE dealer_id = ?", (dealer_id,))
    result = cursor.fetchone()
    conn.close()

    current_plan = result["current_plan"] if result else "prod_S5UkBvabSnSyT0"  # Default to Flex
    price_cents = EXTRA_LIEN_PRICING.get(current_plan, 10000)

    if request.method == "POST":
        try:
            quantity = int(request.form["quantity"])
            if quantity < 1:
                raise ValueError("Quantity must be 1 or more")

            # Create Stripe checkout session dynamically
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"Extra Liens - {quantity} credit(s)"
                        },
                        "unit_amount": price_cents,
                    },
                    "quantity": quantity,
                }],
                mode="payment",
                success_url=url_for("checkout_success", _external=True),
                cancel_url=url_for("dashboard", _external=True),
                metadata={
                    "dealer_id": dealer_id,
                    "quantity": quantity,
                    "product_type": "extra_credit",
                    "plan_id": current_plan
                }
            )

            # Optional: save session ID if needed for post-checkout tracking
            session["stripe_session_id"] = checkout_session["id"]

            return redirect(checkout_session.url, code=303)

        except Exception as e:
            print(f"❌ Error creating Stripe session: {e}")
            flash("An error occurred while starting your purchase. Please try again.", "danger")

    return render_template("buy_credits.html", plan=current_plan, price_cents=price_cents)


@app.route("/buy-credits-success")
def buy_credits_success():
    dealer_id = session.get("dealer_id")
    qty = int(request.args.get("qty", 0))

    if dealer_id and qty > 0:
        add_lien_credits(dealer_id, qty)
        flash(f"✅ Successfully purchased {qty} extra lien credit(s).", "success")
    else:
        flash("⚠ Something went wrong with the credit purchase.", "warning")

    return redirect(url_for("dashboard"))



from flask import request, jsonify

@app.route("/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("stripe-signature")

    endpoint_secret = "your_webhook_signing_secret_here"  # 🔐 Replace with your actual webhook secret

    event = None

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)

    except ValueError as e:
        print("⚠️ Invalid payload:", e)
        return '', 400
    except stripe.error.SignatureVerificationError as e:
        print("❌ Invalid signature:", e)
        return '', 400

    # 🔁 Handle event types
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        print("✅ Payment success! Session:", session)
        # TODO: update database, activate subscription, etc.

    elif event['type'] == 'invoice.payment_failed':
        print("❌ Payment failed")

    # Return 200 to acknowledge receipt
    return '', 200

    except stripe.error.SignatureVerificationError as e:
        print("⚠️ Webhook signature verification failed:", e)
        return "Unauthorized", 400

    # ✅ Check for paid invoice
    if event["type"] == "invoice.paid":
        invoice = event["data"]["object"]
        customer_id = invoice["customer"]
        subscription_id = invoice["subscription"]

        # Optional: log it
        print(f"✅ Invoice paid for subscription: {subscription_id}")

        # 👇 Fetch subscription to get product_id (plan type)
        subscription = stripe.Subscription.retrieve(subscription_id)
        product_id = subscription["items"]["data"][0]["price"]["product"]

        # 🔍 Look up dealer by customer_id in your DB
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT dealer_id FROM subscriptions WHERE stripe_customer_id = ?", (customer_id,))
        result = cursor.fetchone()

        if result:
            dealer_id = result[0]

            # 💡 Only add credits for monthly plans, not Flex
            if product_id != "prod_S5UkBvabSnSyT0":  # Flex plan product_id
                quantity = {
                    "prod_S9fGOtMikUhZ5W": 3,    # Starter
                    "prod_S9fGRwDYjYTDxq": 10,   # Pro
                    "prod_S9fGAYpcLnlnO7": 25    # Enterprise
                }.get(product_id, 0)

                if quantity > 0:
                    reset_lien_credits(dealer_id, quantity)
                    print(f"📦 Reset {quantity} credits for dealer {dealer_id}")

        conn.close()

    return jsonify({"status": "success"}), 200

def reset_lien_credits(dealer_id, quantity):
    """Reset monthly credits for a dealer (used in non-Flex plans)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Expire previous credits
    cursor.execute("DELETE FROM lien_credits WHERE dealer_id = ?", (dealer_id,))

    # Add new ones
    cursor.execute("""
        INSERT INTO lien_credits (dealer_id, quantity)
        VALUES (?, ?)
    """, (dealer_id, quantity))

    conn.commit()
    conn.close()

def get_credits_for_plan(product_id):
    return {
        "prod_S5UkBvabSnSyT0": 0,    # Flex – pay as you go, no credits granted
        "prod_S5o6uwMUHoVEwt": 3,    # Starter – 3 credits
        "prod_S5o7tXn3FY1Eq1": 10,   # Pro – 10 credits
        "prod_S5oBIn40Hf1AES": 25,   # Enterprise – 25 credits
    }.get(product_id, 0)

@app.route("/start_credit_checkout", methods=["POST"])
def start_credit_checkout():
    qty = int(request.form.get("qty", 1))
    dealer_id = session.get("dealer_id")

    if not dealer_id or qty <= 0:
        flash("Invalid request.", "danger")
        return redirect(url_for("dashboard"))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT current_plan FROM dealers WHERE dealer_id = ?", (dealer_id,))
    dealer = cursor.fetchone()
    conn.close()

    current_plan = dealer["current_plan"] if dealer else "prod_S5UkBvabSnSyT0"

    # Pricing map
    PRODUCT_TO_PRICE_ID = {
    "prod_S9fG9zRooP7uMR": "price_1RFLvwGyZwKSDCtwr2p5sX4K",       # Flex
    "prod_S9fGOtMikUhZ5W": "price_1RFLvrGyZwKSDCtwOn0PE5hv",    # Starter
    "prod_S9fGRwDYjYTDxq": "price_1RFLvrGyZwKSDCtwLAzLZSE9",        # Pro
    "prod_S9fGAYpcLnlnO7": "price_1RFLvrGyZwKSDCtweDzHbZnA"  # Enterprise
}


    price_id = PRODUCT_TO_PRICE_ID.get(current_plan)

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": qty}],
            mode="payment",
            success_url=url_for("checkout_success", _external=True),
            cancel_url=url_for("dashboard", _external=True),
            metadata={
                "dealer_id": dealer_id,
                "purpose": "extra_credits",
                "qty": qty
            }
        )
        return redirect(checkout_session.url, code=303)

    except Exception as e:
        print(f"❌ Stripe error: {e}")
        return f"Error: {e}"

def check_lien_credits_for_demo():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lien_credits WHERE dealer_id = ?", (6629,))
    results = cursor.fetchall()
    conn.close()

    if results:
        print(f"🔍 Found {len(results)} lien credit rows for dealer 6629:")
        for row in results:
            print(row)
    else:
        print("❌ No lien credit row found for dealer 6629.")

@app.route("/export_all_vins")
def export_all_vins():
    """Exports all VIN records to CSV."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT vin, year, make, model, dealer_id
            FROM vins
        """)
        records = cursor.fetchall()

        if not records:
            flash("No VIN records to export.", "warning")
            return redirect(url_for("dashboard"))

        # Save to Desktop
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        output_file = os.path.join(desktop_path, "all_vin_records.csv")

        with open(output_file, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["VIN", "Year", "Make", "Model", "Dealer ID"])
            writer.writerows(records)

        flash(f"✅ All VIN records exported: {output_file}", "success")
        return send_file(output_file, as_attachment=True)

    except Exception as e:
        flash(f"❌ Export error: {e}", "danger")
        return redirect(url_for("dashboard"))

    finally:
        if conn:
            conn.close()

from datetime import datetime

@app.route("/add_vin/<int:dealer_id>", methods=["GET", "POST"])
def add_vin(dealer_id):
    role = session.get("role")

    if role not in ("admin", "dealer"):
        flash("Unauthorized access.", "danger")
        return redirect(url_for("login"))

    if role == "dealer" and dealer_id != session.get("dealer_id"):
        flash("Dealers can only add VINs for their own account.", "danger")
        return redirect(url_for("dashboard"))

    if role != "admin":
        available_credits = get_available_credits(dealer_id)
        print(f"💳 Available credits for dealer {dealer_id}: {available_credits}")
        if available_credits <= 0:
            flash("❌ This dealer is out of lien credits. Please buy more to add a new VIN.", "danger")
            return redirect(url_for("view_dealer", dealer_id=dealer_id))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM dealers WHERE dealer_id = ?", (dealer_id,))
    dealer_row = cursor.fetchone()

    if not dealer_row:
        flash("⚠ Dealer not found!", "danger")
        conn.close()
        return redirect(url_for("view_dealers"))

    dealer = dict(dealer_row)

    if request.method == "POST":
        try:
            vin_data = {key: request.form.get(key, "").strip() for key in request.form}
            vin_data["dealer_id"] = dealer_id
            vin_data["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            required_fields = [
                "vin", "year", "make", "model", "body", "color", "plate", "weight", "cweight", "odometer",
                "owner", "owner_address1", "owner_address2", "renewal", "renewal_address1", "renewal_address2",
                "lein_holder", "lein_holder_address1", "lein_holder_address2", "person_left", "person_left_address1", "person_left_address2",
                "county", "repair_amount", "ready_to_title", "status_downtown", "date_sent_downtown", "lien_canceled",
                "date_canceled", "transferred_harris_county", "cert1", "cert2", "cert3", "cert4", "cert5", "cert6",
                "cert1_status", "cert2_status", "cert3_status", "cert4_status", "cert5_status", "cert6_status",
                "date_left", "date_completed", "date_notified", "sale_date", "previous_owner", "previous_address",
                "buyer", "buyer_address1", "buyer_address2", "buyer_tdl", "status"
            ]

            for field in required_fields:
                vin_data.setdefault(field, "N/A")

            cursor.execute("""
                INSERT INTO vins (
                    vin, year, make, model, body, color, plate, weight, cweight, odometer,
                    owner, owner_address1, owner_address2, renewal, renewal_address1, renewal_address2,
                    lein_holder, lein_holder_address1, lein_holder_address2, person_left, person_left_address1, person_left_address2,
                    county, repair_amount, ready_to_title, status_downtown, date_sent_downtown, lien_canceled,
                    date_canceled, transferred_harris_county, cert1, cert2, cert3, cert4, cert5, cert6,
                    cert1_status, cert2_status, cert3_status, cert4_status, cert5_status, cert6_status,
                    date_left, date_completed, date_notified, sale_date, previous_owner, previous_address,
                    buyer, buyer_address1, buyer_address2, buyer_tdl, status, created_at, dealer_id
                ) VALUES (
                    :vin, :year, :make, :model, :body, :color, :plate, :weight, :cweight, :odometer,
                    :owner, :owner_address1, :owner_address2, :renewal, :renewal_address1, :renewal_address2,
                    :lein_holder, :lein_holder_address1, :lein_holder_address2, :person_left, :person_left_address1, :person_left_address2,
                    :county, :repair_amount, :ready_to_title, :status_downtown, :date_sent_downtown, :lien_canceled,
                    :date_canceled, :transferred_harris_county, :cert1, :cert2, :cert3, :cert4, :cert5, :cert6,
                    :cert1_status, :cert2_status, :cert3_status, :cert4_status, :cert5_status, :cert6_status,
                    :date_left, :date_completed, :date_notified, :sale_date, :previous_owner, :previous_address,
                    :buyer, :buyer_address1, :buyer_address2, :buyer_tdl, :status, :created_at, :dealer_id
                )
            """, vin_data)

            conn.commit()
            decrement_lien_credit(dealer_id)

            remaining_credits = get_available_credits(dealer_id)
            if remaining_credits == 1:
                send_low_credit_email(dealer["name"], dealer["email"])

            # Optional cert fields fallback
            optional_fields = [
                "cert2", "cert3", "cert4", "cert5", "cert6",
                "cert2_status", "cert3_status", "cert4_status", "cert5_status", "cert6_status"
            ]
            for field in optional_fields:
                vin_data.setdefault(field, "N/A")

            # Email dealer
            try:
                html_body = render_template("email_templates/new_vin_added.html",
                                            dealer_name=dealer["name"],
                                            vin_data=vin_data)
                for email in [dealer.get("email"), dealer.get("email2")]:
                    if email:
                        print(f"📨 Sending email to: {email}")
                        send_email(email, f"🚗 New Lien Added - {vin_data['vin']}", html_body)
                        print(f"📧 Email sent to: {email}")
            except Exception as e:
                print("❌ Email render/send error:", e)

            flash("✅ VIN added successfully!", "success")
            conn.close()
            return redirect(url_for("dashboard"))

        except Exception as e:
            print(f"❌ VIN insert error: {e}")
            flash("❌ Failed to add VIN. Please check your data or contact support.", "danger")

    return render_template("add_vin.html", dealer=dealer)

@app.route("/test_cert_returned/<int:vin_id>/<int:cert_number>")
def test_cert_returned(vin_id, cert_number):
    if session.get("role") != "admin":
        flash("Unauthorized access.", "danger")
        return redirect(url_for("login"))

    if cert_number not in range(1, 7):
        flash("Invalid certification number. Must be between 1–6.", "danger")
        return redirect(url_for("dashboard"))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Step 1: Get VIN record
    cursor.execute("SELECT * FROM vins WHERE rowid = ?", (vin_id,))
    vin_row = cursor.fetchone()
    if not vin_row:
        flash("⚠ VIN not found.", "danger")
        return redirect(url_for("dashboard"))

    vin = dict(vin_row)
    status_field = f"cert{cert_number}_status"
    today = datetime.today().strftime("%Y-%m-%d")
    new_status = f"Returned - {today}"

    # Step 2: Update cert status in DB and commit
    cursor.execute(f"""
        UPDATE vins SET {status_field} = ? WHERE rowid = ?
    """, (new_status, vin_id))
    conn.commit()

    # Step 3: Re-fetch updated VIN to confirm
    cursor.execute("SELECT * FROM vins WHERE rowid = ?", (vin_id,))
    vin = dict(cursor.fetchone())
    print(f"🧪 Confirmed DB value for {status_field}: {vin[status_field]}")

    # Step 4: Fetch dealer info
    cursor.execute("SELECT * FROM dealers WHERE dealer_id = ?", (vin["dealer_id"],))
    dealer_row = cursor.fetchone()
    conn.close()

    if not dealer_row:
        flash("⚠ Dealer not found for this VIN.", "danger")
        return redirect(url_for("dashboard"))

    dealer = dict(dealer_row)

    # Step 5: Email body with formatted table
    subject = f"📬 Certified Letter Returned - VIN {vin['vin']}"
    body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background-color: #fff; border-radius: 8px; padding: 20px; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
        <h2 style="background-color: #dc3545; color: white; padding: 10px; border-radius: 5px; text-align: center;">📬 Certified Letter Returned</h2>

        <p>Dear <strong>{dealer['name']}</strong>,</p>

        <p>The following certified letter has been returned for one of your active lien records:</p>

        <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
            <tr style="background-color: #f0f0f0;">
                <th style="padding: 8px; border: 1px solid #ddd;">VIN</th>
                <th style="padding: 8px; border: 1px solid #ddd;">Certification</th>
                <th style="padding: 8px; border: 1px solid #ddd;">Status</th>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">{vin['vin']}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">cert{cert_number}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{vin[status_field]}</td>
            </tr>
        </table>

        <p style="margin-top: 20px;">Please log in to your dashboard to take any required action.</p>

        <p>Thank you,<br><strong>The Mechanic Lien Team</strong></p>
        </div>
        </body>
    </html>
    """

    # Step 6: Send to both emails
    emails = [dealer.get("email"), dealer.get("email2")]
    print(f"📨 Attempting to send to: {emails}")

    for email in emails:
        if email:
            try:
                send_dealer_email(email, subject, body)
                print(f"✅ Return email sent to {email}")
            except Exception as e:
                print(f"❌ Failed to send to {email}: {e}")
        else:
            print("⚠ Skipped empty email slot.")

    flash(f"✅ Simulated cert{cert_number} returned and email sent.", "success")
    return redirect(url_for("dashboard"))

@app.route("/buy_extra_credit", methods=["GET"])
def buy_extra_credit():
    dealer_id = session.get("dealer_id")
    if not dealer_id:
        flash("Please log in to buy credits.", "warning")
        return redirect(url_for("login"))

    # Get current plan for dealer
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT product_id FROM subscriptions WHERE dealer_id = ?", (dealer_id,))
    row = cursor.fetchone()
    conn.close()

    product_id = row[0] if row else None
    if not product_id:
        product_id = "prod_S5UkBvabSnSyT0"  # Default to Pay-as-you-go if no subscription

    # Price (in cents) from your pricing map
    amount_cents = EXTRA_LIEN_PRICING.get(product_id, 10000)

    # Create Stripe Checkout Session
    session_data = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "unit_amount": amount_cents,
                "product_data": {
                    "name": "Extra Lien Credit",
                },
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=url_for("checkout_success", _external=True),
        cancel_url=url_for("dashboard", _external=True),
        metadata={
            "dealer_id": dealer_id,
            "product_id": product_id,
            "source": "extra_lien_purchase"
        }
    )

    # Store session info
    session["stripe_session_id"] = session_data.id
    session["last_product_id"] = product_id

    return redirect(session_data.url, code=303)

@app.route("/admin/vins")
def admin_view_vins():
    if session.get("role") != "admin":
        flash("Unauthorized access.", "danger")
        return redirect(url_for("dashboard"))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT vin, year, make, model, created_at, dealer_id 
        FROM vins 
        ORDER BY datetime(created_at) DESC 
        LIMIT 100
    """)
    vins = cursor.fetchall()
    conn.close()

    return render_template("admin_vins.html", vins=vins)

@app.route("/admin_logs")
def admin_logs():
    if session.get("role") != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM vins ORDER BY created_at DESC")
    vin_logs = cursor.fetchall()

    cursor.execute("SELECT * FROM email_logs ORDER BY timestamp DESC")
    email_logs = cursor.fetchall()

    cursor.execute("SELECT * FROM payments ORDER BY timestamp DESC")
    payment_logs = cursor.fetchall()

    conn.close()

    return render_template("admin_logs.html", vin_logs=vin_logs, email_logs=email_logs, payment_logs=payment_logs)



# -------------------- Run Flask App --------------------
if __name__ == "__main__":
    create_users_table()  # ✅ This must come BEFORE app.run()
    app.run(debug=True)

