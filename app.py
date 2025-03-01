from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import os
import sqlite3
import fitz  # PyMuPDF for PDF generation

import smtplib
from email.mime.text import MIMEText
import sqlite3
# --------------- SENDING EMAILS -----------------------------------------------
from flask import Flask, request, render_template, redirect, url_for, flash
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
DB_PATH = r"C:\Users\marka\Desktop\dealers_and_vins.db"

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
        vin_data["dealer_id"] = dealer_id  # Assign dealer_id to the new VIN

        # Required fields for VIN entry
        required_fields = [
            "vin", "year", "make", "model", "body", "color", "plate", "weight", "cweight", "odometer",
            "owner", "owner_address1", "owner_address2", "renewal", "renewal_address1", "renewal_address2",
            "lein_holder", "lein_holder_address1", "lein_holder_address2", "person_left", "person_left_address1", "person_left_address2",
            "county", "repair_amount", "ready_to_title", "status_downtown", "date_sent_downtown", "lien_canceled",
            "date_canceled", "transferred_harris_county", "cert1", "cert2", "cert3", "cert4", "cert5", "cert6",
            "cert1_status", "cert2_status", "cert3_status", "cert4_status", "cert5_status", "cert6_status",
            "date_left", "date_completed", "date_notified", "sale_date"
        ]

        # Default missing fields to "N/A"
        for field in required_fields:
            vin_data.setdefault(field, "N/A")

        # ✅ Insert new VIN into the database
        cursor.execute("""
            INSERT INTO vins (vin, year, make, model, body, color, plate, weight, 
                             cweight, odometer, owner, owner_address1, owner_address2, 
                             renewal, renewal_address1, renewal_address2, 
                             lein_holder, lein_holder_address1, lein_holder_address2, 
                             person_left, person_left_address1, person_left_address2,
                             county, repair_amount, ready_to_title, status_downtown, 
                             date_sent_downtown, lien_canceled, date_canceled, transferred_harris_county,
                             cert1, cert2, cert3, cert4, cert5, cert6, 
                             cert1_status, cert2_status, cert3_status, cert4_status, cert5_status, cert6_status,
                             date_left, date_completed, date_notified, sale_date, dealer_id) 
            VALUES (:vin, :year, :make, :model, :body, :color, :plate, :weight, 
                    :cweight, :odometer, :owner, :owner_address1, :owner_address2, 
                    :renewal, :renewal_address1, :renewal_address2, 
                    :lein_holder, :lein_holder_address1, :lein_holder_address2, 
                    :person_left, :person_left_address1, :person_left_address2,
                    :county, :repair_amount, :ready_to_title, :status_downtown, 
                    :date_sent_downtown, :lien_canceled, :date_canceled, :transferred_harris_county,
                    :cert1, :cert2, :cert3, :cert4, :cert5, :cert6, 
                    :cert1_status, :cert2_status, :cert3_status, :cert4_status, :cert5_status, :cert6_status,
                    :date_left, :date_completed, :date_notified, :sale_date, :dealer_id)
        """, vin_data)

        conn.commit()
        conn.close()

        # ✅ **Hardcoded Email Address** (Replace with your email)
        hardcoded_email = "your_email@example.com"

        # ✅ Fetch Dealer Emails and Add Hardcoded Email
        dealer_emails = [dealer["email"], dealer["email2"], hardcoded_email]  
        dealer_emails = [email for email in dealer_emails if email]  # Remove empty values

        print(f"📧 Debug: Dealer emails found: {dealer_emails}")  # Debugging log

        # ✅ Construct Email Template with Inline CSS & Cards
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

        # ✅ Send Email to All Recipients
        subject = f"🚗 Mechanic Lien Update: {vin_data['vin']}"
        for email in dealer_emails:
            send_dealer_email(email, subject, email_body)

        flash("✅ VIN added successfully and email sent!", "success")
        return redirect(url_for("view_dealers"))

    return render_template("add_vin.html", dealer=dealer)



