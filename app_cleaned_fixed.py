from dotenv import load_dotenv
load_dotenv()
import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from werkzeug.security import generate_password_hash, check_password_hash
import fitz  # PyMuPDF for PDF generation

# Initialize Flask app BEFORE defining routes
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback_hardcoded_key_for_testing")

# Now you can safely define routes
@app.route("/")
def home():
    return redirect(url_for("dashboard"))


# Database path
DB_PATH = os.path.join(os.getcwd(), "dealers_and_vins.db")
print("🚨 Using DB from:", DB_PATH)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback_hardcoded_key_for_testing")


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
from flask import Flask, request, render_template, redirect, url_for, flash
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# DB_PATH = r"C:\Users\marka\Desktop\dealers_and_vins.db"

# SMTP Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "markacaffey@gmail.com"
EMAIL_PASSWORD = "zggb kioj fdcx kwvf"  # Use an App Password for Gmail

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

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ✅ SMTP Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "markacaffey@gmail.com"
EMAIL_PASSWORD = "zggb kioj fdcx kwvf"  # Use an App Password for security

def send_dealer_email(recipient, subject, message):
    """Sends an email to the dealer with VIN details."""
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(message, "html"))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, recipient, msg.as_string())
        server.quit()

        print(f"✅ Email sent to {recipient}")

    except Exception as e:
        print(f"❌ Email sending failed: {e}")



@app.route("/add_vin/<int:dealer_id>", methods=["GET", "POST"])
def add_vin(dealer_id):
    """Allows adding a new VIN to a selected dealer, then sends an email notification."""

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Fetch dealer details
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
            ) 
            VALUES (
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
        conn.close()

        # Prepare recipient emails (live dealer emails only)
        dealer_emails = []
        if dealer["email"]:
            dealer_emails.append(dealer["email"])
        if dealer["email2"]:
            dealer_emails.append(dealer["email2"])

        print(f"📧 Final email recipients: {dealer_emails}")

        # Build email body
        email_body = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #eef1f7;
                    margin: 20px;
                }}
                .container {{
                    background: #fff;
                    padding: 25px;
                    border-radius: 10px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                    max-width: 700px;
                    margin: auto;
                }}
                .header {{
                    background: #0056b3;
                    color: #fff;
                    text-align: center;
                    padding: 15px;
                    font-size: 20px;
                    font-weight: bold;
                    border-radius: 10px 10px 0 0;
                }}
                .card {{
                    background: #f8f9fa;
                    padding: 15px;
                    margin-top: 15px;
                    border-radius: 8px;
                    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
                }}
                .card-title {{
                    font-size: 18px;
                    font-weight: bold;
                    color: #0056b3;
                    margin-bottom: 10px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 10px;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 10px;
                    text-align: left;
                }}
                th {{
                    background: #0056b3;
                    color: #fff;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">🚗 Mechanic Lien Update</div>
                <p>Dear {dealer['name']},</p>
                <p>A new Mechanic Lien has been added to your dealership:</p>

                <div class="card">
                    <div class="card-title">🔹 Vehicle Information</div>
                    <table>
                        <tr><th>VIN</th><td>{vin_data['vin']}</td></tr>
                        <tr><th>Year</th><td>{vin_data['year']}</td></tr>
                        <tr><th>Make</th><td>{vin_data['make']}</td></tr>
                        <tr><th>Model</th><td>{vin_data['model']}</td></tr>
                    </table>
                </div>

                <div class="card">
                    <div class="card-title">📝 Ownership & Lien Details</div>
                    <table>
                        <tr><th>Owner</th><td>{vin_data['owner']}</td></tr>
                        <tr><th>Renewal</th><td>{vin_data['renewal']}</td></tr>
                        <tr><th>Lien Holder</th><td>{vin_data['lein_holder']}</td></tr>
                        <tr><th>Person Left</th><td>{vin_data['person_left']}</td></tr>
                    </table>
                </div>

                <div class="card">
                    <div class="card-title">📨 Certified Letters & Status</div>
                    <table>
                        <tr><th>Certification</th><th>Status</th></tr>
                        <tr><td>{vin_data['cert1']}</td><td>{vin_data['cert1_status']}</td></tr>
                        <tr><td>{vin_data['cert2']}</td><td>{vin_data['cert2_status']}</td></tr>
                        <tr><td>{vin_data['cert3']}</td><td>{vin_data['cert3_status']}</td></tr>
                    </table>
                </div>

                <p><strong>Best Regards,</strong><br>The Mechanic Lien Team at My Title Guy</p>
            </div>
        </body>
        </html>
        """

        subject = f"🚗 Mechanic Lien Update: {vin_data['vin']}"

        for email in dealer_emails:
            send_dealer_email(email, subject, email_body)

        flash("✅ VIN added successfully and email sent!", "success")
        return redirect(url_for("view_dealers"))

    return render_template("add_vin.html", dealer=dealer)

def combine_address(name, address1, address2):
    """Combines name and address fields into a single string."""
    parts = [name, address1, address2]
    return ", ".join([part for part in parts if part and part != "N/A"]).strip()

def generate_mechanic_letter(vin_data, file_path, pdf_template=None):
    """Generates a Mechanic Lien Letter PDF with proper X, Y coordinate placement."""

    if not vin_data:
        flash("⚠ No VIN data provided!", "danger")
        return

    # ✅ Set default template path if not provided
    if pdf_template is None:
        pdf_template = r"C:\Users\marka\Desktop\mechanic_lien_app\forms\letter_new_new.pdf"

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
    page.insert_text((57, 185), system_date, fontsize=12)  # System Date

    # ✅ Dealer Information
    dealer_name = vin_data.get('dealer_name', 'Unknown Dealer')
    dealer_address = vin_data.get('dealer_address', 'Unknown Address')
    dealer_city = vin_data.get('dealer_city', 'Unknown City')
    dealer_state = vin_data.get('dealer_state', 'Unknown State')
    dealer_zip = vin_data.get('dealer_zip', 'Unknown ZIP')
    dealer_phone = vin_data.get('dealer_phone', 'Unknown Phone')

    # ✅ Insert Dealer Details (Header Section)
    page.insert_text((57, 70), dealer_name, fontsize=14)  # Dealer Name
    page.insert_text((57, 80), dealer_address, fontsize=10)  # Dealer Address
    page.insert_text((57, 90), f"{dealer_city}, {dealer_state}, {dealer_zip}", fontsize=10)  # City, State, ZIP
    page.insert_text((57, 100), dealer_phone, fontsize=10)  # Phone Number

    # ✅ Insert Dealer Details (Footer Section)
    page.insert_text((57, 610), dealer_name, fontsize=12)  # Dealer Name (Footer)
    page.insert_text((57, 620), dealer_address, fontsize=10)  # Dealer Address (Footer)
    page.insert_text((57, 630), f"{dealer_city}, {dealer_state}, {dealer_zip}", fontsize=10)  # City, State, ZIP
    page.insert_text((57, 640), dealer_phone, fontsize=10)  # Phone Number

    # ✅ Vehicle Details
    vin = vin_data.get('vin', 'Unknown VIN')
    year = vin_data.get('year', 'Unknown Year')
    make = vin_data.get('make', 'Unknown Make')
    model = vin_data.get('model', 'Unknown Model')
    color = vin_data.get('color', 'Unknown Color')
    plate = vin_data.get('plate', 'Unknown Plate')
    repair_amount = f"${float(vin_data['repair_amount']):,.2f}" if vin_data.get('repair_amount') else "N/A"

    page.insert_text((180, 250), vin, fontsize=12)  # VIN
    page.insert_text((180, 270), f"{year} / {make}", fontsize=12)  # Year / Make
    page.insert_text((180, 290), model, fontsize=12)  # Model
    page.insert_text((180, 305), color, fontsize=12)  # Color
    page.insert_text((180, 325), plate, fontsize=12)  # Plate
    page.insert_text((180, 342), repair_amount, fontsize=12)  # Repair Amount

    # ✅ Owner Details
    owner_name = vin_data.get('owner', 'Unknown Owner')
    owner_address1 = vin_data.get('owner_address1', 'Unknown Address')
    owner_address2 = vin_data.get('owner_address2', '')

    owner_full = combine_address(owner_name, owner_address1, owner_address2)
    page.insert_text((190, 420), owner_full, fontsize=10)  # Owner Information

    # ✅ Renewal Name & Address
    renewal_name = vin_data.get('renewal', 'Unknown Renewal Name')
    renewal_address1 = vin_data.get('renewal_address1', 'Unknown Renewal Address')
    renewal_address2 = vin_data.get('renewal_address2', '')

    renewal_full = combine_address(renewal_name, renewal_address1, renewal_address2)
    page.insert_text((190, 445), renewal_full, fontsize=10)  # Renewal Information

    # ✅ Lien Holder Name & Address
    lien_holder_name = vin_data.get('lein_holder', 'Unknown Lien Holder')
    lien_holder_address1 = vin_data.get('lein_holder_address1', 'Unknown Lien Address')
    lien_holder_address2 = vin_data.get('lein_holder_address2', '')

    lien_holder_full = combine_address(lien_holder_name, lien_holder_address1, lien_holder_address2)
    page.insert_text((190, 470), lien_holder_full, fontsize=10)  # Lien Holder Information

    # ✅ Person Left Name & Address
    person_left = vin_data.get('person_left', 'Unknown Person')
    person_left_address1 = vin_data.get('person_left_address1', 'Unknown Address')
    person_left_address2 = vin_data.get('person_left_address2', '')

    person_left_full = combine_address(person_left, person_left_address1, person_left_address2)
    page.insert_text((190, 495), person_left_full, fontsize=10)  # Person Left Information

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
    pdf_writer.save(file_path)  # Save PDF
    pdf_writer.close()
    print(f"✅ Mechanic Lien Letter saved: {file_path}")

    flash(f"✅ Mechanic Lien Letter saved at: {file_path}", "success")


# -------------------- Home Page --------------------

# -------------------- Dealer Management --------------------
@app.route("/view_dealers")
def view_dealers():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Check user role and fetch appropriate data
    if session.get("role") == "dealer":
        cursor.execute("SELECT * FROM dealers WHERE dealer_id = ?", (session.get("dealer_id"),))
    else:
        cursor.execute("SELECT * FROM dealers ORDER BY name ASC")  # Admin sees all

    dealers = cursor.fetchall()
    conn.close()

    return render_template("view_dealers.html", dealers=dealers)

@app.route("/add_dealer", methods=["GET", "POST"])
def add_dealer():
    # 🔒 Only allow admin access
    if session.get("role") != "admin":
        flash("🚫 You are not authorized to access this page.", "danger")
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

        flash("✅ Dealer added successfully!", "success")
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
        ))

        conn.commit()
        conn.close()

        # ✅ Redirect to view the updated record
        return redirect(url_for("view_vin", vin_id=vin_id))

    # ✅ Fetch VIN data for GET request (displaying the form)
    cursor.execute("SELECT * FROM vins WHERE vin = ?", (vin_id,))
    vin = cursor.fetchone()
    conn.close()

    return render_template("view_vin.html", vin=vin)  # ✅ View & Edit in same page

# -------------------- Mechanic Lien Letter Generation --------------------
@app.route("/select_dealer_for_vin")
def select_dealer_for_vin():
    """Displays the list of dealers to select for adding a VIN."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM dealers ORDER BY name ASC")
    dealers = cursor.fetchall()
    conn.close()

    return render_template("select_dealer_for_vin.html", dealers=dealers)



@app.route("/generate_forms", methods=["GET", "POST"])
def generate_forms():
    """Generate multiple selected forms using stored VIN data."""

    if "selected_vin" not in session or "selected_forms" not in session:
        flash("⚠ Missing VIN or form selection. Start over!", "danger")
        return redirect(url_for("search_vin"))

    vin_data = session["selected_vin"]
    selected_forms = session["selected_forms"]
    dealer_name = vin_data.get("dealer_name", "UnknownDealer").replace(" ", "_")
    vin = vin_data.get("vin", "UnknownVIN")

    # Define directories
    form_templates_dir = os.path.join("static", "forms")
    export_folder = os.path.join("static", "generated_pdfs")
    generated_forms = []

    print(f"🔍 DEBUG: Selected forms -> {selected_forms}")

    for form in selected_forms:
        file_name = f"{dealer_name}_{vin}_{form}.pdf"
        form_path = os.path.join(export_folder, file_name)
        template_filename = f"{form.replace('-', '').replace(' ', '')}.pdf"
        pdf_template = os.path.join(form_templates_dir, template_filename)

        if not os.path.exists(pdf_template):
            flash(f"❌ Error: Form template not found at {pdf_template}", "danger")
            print(f"❌ Error: Form template not found at {pdf_template}")
            continue

        try:
            if form == "130-U":
                generate_130u_form(vin_data, form_path, pdf_template)
            elif form == "Mechanic Letter":
                generate_mechanic_letter(vin_data, form_path, pdf_template)
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
            else:
                flash(f"⚠ Unknown form selected: {form}", "warning")
                print(f"⚠ Unknown form selected: {form}")
                continue

            generated_forms.append(file_name)

        except Exception as e:
            flash(f"❌ Error generating {form}: {e}", "danger")
            print(f"❌ ERROR: Exception while generating {form}: {e}")

    # ✅ After generation logic
    if generated_forms:
        flash(f"✅ Forms generated: {', '.join(generated_forms)}", "success")

        # 🔒 TEMP: Send email to yourself only for testing
        recipient_email = os.getenv("TEST_EMAIL")  # Your testing email in .env
        send_form_email(recipient_email, dealer_name, generated_forms)
    else:
        flash("⚠ No forms were successfully generated.", "warning")

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



#------------------FIND CERTIFIED LETTERS AND SEND EMAIL ----------------------------------------------
from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash
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
    
    vin_data_list = []
    selected_vin_data = None
    certs_found = []
    emails_found = []
    status_field = None
    full_cert = None
    conn = None  

    if request.method == "POST":
        cert_last6 = request.form.get("cert_last6", "").strip()
        confirm_cert = request.form.get("confirm_cert")
        selected_vin = request.form.get("selected_vin")

        if not cert_last6:
            flash("❌ Please enter the last 6 digits of a certified letter.", "danger")
            return render_template("certify_tracking.html")

        print(f"🔍 Searching for Certified Letter ending in: {cert_last6}")

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # ✅ Fetch matching VINs
            query = """
                SELECT * FROM vins 
                WHERE substr(cert1, -6) = ? 
                OR substr(cert2, -6) = ? 
                OR substr(cert3, -6) = ? 
                OR substr(cert4, -6) = ? 
                OR substr(cert5, -6) = ? 
                OR substr(cert6, -6) = ?
            """
            cursor.execute(query, (cert_last6,) * 6)
            rows = cursor.fetchall()

            if rows:
                vin_data_list = [dict(row) for row in rows]

                for vin in vin_data_list:
                    for i in range(1, 7):
                        cert_key = f"cert{i}"
                        if vin.get(cert_key) and vin[cert_key].endswith(cert_last6):
                            certs_found.append({"cert": vin[cert_key], "vin": vin["vin"]})

                if selected_vin:
                    selected_vin_data = next((vin for vin in vin_data_list if vin["vin"] == selected_vin), None)

                    if selected_vin_data:
                        for i in range(1, 7):
                            cert_key = f"cert{i}"
                            if selected_vin_data.get(cert_key) and selected_vin_data[cert_key].endswith(cert_last6):
                                full_cert = selected_vin_data[cert_key]
                                status_field = f"cert{i}_status"
                                break

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

                                if not updated_record or updated_record[1] != new_status:
                                    flash("❌ Database update failed.", "danger")
                                else:
                                    flash("✅ Certification updated successfully!", "success")

                            except sqlite3.Error as e:
                                flash(f"❌ Database update error: {e}", "danger")

                        # ✅ Fetch Dealer Info & Emails
                        dealer_id = selected_vin_data.get("dealer_id")

                        if dealer_id:
                            cursor.execute(
                                "SELECT dealer_id, email, email2, name FROM dealers WHERE dealer_id = ?", 
                                (dealer_id,)
                            )
                            dealer_info = cursor.fetchone()

                            if dealer_info:
                                dealer_email = dealer_info["email"]
                                dealer_email2 = dealer_info["email2"]
                                dealer_name = dealer_info["name"]
                                emails_found = [email for email in [dealer_email, dealer_email2] if email]

                                if emails_found:
                                    cert_table_rows = "".join(
                                        f"<tr><td>Cert{i}</td><td>{selected_vin_data[f'cert{i}']}</td><td>{selected_vin_data[f'cert{i}_status']}</td></tr>"
                                        for i in range(1, 7) if selected_vin_data.get(f'cert{i}')
                                    )

                                    # ✅ Email Template with Cards & Categories (Including Owner Information)
                                    email_body = f"""
                                    <html>
                                    <head>
                                        <style>
                                            body {{
                                                font-family: Arial, sans-serif;
                                                background-color: #eef1f7;
                                                margin: 20px;
                                            }}
                                            .container {{
                                                background: #fff;
                                                padding: 25px;
                                                border-radius: 10px;
                                                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                                                max-width: 700px;
                                                margin: auto;
                                            }}
                                            .header {{
                                                background: #0056b3;
                                                color: #fff;
                                                text-align: center;
                                                padding: 15px;
                                                font-size: 20px;
                                                font-weight: bold;
                                                border-radius: 10px 10px 0 0;
                                            }}
                                            .card {{
                                                background: #f8f9fa;
                                                padding: 15px;
                                                margin-top: 15px;
                                                border-radius: 8px;
                                                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
                                            }}
                                            .card-title {{
                                                font-size: 18px;
                                                font-weight: bold;
                                                color: #0056b3;
                                                margin-bottom: 10px;
                                            }}
                                        </style>
                                    </head>
                                    <body>
                                        <div class="container">
                                            <div class="header">🚗 Mechanic Lien Update</div>
                                            <p>Dear {dealer_name},</p>
                                            <p>The mechanic lien process has been updated for the following vehicle:</p>

                                            <div class="card">
                                                <div class="card-title">🔹 Vehicle Information</div>
                                                <p>VIN: {selected_vin_data['vin']}</p>
                                                <p>Year: {selected_vin_data['year']}</p>
                                                <p>Make: {selected_vin_data['make']}</p>
                                                <p>Model: {selected_vin_data['model']}</p>
                                            </div>

                                            <div class="card">
                                                <div class="card-title">📝 Ownership & Lien Details</div>
                                                <p>Owner: {selected_vin_data['owner']}</p>
                                                <p>Renewal: {selected_vin_data['renewal']}</p>
                                                <p>Lien Holder: {selected_vin_data['lein_holder']}</p>
                                                <p>Person Who Left Vehicle: {selected_vin_data['person_left']}</p>
                                            </div>

                                            <div class="card">
                                                <div class="card-title">📨 Certified Letters & Status</div>
                                                <table>
                                                    <tr><th>Certification</th><th>Tracking Number</th><th>Status</th></tr>
                                                    {cert_table_rows}
                                                </table>
                                            </div>

                                            <p><strong>Best Regards,</strong><br>The Mechanic Lien Team at My Title Guy</p>
                                        </div>
                                    </body>
                                    </html>
                                    """

                                    subject = f"Mechanic Lien Update: {selected_vin_data['vin']}"

                                    try:
                                        for email in emails_found:
                                            send_email(email, subject, email_body)
                                    except Exception as e:
                                        print(f"❌ Failed to send email: {e}")

                        conn.close()
                        return redirect(url_for("certify_tracking"))

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

    flash("✅ Certified letter marked as delivered & email sent!", "success")
    return redirect(url_for("certify_tracking"))



#------------FORMS----------------------------------------------------------------------

import fitz

import os
import fitz  # PyMuPDF
from flask import flash

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
from flask import flash


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
            'cweight': (520, 130),
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
            'associate2': (300, 705)
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
from flask import flash

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
from flask import flash

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
from flask import flash

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
    form_templates_dir = os.path.join("static", "forms")
    export_folder = os.path.join("static", "generated_pdfs")
    file_name = f"{dealer_name}_{vin}_Mechanic_Lien.pdf"
    form_path = os.path.join(export_folder, file_name)
    pdf_template = os.path.join(form_templates_dir, "letter_new_new.pdf")

    print(f"🔍 Generating Mechanic Lien using template: {pdf_template}")

    if not os.path.exists(pdf_template):
        print(f"❌ ERROR: Mechanic Lien template not found at {pdf_template}")
        flash(f"❌ ERROR: Template not found at {pdf_template}", "danger")
        return redirect(url_for("search_vin"))

    try:
        generate_mechanic_letter(vin_data, form_path, pdf_template)
        print(f"✅ Mechanic Lien Letter saved at {form_path}")
        flash(f"✅ Mechanic Lien Letter generated: {file_name}", "success")

    except Exception as e:
        flash(f"❌ Error generating Mechanic Lien: {e}", "danger")
        print(f"❌ ERROR: Exception while generating Mechanic Lien: {e}")

    return redirect(url_for("search_vin"))

from flask import send_file

import sqlite3
import csv
import os
from flask import Flask, request, redirect, url_for, flash, send_file

def get_desktop_path():
    """Returns the path to the user's desktop."""
    return os.path.join(os.path.expanduser("~"), "Desktop")

def export_vin_records(last_4_vin, db_path, output_filename="vin_records.csv"):
    """Exports VIN records to a CSV file based on the last 4 digits."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        query = """
        SELECT vin, year, make, model, 
               owner, owner_address1, owner_address2,
               renewal, renewal_address1, renewal_address2,
               lein_holder, lein_holder_address1, lein_holder_address2,
               person_left, person_left_address1, person_left_address2
        FROM vins WHERE vin LIKE ?
        """
        cursor.execute(query, ('%' + last_4_vin,))
        records = cursor.fetchall()

        if not records:
            print(f"No records found with VIN ending in {last_4_vin}")
            return None  # No file to return

        headers = ['VIN', 'Last 4 VIN', 'Type', 'Name', 'Address1', 'Address2']
        desktop_path = get_desktop_path()
        csv_path = os.path.join(desktop_path, output_filename)

        with open(csv_path, mode='w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(headers)

            for record in records:
                vin, year, make, model = record[:4]
                last_4 = vin[-4:]
                
                # Data Mapping
                data_entries = [
                    ('Owner', record[4:7]),
                    ('Renewal', record[7:10]),
                    ('Lien Holder', record[10:13]),
                    ('Person Left', record[13:16])
                ]

                for label, (name, address1, address2) in data_entries:
                    if name and name.strip():
                        csv_writer.writerow([vin, last_4, label, name.strip(), address1.strip() if address1 else '', address2.strip() if address2 else ''])

        conn.close()
        return csv_path  # Return path for downloading

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return None

import os
from flask import send_file, flash, redirect, url_for

@app.route("/export_vin/<string:last_4_vin>", methods=["GET"])
def export_vin(last_4_vin):
  #  db_path = r"C:\Users\marka\Desktop\dealers_and_vins.db"
    output_filename = r"C:\Users\marka\Desktop\vin_records.csv"  # ✅ Always use the same file name

    # ✅ Overwrite the file every time by ensuring the function recreates it
    if os.path.exists(output_filename):
        os.remove(output_filename)  # ✅ Delete the file before writing new data

    file_path = export_vin_records(last_4_vin, db_path, output_filename)  # ✅ Ensure new data is written

    if file_path:
        flash(f"✅ VIN records exported successfully: {file_path}", "success")
        return send_file(file_path, as_attachment=True)
    else:
        flash(f"❌ No records found for {last_4_vin}", "danger")
        return redirect(url_for("search_vin"))

@app.route("/dashboard")
def dashboard():
    """Displays the dashboard with updated lien information."""

    print("🧪 Session contents:", dict(session))

    dealer_id = session.get("dealer_id")
    role = session.get("role")

    if not role:
        flash("Unauthorized access. Please log in.", "danger")
        return redirect(url_for("login"))

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

    # ✅ Get Plan Info for the logged-in user
    if role != "admin":
        cursor.execute("""
            SELECT plan, lien_limit, liens_used, billing_cycle_start
            FROM users WHERE dealer_id = ?
        """, (dealer_id,))
        user_plan_data = cursor.fetchone()
    else:
        user_plan_data = None

    conn.close()

    # ✅ Debug Output
    print("📌 Total Liens:", total_liens)
    print("📌 Open Liens Count:", len(open_liens))
    print("📌 Liens In Process:", liens_in_process)
    print("📌 Completed Liens:", liens_finished)
    print("📌 Recent Liens Count:", len(recent_liens))
    print("📌 Selected Filter:", status_filter)

    return render_template(
        "dashboard.html",
        total_liens=total_liens,
        open_liens=open_liens,
        liens_in_process=liens_in_process,
        liens_finished=liens_finished,
        recent_liens=recent_liens,
        status_filter=status_filter,
        user_plan_data=user_plan_data
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

        conn.commit()
        conn.close()

        flash("✅ Registration successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    print("🧪 /login route was hit")

    if request.method == "POST":
        pnumber = request.form["pnumber"].strip().upper()
        password = request.form["password"]

        print(f"🔎 Input pnumber: '{pnumber}' | length: {len(pnumber)} | hex: {pnumber.encode().hex().upper()}")
        print(f"📁 DB file path: {DB_PATH}")

        conn = sqlite3.connect(f"file:{DB_PATH}?mode=rw", uri=True)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Debug: Show users table structure
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        print(f"📊 Total users: {total_users}")

        cursor.execute("PRAGMA table_info(users)")
        for col in cursor.fetchall():
            print("🧱 users column:", dict(col))

        # Fetch all users to compare pnumber manually
        cursor.execute("SELECT id, pnumber, email, password_hash, role, dealer_id, account_status FROM users")
        all_users = cursor.fetchall()

        user = None
        print("🔍 Searching for pnumber match...")
        for row in all_users:
            row_pnumber = row["pnumber"].strip().upper()
            if row_pnumber == pnumber:
                print("✅ Match found!")
                user = dict(row)
                break

        if user:
            print(f"🔐 Validating password for: {user['pnumber']} (role: {user['role']})")
            if check_password_hash(user["password_hash"], password):
                if user.get("account_status", "active") != "active":
                    flash("⚠️ Your account is inactive. Please contact support.", "danger")
                    conn.close()
                    return redirect(url_for("login"))

                # Set session data
                session["user_id"] = user["id"]
                session["pnumber"] = user["pnumber"]
                session["role"] = user["role"]
                session["dealer_id"] = user.get("dealer_id")

                # Lookup dealer name from `dealers` table using pnumber
                cursor.execute("SELECT name FROM dealers WHERE pnumber = ?", (user["pnumber"],))
                result = cursor.fetchone()
                dealer_name = result["name"] if result else user["pnumber"]
                session["dealer_name"] = dealer_name

                print("🧾 Logged in dealer name:", dealer_name)
                conn.close()

                flash(f"✅ Welcome back, {dealer_name}!", "success")
                return redirect(url_for("dashboard"))  # Redirect to dashboard
            else:
                conn.close()
                flash("❌ Incorrect password.", "danger")
        else:
            conn.close()
            print("❌ No user found with that pnumber.")
            flash("❌ User not found.", "danger")

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
from flask import request

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")  # We'll get this in the next step

@app.route('/stripe/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('stripe-signature')
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

def send_dealer_pdf_link(dealer_email, dealer_name, file_name):
    try:
        pdf_url = f"{request.url_root}static/generated_pdfs/{file_name}"  # full URL to file
        subject = "Your Mechanic Lien Forms are Ready"
        body = f"""
        Hello {dealer_name},

        Your Mechanic Lien forms have been successfully generated for the selected VIN.

        📄 Download your form here:
        {pdf_url}

        Thank you for using My Title Guy, The Mechanic Lien Application!

        — The Mechanic Lien Team
        """

        msg = Message(subject, recipients=[dealer_email])
        msg.body = body

        mail.send(msg)
        print(f"✅ Email sent to {dealer_email}")

    except Exception as e:
        print(f"❌ Failed to send email: {e}")

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import request
from dotenv import load_dotenv

load_dotenv()  # Loads from .env

def send_form_email(recipient_email, dealer_name, generated_forms):
    """Sends an email with links to generated PDF forms."""
    print("📧 send_form_email() called")

    # Credentials from environment
    sender_email = os.getenv("EMAIL_ADDRESS")
    sender_password = os.getenv("EMAIL_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 587))

    print("📧 Attempting to send email...")
    print(f"Sender: {sender_email}")
    print(f"Recipient: {recipient_email}")
    print(f"SMTP Server: {smtp_server}:{smtp_port}")

    base_url = request.url_root.rstrip("/")
    logo_url = "https://i.postimg.cc/g074T8PN/logo.png"  # External logo link

    subject = f"📄 Your Mechanic Lien Forms Are Ready - {dealer_name}"

    # Start email body
    body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6;">
        <img src="{logo_url}" alt="My Title Guy Logo" style="width: 200px; margin-bottom: 20px;">
        <h2 style="color: #2a9d8f;">Mechanic Lien Forms Ready</h2>
        <p>Hi <strong>{dealer_name}</strong>,</p>
        <p>Your requested lien form(s) are ready to download. Click the buttons below to open each form:</p>
    """

    for file_name in generated_forms:
        file_url = f"{base_url}/static/generated_pdfs/{file_name}"
        body += f"""
        <a href="{file_url}" 
           style="display: inline-block; padding: 10px 20px; margin: 10px 0; background-color: #2a9d8f; 
                  color: #ffffff; text-decoration: none; border-radius: 5px; font-weight: bold;">
            {file_name}
        </a><br>
        """

    body += """
        <p>If you have any questions or need support, feel free to contact our team.</p>
        <p>Thank you for using <strong>My Title Guy</strong>.<br><br>
        Best regards,<br>
        <em>The Mechanic Lien Team</em></p>
        <hr>
        <small style="color: #999;">This message was automatically generated. Please do not reply to this email.</small>
      </body>
    </html>
    """

    # Compose and send the email
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            print(f"✅ Email sent to {recipient_email}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

@app.route("/send_test_email")
def send_test_email():
    test_email = os.getenv("TEST_EMAIL")
    test_forms = ["Bayway_Chevrolet_1111_VTR-265-FM.pdf"]
    dealer = "Bayway Chevrolet"
    send_form_email(test_email, dealer, test_forms)
    return "✅ Test email sent!"

from flask import Flask, redirect, url_for, session, flash, render_template
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "your-secret-key"  # if you use sessions

def get_db_connection():
    return sqlite3.connect("dealers_and_vins.db")

def can_create_lien(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT plan, liens_used, lien_limit, billing_cycle_start
        FROM users WHERE id = ?
    """, (user_id,))
    result = cursor.fetchone()
    conn.close()

    if not result:
        return False, "User not found"

    plan, liens_used, lien_limit, billing_start = result

    if plan == "flex":
        return True, "Flex user – redirect to payment before proceeding"

    if billing_start:
        start_date = datetime.fromisoformat(billing_start)
        if datetime.now() - start_date >= timedelta(days=30):
            reset_lien_usage(user_id)
            liens_used = 0

    if liens_used < lien_limit:
        return True, "Lien creation allowed"
    else:
        return False, "You’ve reached your lien limit for this billing cycle."

def increment_lien_usage(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET liens_used = liens_used + 1 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

def reset_lien_usage(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users
        SET liens_used = 0,
            billing_cycle_start = DATE('now')
        WHERE id = ?
    """, (user_id,))
    conn.commit()
    conn.close()

# Route to start a lien
@app.route("/start-lien")
def start_lien():
    user_id = session.get("user_id")  # assume you're storing user_id in session
    if not user_id:
        flash("You must be logged in.")
        return redirect(url_for("login"))

    allowed, message = can_create_lien(user_id)

    if allowed:
        if message.startswith("Flex"):
            flash("Pay $100 to proceed with lien.")
            return redirect(url_for("flex_payment"))  # Create this route separately
        else:
            increment_lien_usage(user_id)
            return redirect(url_for("lien_form"))  # Route where they actually fill out the form
    else:
        flash(message)
        return redirect(url_for("account"))  # Maybe show plan details / upgrade options

import stripe
from flask import request, redirect, url_for, session

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

@app.route("/flex-payment")
def flex_payment():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    # Optional: you could fetch the user's email from your DB to send to Stripe
    session_data = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": "One-Time Lien Payment"},
                "unit_amount": 10000  # $100 in cents
            },
            "quantity": 1
        }],
        mode="payment",
        success_url=url_for("flex_payment_success", _external=True),
        cancel_url=url_for("account", _external=True),
        metadata={"user_id": user_id}
    )
    return redirect(session_data.url)