def combine_address(name, address1, address2):
    """Helper function to format an address by combining name, address1, and address2."""
    parts = [name, address1, address2]
    return ", ".join(filter(None, parts))  # Removes None or empty values and joins with a comma


app = Flask(__name__)
app.secret_key = "your_secret_key"  # Required for session handling

# Define database path
DB_PATH = r"C:\Users\marka\Desktop\dealers_and_vins.db"
mechanic_lien_template_path = r"C:\Users\marka\Desktop\mechanic_lien_app\forms\letter_new_new.pdf"


# Define paths
import fitz
import os
from datetime import datetime
from flask import flash


# ✅ Ensure the correct export folder exists
export_folder = r"C:\Users\marka\Desktop\Mechanic Lien Work Space"
# Update PDF template directory
pdf_template_path = r"C:\Users\marka\Desktop\mechanic_lien_app\forms"



import fitz  # PyMuPDF
from datetime import datetime
from flask import flash

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
@app.route("/")
def index():
    return render_template("main_menu.html")

# -------------------- Dealer Management --------------------
@app.route("/view_dealers")
def view_dealers():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM dealers ORDER BY name ASC")
    dealers = cursor.fetchall()
    conn.close()
    return render_template("view_dealers.html", dealers=dealers)

@app.route("/add_dealer", methods=["GET", "POST"])
def add_dealer():
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