@app.route("/flex-payment/success")
def flex_payment_success():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    # Optionally flag the user for a 1-lien credit
    # You could either:
    # - Increment `lien_limit` by 1 temporarily
    # - Or set a special "flex_credit" flag

    # Here's a simple approach: increase lien_limit by 1
    conn = sqlite3.connect("dealers_and_vins.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users SET lien_limit = lien_limit + 1 WHERE id = ?
    """, (user_id,))
    conn.commit()
    conn.close()

    flash("Payment successful. You can now start your lien.")
    return redirect(url_for("lien_form"))

@app.route("/lien-form", methods=["GET", "POST"])
def lien_form():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    if request.method == "POST":
        # Process form data (VIN, owner info, etc.)
        # Save to `vins` or related table

        increment_lien_usage(user_id)  # Already defined earlier
        flash("Lien submitted successfully.")
        return redirect(url_for("dashboard"))  # Or wherever you want to redirect

    return render_template("lien_form.html")  # Make this form template

@app.route("/account")
def account():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    conn = sqlite3.connect("dealers_and_vins.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT plan, lien_limit, liens_used, billing_cycle_start
        FROM users WHERE id = ?
    """, (user_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        plan, limit, used, start = result
    else:
        flash("User not found.")
        return redirect(url_for("dashboard"))

    return render_template("account.html", plan=plan, limit=limit, used=used, start=start)

@app.route("/debug-landing")
def debug_landing():
    try:
        return render_template("landing.html")
    except Exception as e:
        return f"❌ Template Error: {e}"


@app.route("/test-landing")
def test_landing():
    return render_template("landing.html")


# -------------------- Run Flask App --------------------
if __name__ == "__main__":
    create_users_table()  # ✅ This must come BEFORE app.run()
    app.run(debug=True)