@app.route("/edit_vin/<int:vin_id>", methods=["GET", "POST"])
def edit_vin(vin_id):
    """Edit an existing VIN record."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == "POST":
        vin_data = {key: request.form.get(key, "") for key in request.form}
        vin_data["vin_id"] = vin_id

        cursor.execute("""
            UPDATE vins SET 
                vin = :vin, year = :year, make = :make, model = :model, body = :body, color = :color, plate = :plate, 
                weight = :weight, odometer = :odometer, owner = :owner, owner_address1 = :owner_address1, 
                owner_address2 = :owner_address2, repair_amount = :repair_amount
            WHERE rowid = :vin_id
        """, vin_data)

        conn.commit()
        conn.close()
        flash("✅ VIN updated successfully!")
        return redirect(url_for("search_vin"))

    cursor.execute("SELECT * FROM vins WHERE rowid = ?", (vin_id,))
    vin = cursor.fetchone()
    conn.close()

    return render_template("edit_vin.html", vin=vin)


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

    # Directory for form templates
    form_templates_dir = r"C:\Users\marka\Desktop\mechanic_lien_app\forms"
    
    generated_forms = []

    print(f"🔍 DEBUG: Selected forms -> {selected_forms}")  # Debugging Statement

    for form in selected_forms:
        file_name = f"{dealer_name}_{vin}_{form}.pdf"
        form_path = os.path.join(r"C:\Users\marka\Desktop\Mechanic Lien Work Space", file_name)
        pdf_template = os.path.join(form_templates_dir, f"{form.replace('-', '').replace(' ', '')}.pdf")

        # Ensure the PDF template exists before generating
        if not os.path.exists(pdf_template):
            flash(f"❌ Error: Form template not found at {pdf_template}", "danger")
            print(f"❌ Error: Form template not found at {pdf_template}")
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

            elif form == "VTR-130-SOF":  # ✅ Added Bonded Title Form
                generate_bonded_title_form(vin_data, form_path, pdf_template)

            else:
                flash(f"⚠ Unknown form selected: {form}", "warning")
                print(f"⚠ Unknown form selected: {form}")
                continue

            generated_forms.append(file_name)  # Keep track of generated files

        except Exception as e:
            flash(f"❌ Error generating {form}: {e}", "danger")
            print(f"❌ ERROR: Exception while generating {form}: {e}")

    if generated_forms:
        flash(f"✅ Forms generated: {', '.join(generated_forms)}", "success")
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


@app.route("/add_vin/<int:dealer_id>", methods=["GET", "POST"])
def add_vin(dealer_id):
    """Allows adding a new VIN to a selected dealer, including Cert statuses and sending an email notification."""

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Fetch dealer details
    cursor.execute("SELECT * FROM dealers WHERE dealer_id = ?", (dealer_id,))
    dealer_row = cursor.fetchone()

    if not dealer_row:
        flash("⚠ Dealer not found!", "danger")
        conn.close()
        return redirect(url_for("view_dealers"))

    dealer = dict(dealer_row)  # Convert SQLite row to dictionary

    if request.method == "POST":
        try:
            vin_data = {key: request.form.get(key, "").strip().upper() for key in request.form}
            vin_data["dealer_id"] = dealer_id  # Assign dealer_id to the new VIN

            # Ensure required fields are set
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
                vin_data.setdefault(field, "N/A")  # Default value to prevent missing keys

            # ✅ Insert VIN into the database
            cursor.execute("""
                INSERT INTO vins (vin, year, make, model, body, color, plate, weight, 
                                 cweight, odometer, owner, owner_address1, owner_address2, 
                                 renewal, renewal_address1, renewal_address2, 
                                 lein_holder, lein_holder_address1, lein_holder_address2, 
                                 person_left, person_left_address1, person_left_address2,
                                 county, repair_amount, ready_to_title, status_downtown, 
                                 date_sent_downtown, lien_canceled, date_canceled, transferred_harris_county,
                                 cert1, cert2, cert3, cert4, cert5, cert6, 
                                 cert1_status, cert2_status, cert3_status, cert4_status, cert5_status, cert6_status,
                                 date_left, date_completed, date_notified, sale_date, dealer_id) 
                VALUES (:vin, :year, :make, :model, :body, :color, :plate, :weight, 
                        :cweight, :odometer, :owner, :owner_address1, :owner_address2, 
                        :renewal, :renewal_address1, :renewal_address2, 
                        :lein_holder, :lein_holder_address1, :lein_holder_address2, 
                        :person_left, :person_left_address1, :person_left_address2,
                        :county, :repair_amount, :ready_to_title, :status_downtown, 
                        :date_sent_downtown, :lien_canceled, :date_canceled, :transferred_harris_county,
                        :cert1, :cert2, :cert3, :cert4, :cert5, :cert6, 
                        :cert1_status, :cert2_status, :cert3_status, :cert4_status, :cert5_status, :cert6_status,
                        :date_left, :date_completed, :date_notified, :sale_date, :dealer_id)
            """, vin_data)
            conn.commit()

            # ✅ Generate Certification Table (Only Include Non-Empty Certs)
            cert_rows = ""
            for i in range(1, 7):
                cert_key = f"cert{i}"
                status_key = f"cert{i}_status"
                cert_value = vin_data.get(cert_key, "").strip()
                status_value = vin_data.get(status_key, "").strip()

                if cert_value:  # Only include if cert is not blank
                    cert_rows += f"""
                        <tr>
                            <td style="text-align: left; padding: 8px; font-weight: bold;">{cert_value}</td>
                            <td style="text-align: right; padding: 8px; font-style: italic;">{status_value}</td>
                        </tr>
                    """

            cert_table = f"""
                <div style="border: 1px solid #ffc107; border-radius: 8px; margin-bottom: 10px;">
                    <div style="background: #ffc107; color: #000; padding: 10px; font-weight: bold; border-radius: 8px 8px 0 0;">
                        📜 Certification Details
                    </div>
                    <div style="padding: 10px;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <th style="text-align: left; padding: 8px;">Certification</th>
                                <th style="text-align: right; padding: 8px;">Status</th>
                            </tr>
                            {cert_rows if cert_rows else "<tr><td colspan='2' style='text-align: center;'>No Certifications Available</td></tr>"}
                        </table>
                    </div>
                </div>
            """ if cert_rows else ""

            # ✅ Construct the Email Body with Cards
            body = f"""
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Mechanic Lien Update</title>
            </head>
            <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                <div style="max-width: 600px; margin: auto; background: #ffffff; padding: 20px; border-radius: 10px; border: 1px solid #ddd;">
                    
                    <!-- 🚗 Header -->
                    <div style="background: #007bff; color: #ffffff; padding: 15px; text-align: center; font-size: 20px; font-weight: bold; border-radius: 10px 10px 0 0;">
                        🚗 Mechanic Lien Update - New VIN Assigned
                    </div>

                    <div style="padding: 20px;">
                        <p style="font-size: 16px;">Dear <strong>{dealer['name']}</strong>,</p>

                        <!-- 🚗 VIN Details -->
                        <div style="border: 1px solid #007bff; padding: 10px; border-radius: 8px; margin-bottom: 10px;">
                            <p><strong>VIN:</strong> {vin_data['vin']}</p>
                            <p><strong>Year:</strong> {vin_data['year']} | <strong>Make:</strong> {vin_data['make']} | <strong>Model:</strong> {vin_data['model']}</p>
                        </div>

                        <!-- 🏠 Owner, Renewal & Lien Holder -->
                        <div style="border: 1px solid #28a745; padding: 10px; border-radius: 8px; margin-bottom: 10px;">
                            <p><strong>Owner:</strong> {vin_data['owner']}</p>
                            <p><strong>Renewal:</strong> {vin_data['renewal']}</p>
                            <p><strong>Lien Holder:</strong> {vin_data['lein_holder']}</p>
                            <p><strong>Person Left:</strong> {vin_data['person_left']}</p>
                        </div>

			<!-- 📜 Certification Details -->
                        {cert_table}
                    </div>

                    <!-- 📩 Footer -->
                    <div style="text-align: center; padding: 10px; font-size: 12px; color: #666;">
                        <p>Best Regards,</p>
                        <p style="font-weight: bold; font-size: 14px;">The Mechanic Lien Team at My Title Guy</p>                        
                    </div>
                </div>
            </body>
            </html>
            """
            # ✅ Send the email
            send_dealer_email(dealer["email"], f"🚗 Mechanic Lien Update - {vin_data['vin']}", body)

        except Exception as e:
            print(f"❌ Error: {e}")

    return render_template("add_vin.html", dealer=dealer)

#------------------FIND CERTIFIED LETTERS AND SEND EMAIL ----------------------------------------------
from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime

# Define database path
DB_PATH = r"C:\Users\marka\Desktop\dealers_and_vins.db"

# ✅ Fix: Define the missing function
def get_db_connection():
    """Establish and return a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Allows fetching rows as dictionaries
    return conn


@app.route("/certify_tracking", methods=["GET", "POST"])
def certify_tracking():
    vin_data_list = []
    selected_vin_data = None
    certs_found = []
    emails_found = []
    status_field = None
    full_cert = None
    conn = None  # Prevent UnboundLocalError

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
                            update_query = f"UPDATE vins SET {status_field} = ? WHERE vin = ? AND dealer_id = ?"

                            try:
                                cursor.execute(update_query, (new_status, selected_vin, selected_vin_data["dealer_id"]))
                                conn.commit()

                                cursor.execute(
                                    f"SELECT vin, {status_field} FROM vins WHERE vin = ? AND dealer_id = ?",
                                    (selected_vin, selected_vin_data["dealer_id"]),
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
    cursor = conn.cursor()
    
    # Update the status to "Delivered - {current date}"
    system_date = datetime.now().strftime("%Y-%m-%d")
    update_query = f"UPDATE vins SET {matched_status_field} = ? WHERE id = ?"
    cursor.execute(update_query, (f"Delivered - {system_date}", vin_id))
    conn.commit()

    # Fetch updated record for email notification
    cursor.execute("SELECT * FROM vins WHERE id = ?", (vin_id,))
    vin_record = cursor.fetchone()
    conn.close()

    # Send email to dealer
    if vin_record and vin_record["dealer_id"]:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM dealers WHERE dealer_id = ?", (vin_record["dealer_id"],))
        dealer = cursor.fetchone()
        conn.close()

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
            
            'associate1': (300, 720),
            'associate1tdl': (430, 158),
            'associate2': (300, 690)
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


# -------------------- Run Flask App --------------------
if __name__ == "__main__":
    app.run(debug=True)
