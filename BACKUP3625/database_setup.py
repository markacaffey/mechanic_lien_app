# Database Path
db_path = r"C:\Users\marka\Desktop\dealers_and_vins.db"
DB_PATH = r"C:\Users\marka\Desktop\dealers_and_vins.db"
from datetime import datetime
import os
import sqlite3
import fitz
import logging
import smtplib
from flask import Flask, render_template, request, flash, redirect, url_for, send_file
from email.message import EmailMessage
from email.utils import make_msgid

# Paths for database and PDF files
# db_path = r"C:\Users\marka\Desktop\dealers_and_vins.db"
pdf_template_path = r"C:\Users\marka\Desktop\mechanic_lien_app\letter_new_new.pdf"  # Ensure this is correct
export_folder = r"C:\Users\marka\Desktop\FORMS_TO_PRINT"
exported_pdf_path = os.path.join(export_folder, "generated_mechanic_letter.pdf")
# SMTP Credentials
SMTP_USER = "markacaffey@gmail.com"
SMTP_PASSWORD = "zggb kioj fdcx kwvf"
LOGO_PATH = "C:/Users/marka/Desktop/mtg logo for emails.png"

# Configure logging for debugging
logging.basicConfig(level=logging.INFO)

# Flask app initialization
app = Flask(__name__)
app.secret_key = 'your_secret_key'


# ----------------- Helper Functions -----------------

def send_email(receiver_emails, subject, body, logo_path):
    sender_email = SMTP_USER
    sender_password = SMTP_PASSWORD

    message = EmailMessage()
    message["From"] = sender_email
    message["To"] = ", ".join(receiver_emails)
    message["Subject"] = subject

    logo_cid = make_msgid()[1:-1]
    body = body.replace("cid:logo_cid", f"cid:{logo_cid}")
    message.set_content(body, subtype="html")

    try:
        with open(logo_path, "rb") as img:
            message.add_related(img.read(), maintype="image", subtype="png", cid=logo_cid)
    except FileNotFoundError:
        logging.error("Logo not found. Sending email without logo.")

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(message)
        logging.info("Email sent successfully!")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")


def send_email_update(cursor, vin_id):
    """
    Sends an HTML email update to the dealer(s) associated with the specified VIN.
    """
    cursor.execute('SELECT * FROM vins WHERE rowid = ?', (vin_id,))
    vin_info = cursor.fetchone()

    if not vin_info:
        logging.error("VIN data not found. Email not sent.")
        return

    vin_dict = dict(zip([description[0] for description in cursor.description], vin_info))

    cursor.execute('SELECT * FROM dealers WHERE dealer_id = ?', (vin_dict['dealer_id'],))
    dealer = cursor.fetchone()

    if not dealer:
        logging.error("Dealer data not found. Email not sent.")
        return

    dealer_dict = dict(zip([description[0] for description in cursor.description], dealer))

    receiver_emails = [dealer_dict['email']]
    if dealer_dict.get('email2'):
        receiver_emails.append(dealer_dict['email2'])

    # Prepare certificates data only if they are not empty
    certificates_html = ""
    for i in range(1, 7):
        cert_number = vin_dict.get(f'cert{i}', '')
        cert_status = vin_dict.get(f'cert{i}_status', '')
        if cert_number:  # Include only if cert_number is not empty
            certificates_html += f"""
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">Cert{i}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{cert_number}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{cert_status}</td>
            </tr>
            """

    # HTML Email Content
    email_body = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f8f9fa;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: auto;
                background: #ffffff;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            }}
            h2 {{
                color: #007BFF;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
            }}
            th {{
                background-color: #007BFF;
                color: #ffffff;
                padding: 10px;
                text-align: left;
            }}
            td {{
                padding: 10px;
                border: 1px solid #ddd;
            }}
            .section {{
                margin-bottom: 20px;
                padding: 15px;
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #f8f9fa;
            }}
            .footer {{
                margin-top: 20px;
                text-align: center;
                font-size: 14px;
                color: #888;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <img src="cid:logo_cid" alt="Company Logo" style="max-width: 100%; height: auto; margin-bottom: 20px;">
            <h2>Mechanic Lien Update</h2>
            <p>Dear {dealer_dict['name']},</p>

            <div class="section">
                <h3>Vehicle Information</h3>
                <table>
                    <tr><td><b>VIN:</b></td><td>{vin_dict['vin']}</td></tr>
                    <tr><td><b>Year:</b></td><td>{vin_dict['year']}</td></tr>
                    <tr><td><b>Make:</b></td><td>{vin_dict['make']}</td></tr>
                    <tr><td><b>Model:</b></td><td>{vin_dict['model']}</td></tr>
                    <tr><td><b>Color:</b></td><td>{vin_dict['color']}</td></tr>
                    <tr><td><b>Plate:</b></td><td>{vin_dict['plate']}</td></tr>
                </table>
            </div>

            <div class="section">
                <h3>Ownership Details</h3>
                <table>
                    <tr><td><b>Owner:</b></td><td>{vin_dict['owner']}</td></tr>
                    <tr><td><b>Renewal:</b></td><td>{vin_dict['renewal']}</td></tr>
                    <tr><td><b>Lien Holder:</b></td><td>{vin_dict['lein_holder']}</td></tr>
                </table>
            </div>

            <div class="section">
                <h3>Certified Letters and Status</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Certificate</th>
                            <th>Number</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {certificates_html}
                    </tbody>
                </table>
            </div>

            <p>Thank you,<br><b>The Mechanic Lien Team</b></p>

            <div class="footer">
                © {datetime.now().year} My Title Guy, Mechanic Lien. All rights reserved.
            </div>
        </div>
    </body>
    </html>
    """

    # Send Email
    send_email(receiver_emails, f"Mechanic Lien Update for VIN {vin_dict['vin']}", email_body, LOGO_PATH)


# ----------------- Flask Routes -----------------
@app.route('/view_dealers')
def view_dealers():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM dealers ORDER BY name ASC")
    dealers = cursor.fetchall()
    conn.close()
    return render_template("view_dealers.html", dealers=dealers)


@app.route('/')
def index():
    return render_template("main_menu.html")


@app.route('/add_dealer', methods=['GET', 'POST'])
def add_dealer():
    if request.method == 'POST':
        dealer_data = {key: request.form.get(key, '') for key in request.form}
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO dealers 
            (name, pnumber, address, city, state, zip, phone, email, email2, associate1, associate1tdl, associate2, associate2cell, expdate) 
            VALUES (:name, :pnumber, :address, :city, :state, :zip, :phone, :email, :email2, :associate1, :associate1tdl, :associate2, :associate2cell, :expdate)
        """, dealer_data)
        conn.commit()
        conn.close()
        flash("Dealer added successfully!")
        return redirect(url_for('view_dealers'))

    return render_template("add_dealer.html")


@app.route('/select_dealer_for_vin')
def select_dealer_for_vin():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM dealers ORDER BY name ASC")
    dealers = cursor.fetchall()
    conn.close()
    return render_template("select_dealer_for_vin.html", dealers=dealers)


@app.route('/add_vin/<int:dealer_id>', methods=['GET', 'POST'])
def add_vin(dealer_id):
    if request.method == 'POST':
        # Collect form data from the frontend
        vin_data = {
            'dealer_id': dealer_id,
            'vin': request.form.get('vin', '').strip(),
            'year': request.form.get('year', '').strip(),
            'make': request.form.get('make', '').strip(),
            'model': request.form.get('model', '').strip(),
            'body': request.form.get('body', '').strip(),
            'color': request.form.get('color', '').strip(),
            'plate': request.form.get('plate', '').strip(),
            'weight': request.form.get('weight', '').strip(),
            'odometer': request.form.get('odometer', '').strip(),
            'owner': request.form.get('owner', '').strip(),
            'owner_address1': request.form.get('owner_address1', '').strip(),
            'owner_address2': request.form.get('owner_address2', '').strip(),
            'renewal': request.form.get('renewal', '').strip(),
            'renewal_address1': request.form.get('renewal_address1', '').strip(),
            'renewal_address2': request.form.get('renewal_address2', '').strip(),
            'lein_holder': request.form.get('lein_holder', '').strip(),
            'lein_holder_address1': request.form.get('lein_holder_address1', '').strip(),
            'lein_holder_address2': request.form.get('lein_holder_address2', '').strip(),
            'person_left': request.form.get('person_left', '').strip(),
            'person_left_address1': request.form.get('person_left_address1', '').strip(),
            'person_left_address2': request.form.get('person_left_address2', '').strip(),
            'date_left': request.form.get('date_left', '').strip(),
            'date_completed': request.form.get('date_completed', '').strip(),
            'date_notified': request.form.get('date_notified', '').strip(),
            'sale_date': request.form.get('sale_date', '').strip(),
            'cert1': request.form.get('cert1', '').strip(),
            'cert2': request.form.get('cert2', '').strip(),
            'cert3': request.form.get('cert3', '').strip(),
            'cert4': request.form.get('cert4', '').strip(),
            'cert5': request.form.get('cert5', '').strip(),
            'cert6': request.form.get('cert6', '').strip(),
            'county': request.form.get('county', '').strip(),
            'repair_amount': request.form.get('repair_amount', '').strip(),
        }

        # Add default values for certificate statuses
        for i in range(1, 7):
            vin_data[f'cert{i}_status'] = "WAITING FOR SIGNATURE"

        # Database Insertion
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Perform the INSERT operation
            cursor.execute("""
                INSERT INTO vins (
                    dealer_id, vin, year, make, model, body, color, plate, weight, odometer,
                    owner, owner_address1, owner_address2, 
                    renewal, renewal_address1, renewal_address2, 
                    lein_holder, lein_holder_address1, lein_holder_address2, 
                    person_left, person_left_address1, person_left_address2,
                    date_left, date_completed, date_notified, sale_date,
                    cert1, cert1_status, cert2, cert2_status, cert3, cert3_status, 
                    cert4, cert4_status, cert5, cert5_status, cert6, cert6_status
                ) VALUES (
                    :dealer_id, :vin, :year, :make, :model, :body, :color, :plate, :weight, :odometer,
                    :owner, :owner_address1, :owner_address2,
                    :renewal, :renewal_address1, :renewal_address2,
                    :lein_holder, :lein_holder_address1, :lein_holder_address2,
                    :person_left, :person_left_address1, :person_left_address2,
                    :date_left, :date_completed, :date_notified, :sale_date,
                    :cert1, :cert1_status, :cert2, :cert2_status, :cert3, :cert3_status,
                    :cert4, :cert4_status, :cert5, :cert5_status, :cert6, :cert6_status
                )
            """, vin_data)

            # Commit the transaction
            conn.commit()

            # Fetch the last inserted VIN ID for confirmation or email updates
            cursor.execute("SELECT last_insert_rowid()")
            vin_id = cursor.fetchone()[0]
            logging.info(f"New VIN inserted with ID: {vin_id}")

            # Send email update if necessary
            send_email_update(cursor, vin_id)

            conn.close()
            flash("VIN added successfully and email notification sent!", "success")
            return redirect(url_for('view_dealers'))
        except Exception as e:
            logging.error(f"Error inserting VIN: {e}")
            flash("An error occurred while adding the VIN. Please try again.", "danger")
            return redirect(url_for('add_vin', dealer_id=dealer_id))

    # Render the Add VIN page with the dealer ID preloaded
    return render_template("add_vin.html", dealer_id=dealer_id)


@app.route('/generate_mechanic_letter', methods=['GET', 'POST'])
def generate_mechanic_letter():
    vins = []

    if request.method == 'POST':
        # Searching for a VIN
        if 'search_vin' in request.form:
            last_4_vin = request.form['last_4_vin'].strip()
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT vin, year, make, model, color, plate, repair_amount, 
                       owner, owner_address1, owner_address2, 
                       renewal, renewal_address1, renewal_address2, 
                       lein_holder, lein_holder_address1, lein_holder_address2, 
                       person_left, person_left_address1, person_left_address2, 
                       cert1, cert2, cert3, cert4, cert5, cert6, dealer_id 
                FROM vins 
                WHERE vin LIKE ?""", ('%' + last_4_vin,))
            vins = cursor.fetchall()
            conn.close()

            if vins:
                flash(f"Found {len(vins)} matching VIN(s).")
            else:
                flash("No matching VIN found.")

        # Export selected VIN to generate PDF
        elif 'export_vin' in request.form:
            selected_vin = request.form.get('selected_vin')

            if not selected_vin:
                flash("Please select a VIN to export.")
                return render_template("generate_mechanic_letter.html", vins=vins)

            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM vins WHERE vin = ?", (selected_vin,))
            vehicle_details = cursor.fetchone()

            if vehicle_details:
                dealer_id = vehicle_details['dealer_id']

                cursor.execute("SELECT * FROM dealers WHERE dealer_id = ?", (dealer_id,))
                dealer_details = cursor.fetchone()

                if dealer_details:
                    try:
                        pdf_writer = fitz.open(pdf_template_path)
                        merge_data_into_pdf(pdf_writer, vehicle_details, dealer_details)
                        pdf_writer.save(exported_pdf_path)
                        pdf_writer.close()
                        conn.close()

                        if os.path.exists(exported_pdf_path):
                            return send_file(exported_pdf_path, as_attachment=True, download_name="mechanic_lien.pdf")
                        else:
                            flash("Error: PDF generation failed.")
                    except Exception as e:
                        flash(f"An error occurred while generating the PDF: {e}")
                else:
                    flash("Dealer not found.")
            else:
                flash("VIN not found.")
            conn.close()

    return render_template("generate_mechanic_letter.html", vins=vins)


def merge_data_into_pdf(pdf_writer, vehicle_details, dealer_details):
    page = pdf_writer[0]  # Use the first page of the PDF

    # Get system date
    system_date = datetime.now().strftime("%A, %B %d, %Y")
    page.insert_text((57, 185), system_date, fontsize=12)  # System Date

    # Extract vehicle details
    vin = vehicle_details['vin']
    year = vehicle_details['year']
    make = vehicle_details['make']
    model = vehicle_details['model']
    color = vehicle_details['color']
    plate = vehicle_details['plate']
    repair_amount = f"${float(vehicle_details['repair_amount']):,.2f}" if vehicle_details['repair_amount'] else "N/A"

    # Combine Owner Information into a single line
    owner_full = f"{vehicle_details['owner']}, {vehicle_details['owner_address1']}, {vehicle_details['owner_address2']}".strip(
        ', ')

    # Combine Renewal Information into a single line
    renewal_full = f"{vehicle_details['renewal']}, {vehicle_details['renewal_address1']}, {vehicle_details['renewal_address2']}".strip(
        ', ')

    # Lien Holder Information
    lein_holder_full = f"{vehicle_details['lein_holder']}, {vehicle_details['lein_holder_address1']}, {vehicle_details['lein_holder_address2']}".strip(
        ', ')

    # Person Who Left Vehicle Information
    person_left_full = f"{vehicle_details['person_left']}, {vehicle_details['person_left_address1']}, {vehicle_details['person_left_address2']}".strip(
        ', ')

    # Certificate Statuses
    for i in range(1, 7):
        cert_number = vehicle_details.get(f'cert{i}', '')
        cert_status = vehicle_details.get(f'cert{i}_status', '')
        if cert_number:
            page.insert_text((370, 250 + (i * 20)), f"Cert{i}: {cert_number} - {cert_status}", fontsize=12)

    # Insert vehicle details
    page.insert_text((180, 250), vin, fontsize=12)
    page.insert_text((180, 270), f"{year} / {make}", fontsize=12)
    page.insert_text((180, 290), model, fontsize=12)
    page.insert_text((180, 305), color, fontsize=12)
    page.insert_text((180, 325), plate, fontsize=12)
    page.insert_text((180, 342), repair_amount, fontsize=12)

    # Insert combined Owner Information
    page.insert_text((190, 420), owner_full, fontsize=10)

    # Insert combined Renewal Information
    page.insert_text((190, 445), renewal_full, fontsize=10)

    # Insert combined Lien Holder Information
    page.insert_text((190, 470), lein_holder_full, fontsize=10)

    # Insert combined Person Who Left Vehicle Information
    page.insert_text((190, 495), person_left_full, fontsize=10)

    # Insert dealer details
    dealer_name = dealer_details['name']
    dealer_address = dealer_details['address']
    dealer_city = dealer_details['city']
    dealer_state = dealer_details['state']
    dealer_zip = dealer_details['zip']
    dealer_phone = dealer_details['phone']

    # Dealer info header
    page.insert_text((57, 70), dealer_name, fontsize=14)
    page.insert_text((57, 80), dealer_address, fontsize=10)
    page.insert_text((57, 90), f"{dealer_city}, {dealer_state} {dealer_zip}", fontsize=10)
    page.insert_text((57, 100), dealer_phone, fontsize=10)

    # Dealer info footer
    page.insert_text((57, 610), dealer_name, fontsize=12)
    page.insert_text((57, 620), dealer_address, fontsize=10)
    page.insert_text((57, 630), f"{dealer_city}, {dealer_state} {dealer_zip}", fontsize=10)
    page.insert_text((57, 640), dealer_phone, fontsize=10)

    logging.info(f"Inserted dealer name: {dealer_name}, VIN: {vin}, Repair Amount: {repair_amount}")


def merge_data_into_pdf(pdf_writer, vehicle_details, dealer_details):
    page = pdf_writer[0]  # Use the first page of the PDF

    # Get system date
    system_date = datetime.now().strftime("%A, %B %d, %Y")
    page.insert_text((57, 185), system_date, fontsize=12)  # System Date

    # Extract vehicle details
    vin = vehicle_details['vin']
    year = vehicle_details['year']
    make = vehicle_details['make']
    model = vehicle_details['model']
    color = vehicle_details['color']
    plate = vehicle_details['plate']
    repair_amount = f"${float(vehicle_details['repair_amount']):,.2f}" if vehicle_details['repair_amount'] else "N/A"

    # Combine Owner Information into a single line
    owner_full = f"{vehicle_details['owner']}, {vehicle_details['owner_address1']}, {vehicle_details['owner_address2']}".strip(
        ', ')

    # Combine Renewal Information into a single line
    renewal_full = f"{vehicle_details['renewal']}, {vehicle_details['renewal_address1']}, {vehicle_details['renewal_address2']}".strip(
        ', ')

    # Lien Holder Information
    lein_holder_full = f"{vehicle_details['lein_holder']}, {vehicle_details['lein_holder_address1']}, {vehicle_details['lein_holder_address2']}".strip(
        ', ')

    # Person Who Left Vehicle Information
    person_left_full = f"{vehicle_details['person_left']}, {vehicle_details['person_left_address1']}, {vehicle_details['person_left_address2']}".strip(
        ', ')

    # Certificate Statuses
    cert1 = vehicle_details['cert1']
    cert2 = vehicle_details['cert2']
    cert3 = vehicle_details['cert3']
    cert4 = vehicle_details['cert4']
    cert5 = vehicle_details['cert5']
    cert6 = vehicle_details['cert6']

    # Insert vehicle details
    page.insert_text((180, 250), vin, fontsize=12)
    page.insert_text((180, 270), f"{year} / {make}", fontsize=12)
    page.insert_text((180, 290), model, fontsize=12)
    page.insert_text((180, 305), color, fontsize=12)
    page.insert_text((180, 325), plate, fontsize=12)
    page.insert_text((180, 342), repair_amount, fontsize=12)

    # Insert combined Owner Information
    page.insert_text((190, 420), owner_full, fontsize=10)

    # Insert combined Renewal Information
    page.insert_text((190, 445), renewal_full, fontsize=10)

    # Insert combined Lien Holder Information
    page.insert_text((190, 470), lein_holder_full, fontsize=10)

    # Insert combined Person Who Left Vehicle Information
    page.insert_text((190, 495), person_left_full, fontsize=10)

    # Insert certificate statuses
    page.insert_text((370, 250), f"{cert1}", fontsize=12)
    page.insert_text((370, 270), f"{cert2}", fontsize=12)
    page.insert_text((370, 290), f"{cert3}", fontsize=12)
    page.insert_text((370, 310), f"{cert4}", fontsize=12)
    page.insert_text((370, 330), f"{cert5}", fontsize=12)
    page.insert_text((370, 350), f"{cert6}", fontsize=12)

    # Insert dealer details
    dealer_name = dealer_details['name']
    dealer_address = dealer_details['address']
    dealer_city = dealer_details['city']
    dealer_state = dealer_details['state']
    dealer_zip = dealer_details['zip']
    dealer_phone = dealer_details['phone']

    page.insert_text((57, 70), dealer_name, fontsize=14)
    page.insert_text((57, 80), dealer_address, fontsize=10)
    page.insert_text((57, 90), f"{dealer_city}, {dealer_state} {dealer_zip}", fontsize=10)
    page.insert_text((57, 100), dealer_phone, fontsize=10)

    logging.info(f"Inserted dealer name: {dealer_name}, VIN: {vin}, Repair Amount: {repair_amount}")


from flask import flash, redirect, url_for  # Ensure flash is imported


def fill_vtr265fm_form(merged_data, form_path):
    """Fills out the VTR-265-FM form with the given merged data."""

    # Save the form with a meaningful name
    output_folder = "C:/Users/marka/Desktop/Mechanic Lien Work Space/"
    output_path = os.path.join(output_folder,
                               f"{merged_data.get('name', 'UnknownDealer')}_{merged_data.get('vin', 'UnknownVIN')}_VTR-265-FM_Filled.pdf")

    # Open the form template
    doc = fitz.open(form_path)
    page = doc[0]  # Get first page of the PDF

    # Define field coordinates for the VTR-265-FM form
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
        'pnumber': (430, 200),
        'person_left': (290, 300),
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

    # Insert text into the appropriate form fields
    for field_name, coord in field_coordinates.items():
        field_value = merged_data.get(field_name.replace('_dup', '').replace('_combined', ''), '')

        if field_name == 'person_left_add_combined':
            field_value = f"{merged_data.get('person_left_address1', '')} {merged_data.get('person_left_address2', '')}".strip()
        elif field_name in ['combined_dealer_address', 'combined_dealer_address_2']:
            field_value = f"{merged_data.get('address', '')}, {merged_data.get('city', '')}, {merged_data.get('state', '')} {merged_data.get('zip', '')}".strip()

        page.insert_text(coord, f"{field_value}", fontsize=12, fontname="helv")

    # Save the filled form
    doc.save(output_path)
    logging.info(f"VTR-265-FM form successfully generated: {output_path}")

    return output_path


@app.route('/generate_forms', methods=['GET', 'POST'])
def generate_forms():
    if request.method == 'POST':
        last_6 = request.form.get('last_6_vin')

        if not last_6:
            flash("❌ Please enter the last 6 digits of the VIN.", "danger")
            return redirect(url_for('generate_forms'))

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vins WHERE vin LIKE ?", ('%' + last_6,))
        vins = cursor.fetchall()

        if not vins:
            flash("❌ No matching VIN found.", "danger")
            conn.close()
            return redirect(url_for('generate_forms'))

        vin_data = vins[0]  # Assume first result is correct
        merged_data = merge_vin_dealer_data(cursor, vin_data)

        if merged_data:
            selected_forms = request.form.getlist('forms')
            form_paths = {
                "130-U": "C:/Users/marka/Desktop/MECHANIC LIEN FORMS/130-U.pdf",
                "MV-265-M-2": "C:/Users/marka/Desktop/MECHANIC LIEN FORMS/MV-265-M-2.pdf",
                "VTR-265-FM": "C:/Users/marka/Desktop/MECHANIC LIEN FORMS/VTR-265-FM.pdf",
                "TS-5a": "C:/Users/marka/Desktop/MECHANIC LIEN FORMS/TS-5a.pdf",
                "TS-12": "C:/Users/marka/Desktop/MECHANIC LIEN FORMS/TS-12.pdf",
                "VTR-270": "C:/Users/marka/Desktop/MECHANIC LIEN FORMS/VTR-270.pdf",  # ✅ NEW FORM ADDED
            }

            printed_forms = []

            for form in selected_forms:
                if form in form_paths:
                    if form == "130-U":
                        fill_130u_form(merged_data, form_paths[form])
                    elif form == "MV-265-M-2":
                        fill_mv265m2_form(merged_data, form_paths[form])
                    elif form == "VTR-265-FM":
                        fill_vtr265fm_form(merged_data, form_paths[form])
                    elif form == "TS-5a":
                        fill_ts5a_form(merged_data, form_paths[form])
                    elif form == "TS-12":
                        fill_ts12_form(merged_data, form_paths[form])
                    elif form == "VTR-270":  # ✅ NEW CASE ADDED
                        fill_vtr270_form(merged_data, form_paths[form])

                    printed_forms.append(form)

            if printed_forms:
                flash(f"✅ Forms successfully printed: {', '.join(printed_forms)}", "success")
            else:
                flash("❌ No forms were selected for printing.", "danger")

        else:
            flash("❌ Failed to merge VIN and dealer data.", "danger")

        conn.close()
        return redirect(url_for('generate_forms'))

    return render_template('generate_forms.html')


def generate_130u_form(vin_data, dealer_data):
    # Logic for generating the 130-U form
    pass


def generate_mv265m2_form(vin_data, dealer_data):
    # Logic for generating the MV-265-M-2 form
    pass


def generate_vtr265fm_form(vin_data, dealer_data):
    # Logic for generating the VTR-265-FM form
    pass


def generate_ts5a_form(vin_data, dealer_data):
    # Logic for generating the TS-5a form
    pass


def generate_ts12_form(vin_data, dealer_data):
    # Logic for generating the TS-12 form
    pass


import fitz  # PyMuPDF for PDF manipulation


def fill_130u_form(merged_data, form_path):
    dealer_name = merged_data.get('name', 'UnknownDealer').replace(' ', '_')
    vin = merged_data.get('vin', 'UnknownVIN')
    output_path = f"C:/Users/marka/Desktop/Mechanic Lien Work Space/{dealer_name}_{vin}_130-U_Filled.pdf"

    doc = fitz.open(form_path)
    page = doc[0]  # Get first page of PDF

    # Existing field coordinates (DO NOT CHANGE)
    field_coordinates = {
        'vin': (50, 105),
        'year': (250, 105),
        'make': (300, 105),
        'model': (430, 105),
        'body': (380, 105),
        'color': (480, 105),
        'odometer': (140, 130),
        'plate': (50, 130),
        'weight': (430, 130),
        # 'cweight': (350, 120),
        'repair_amount': (250, 550),
        'county': (495, 280),
        'pnumber': (400, 305),
        'pnumber_dup': (500, 503),
    }

    dealer_field_coordinates = {
        'name': (50, 225),
        'address': (50, 280),
        'city': (200, 280),
        'state': (280, 280),
        'zip': (300, 280),
        'combined_dealer_name_city_state': (50, 305),
    }

    # ✅ NEW Fields with their correct X, Y Coordinates
    additional_field_coordinates = {
        'associate1tdl': (430, 158),  # Associate 1 TDL Number
        'associate2': (300, 690),  # Associate 2 Name
        'associate1': (300, 720),  # Associate 1 Name
    }

    # Merge Existing Fields
    for field_name, coord in field_coordinates.items():
        field_value = merged_data.get(field_name.replace('_dup', ''), '')
        page.insert_text(coord, f"{field_value}", fontsize=12, fontname="helv")

    # Merge Dealer Information
    for field_name, coord in dealer_field_coordinates.items():
        if field_name == 'combined_dealer_name_city_state':
            field_value = f"{merged_data.get('name', '')}, {merged_data.get('city', '')}, {merged_data.get('state', '')}".strip()
        else:
            field_value = merged_data.get(field_name, '')

        page.insert_text(coord, f"{field_value}", fontsize=12, fontname="helv")

    # ✅ Merge New Fields (Associate1, Associate1TDL, Associate2)
    for field_name, coord in additional_field_coordinates.items():
        field_value = merged_data.get(field_name, '')
        page.insert_text(coord, f"{field_value}", fontsize=12, fontname="helv")

    # Insert Extra Static Text
    page.insert_text((350, 623), "DEALER PURCHASE FOR RESALE ONLY", fontsize=10, fontname="helv")

    # Save Final Merged PDF
    doc.save(output_path)
    print(f"130-U form saved at: {output_path}")


from flask import send_file


def merge_vin_dealer_data(cursor, vin):
    """
    Merges VIN and dealer data by fetching the dealer info using dealer_id.
    """
    vin_dict = dict(zip([description[0] for description in cursor.description], vin))

    # Fetch dealer details
    cursor.execute('SELECT * FROM dealers WHERE dealer_id = ?', (vin_dict['dealer_id'],))
    dealer = cursor.fetchone()

    if dealer:
        dealer_dict = dict(zip([description[0] for description in cursor.description], dealer))
        merged_data = {**vin_dict, **dealer_dict}  # Merge both dictionaries
        return merged_data
    else:
        print("❌ Dealer information not found.")
        return None


@app.route('/generate_130u', methods=['POST'])
def generate_130u():
    """
    Flask route to generate a filled 130-U form for a given VIN.
    """
    last_6_vin = request.form.get('last_6_vin')
    if not last_6_vin:
        flash("Please enter the last 6 digits of the VIN.", "danger")
        return redirect(url_for('generate_forms'))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM vins WHERE vin LIKE ?", (f"%{last_6_vin}",))
    vin = cursor.fetchone()

    if not vin:
        flash("No matching VIN found.", "danger")
        conn.close()
        return redirect(url_for('generate_forms'))

    merged_data = merge_vin_dealer_data(cursor, vin)
    conn.close()

    if not merged_data:
        flash("Error retrieving dealer data.", "danger")
        return redirect(url_for('generate_forms'))

    # Generate the PDF
    form_path = "C:/Users/marka/Desktop/MECHANIC LIEN FORMS/130-U.pdf"
    output_path = fill_130u_form(merged_data, form_path)

    flash("130-U Form generated successfully!", "success")
    return redirect(url_for('download_form', form_name=output_path.split('/')[-1]))


@app.route('/download_form/<form_name>')
def download_form(form_name):
    """
    Flask route to download the generated 130-U form.
    """
    file_path = f"C:/Users/marka/Desktop/Mechanic Lien Work Space/{form_name}"
    return send_file(file_path, as_attachment=True)


# MV-265-M-2 Form Generation Function
def fill_mv265m2_form(merged_data, form_path):
    """Fills out the MV-265-M-2 form with the given merged data."""

    # Establish database connection
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Fetch dealer details
    cursor.execute('SELECT * FROM dealers WHERE dealer_id = ?', (merged_data['dealer_id'],))
    dealer = cursor.fetchone()

    if dealer:
        dealer_dict = dict(zip([description[0] for description in cursor.description], dealer))
        merged_data['dealer_name'] = dealer_dict.get('name', 'Unknown Dealer')
    else:
        merged_data['dealer_name'] = 'Unknown Dealer'  # Fallback if no dealer found

    # Save the form with a meaningful name
    output_folder = "C:/Users/marka/Desktop/Mechanic Lien Work Space/"
    output_path = os.path.join(output_folder,
                               f"{merged_data.get('name', 'UnknownDealer')}_{merged_data.get('vin', 'UnknownVIN')}_MV-265-M-2_Filled.pdf")

    # Open the form template
    doc = fitz.open(form_path)
    page = doc[0]  # Get first page of the PDF

    # Define field coordinates for the MV-265-M-2 form
    field_coordinates = {
        'vin': (130, 160),
        'year': (130, 190),
        'make': (180, 190),
        'date_notified': (420, 160),
        'date_completed': (420, 190),
        'sale_date': (420, 220),
        'dealer_name': (130, 220)
    }

    # Insert text into the appropriate form fields
    for field_name, coord in field_coordinates.items():
        field_value = merged_data.get(field_name, '')  # Get data from merged dictionary
        page.insert_text(coord, f"{field_value}", fontsize=12, fontname="helv")

    # Save the filled form
    doc.save(output_path)
    logging.info(f"✅ MV-265-M-2 form successfully generated: {output_path}")

    # Close database connection
    conn.close()

    return output_path


import fitz  # PyMuPDF for PDF handling


def fill_vtr265fm_form(merged_data, form_path):
    """
    Fills out the VTR-265-FM form with the given merged VIN and dealer data.
    """
    dealer_name = merged_data.get('name', 'UnknownDealer').replace(' ', '_')
    vin = merged_data.get('vin', 'UnknownVIN')
    output_path = f"C:/Users/marka/Desktop/Mechanic Lien Work Space/{dealer_name}_{vin}_VTR-265-FM_Filled.pdf"

    # ✅ Try to delete the file first (if it exists)
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
            print(f"✅ Deleted existing file: {output_path}")
        except PermissionError:
            print(f"❌ Cannot delete {output_path}, retrying...")
            time.sleep(1)  # Wait for 1 second and try again
            try:
                os.remove(output_path)
                print(f"✅ Successfully deleted file on retry: {output_path}")
            except Exception as e:
                print(f"❌ Error deleting file: {e}")
                return None  # Exit function if the file can't be deleted

    # ✅ Open the form template
    doc = fitz.open(form_path)
    page = doc[0]  # Get the first page of the PDF

    # ✅ Define all field coordinates, including combined PERSON_LEFT_ADDRESS
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
        'pnumber': (430, 200),
        'leftname': (290, 300),
        'person_left': (50, 250),  # ✅ Added PERSON_LEFT field
        'person_left_combined_address': (50, 273),  # ✅ Combined Address (Single Field)
        'date_left': (106, 322),
        'date_completed': (230, 322),
        'repair_amount': (350, 322),
        'repair_amount_dup': (510, 392),
        'date_notified': (106, 372),
        'sale_date': (106, 392),
        'odometer': (280, 523),
        'associate1_dup': (375, 695),
        'associate2_dup': (280, 660),
        'name_dup': (106, 416),
        'combined_dealer_address': (106, 440),
        'combined_dealer_address_2': (200, 395),
    }

    # ✅ Insert all data into the form
    for field_name, coord in field_coordinates.items():
        field_value = merged_data.get(field_name.replace('_dup', '').replace('_combined', ''), '')

        # ✅ Merge address fields into a single field
        if field_name == 'person_left_combined_address':
            field_value = f"{merged_data.get('person_left_address1', '')} {merged_data.get('person_left_address2', '')}".strip()
        elif field_name == 'person_left':
            field_value = f"{merged_data.get('person_left', '')}"
        elif field_name == 'combined_dealer_address':
            field_value = f"{merged_data.get('address', '')}, {merged_data.get('city', '')}, {merged_data.get('state', '')} {merged_data.get('zip', '')}".strip()
        elif field_name == 'combined_dealer_address_2':
            field_value = f"{merged_data.get('address', '')}, {merged_data.get('city', '')}, {merged_data.get('state', '')}".strip()

        page.insert_text(coord, f"{field_value}", fontsize=12, fontname="helv")

    # ✅ Try saving the file
    try:
        doc.save(output_path)
        print(f"✅ VTR-265-FM form saved successfully: {output_path}")
        return output_path  # ✅ Move return statement to a new line
    except Exception as e:
        print(f"❌ Error saving PDF: {e}")
        return None  # ✅ Return None if saving fails


def fill_ts5a_form(merged_data, form_path):
    """
    Fills out the TS-5a form with the given merged VIN and dealer data.
    """
    dealer_name = merged_data.get('name', 'UnknownDealer').replace(' ', '_')
    vin = merged_data.get('vin', 'UnknownVIN')
    output_path = f"C:/Users/marka/Desktop/Mechanic Lien Work Space/{dealer_name}_{vin}_TS-5a_Filled.pdf"

    # ✅ Try to delete the file first (if it exists)
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
            print(f"✅ Deleted existing file: {output_path}")
        except Exception as e:
            print(f"❌ Error deleting file: {e}")
            return None  # Exit function if the file can't be deleted

    # ✅ Open the form template
    doc = fitz.open(form_path)
    page = doc[0]  # Get the first page of the PDF

    # ✅ Define all field coordinates for TS-5a
    field_coordinates = {
        'sale_date': (450, 165),
        'plate': (420, 190),
        'vin': (350, 210),
        'name': (70, 270),
        'address': (75, 297),
        'combined_city_state_zip': (55, 325),
    }

    # ✅ Insert all data into the form
    for field_name, coord in field_coordinates.items():
        field_value = merged_data.get(field_name, '')

        # ✅ Merge dealer city, state, zip into a single field
        if field_name == 'combined_city_state_zip':
            field_value = f"{merged_data.get('city', '')}, {merged_data.get('state', '')} {merged_data.get('zip', '')}".strip()

        page.insert_text(coord, f"{field_value}", fontsize=12, fontname="helv")

    # ✅ Try saving the file
    try:
        doc.save(output_path)
        print(f"✅ TS-5a form saved successfully: {output_path}")
        return output_path  # ✅ Move return statement to a new line
    except Exception as e:
        print(f"❌ Error saving PDF: {e}")
        return None  # ✅ Return None if saving fails


import os
import fitz  # PyMuPDF for PDF generation


def fill_ts12_form(merged_data, form_path):
    """
    Fills out the TS-12 form with the given merged VIN and dealer data.
    """
    dealer_name = merged_data.get('name', 'UnknownDealer').replace(' ', '_')
    vin = merged_data.get('vin', 'UnknownVIN')
    output_path = f"C:/Users/marka/Desktop/Mechanic Lien Work Space/{dealer_name}_{vin}_TS-12_Filled.pdf"

    # ✅ Try to delete the file first (if it exists)
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
            print(f"✅ Deleted existing file: {output_path}")
        except Exception as e:
            print(f"❌ Error deleting file: {e}")
            return None  # Exit function if the file can't be deleted

    # ✅ Open the form template
    doc = fitz.open(form_path)
    page = doc[0]  # Get the first page of the PDF

    # ✅ Define all field coordinates for TS-12
    field_coordinates = {
        'name': (70, 135),  # Dealer Name
        'name_dup': (70, 350),  # ✅ Duplicate Dealer Name (New Coordinate)
        'combined_dealer_address': (70, 375),  # Address in a single field
        'pnumber': (340, 350),  # Dealer phone number
        'year': (70, 500),
        'make': (300, 500),
        'body': (450, 500),
        'vin': (70, 530),
        'associate1': (70, 600),
    }

    # ✅ Insert all data into the form
    for field_name, coord in field_coordinates.items():
        field_value = merged_data.get(field_name, '')

        # ✅ Merge dealer address components
        if field_name == 'combined_dealer_address':
            field_value = f"{merged_data.get('address', '')}, {merged_data.get('city', '')}, {merged_data.get('state', '')} {merged_data.get('zip', '')}".strip()

        # ✅ Ensure the dealer name is duplicated correctly
        elif field_name == 'name_dup':
            field_value = merged_data.get('name', '')

        page.insert_text(coord, f"{field_value}", fontsize=12, fontname="helv")

    # ✅ Try saving the file
    try:
        doc.save(output_path)
        print(f"✅ TS-12 form saved successfully: {output_path}")
        return output_path  # ✅ Return the saved file path
    except Exception as e:
        print(f"❌ Error saving PDF: {e}")
        return None  # ✅ Return None if saving fails


@app.route('/edit_dealer/<int:dealer_id>', methods=['GET', 'POST'])
def edit_dealer(dealer_id):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == 'POST':
        dealer_data = {key: request.form.get(key, '') for key in request.form}
        dealer_data['dealer_id'] = dealer_id

        cursor.execute("""
            UPDATE dealers SET 
                name = :name, pnumber = :pnumber, address = :address, city = :city, state = :state, zip = :zip, 
                phone = :phone, email = :email, email2 = :email2, associate1 = :associate1, associate1tdl = :associate1tdl, 
                associate2 = :associate2, associate2cell = :associate2cell, expdate = :expdate
            WHERE dealer_id = :dealer_id
        """, dealer_data)

        conn.commit()
        conn.close()
        flash("Dealer updated successfully!")
        return redirect(url_for('view_dealers'))

    cursor.execute("SELECT * FROM dealers WHERE dealer_id = ?", (dealer_id,))
    dealer = cursor.fetchone()
    conn.close()

    return render_template("edit_dealer.html", dealer=dealer)


import fitz  # PyMuPDF for PDF manipulation
import os
import time


def fill_vtr270_form(merged_data, form_path):
    """
    Fills out the VTR-270 form with merged VIN and dealer data.
    """
    dealer_name = merged_data.get('name', 'UnknownDealer').replace(' ', '_')
    vin = merged_data.get('vin', 'UnknownVIN')
    output_path = f"C:/Users/marka/Desktop/Mechanic Lien Work Space/{dealer_name}_{vin}_VTR-270_Filled.pdf"

    # ✅ Try to delete the file first (if it exists)
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
            print(f"✅ Deleted existing file: {output_path}")
        except PermissionError:
            print(f"❌ Cannot delete {output_path}, retrying...")
            time.sleep(1)  # Wait and try again
            try:
                os.remove(output_path)
                print(f"✅ Successfully deleted file on retry: {output_path}")
            except Exception as e:
                print(f"❌ Error deleting file: {e}")
                return None  # Exit function if file can't be deleted

    # ✅ Open the form template
    doc = fitz.open(form_path)
    page = doc[0]  # Get first page of PDF

    # ✅ Define all field coordinates
    field_coordinates = {
        'vin': (50, 458),  # Vehicle Identification Number (VIN)
        'year': (290, 458),  # Vehicle Year
        'make': (360, 458),  # Vehicle Make
        'body': (460, 458),  # Vehicle Body Type
        'model': (510, 458),  # Vehicle Model
        'name': (50, 530),  # Dealer Name (From Database)
        'combined_address': (50, 582),  # Dealer Address, City, State, Zip (Merged)
        'associate1': (275, 710),  # First Associate from Dealer Database
    }

    # ✅ Merge data into the PDF
    for field_name, coord in field_coordinates.items():
        field_value = merged_data.get(field_name, '')

        # Ensure combined fields are formatted properly
        if field_name == 'combined_address':
            field_value = f"{merged_data.get('address', '')}, {merged_data.get('city', '')}, {merged_data.get('state', '')} {merged_data.get('zip', '')}".strip()

        page.insert_text(coord, f"{field_value}", fontsize=12, fontname="helv")

    # ✅ Save the updated PDF
    try:
        doc.save(output_path)
        print(f"✅ VTR-270 form saved successfully: {output_path}")
        return output_path
    except Exception as e:
        print(f"❌ Error saving PDF: {e}")
        return None


import fitz  # PyMuPDF for PDF manipulation
import os
import sqlite3
from flask import Flask, render_template, request, flash, redirect, url_for, send_file

# Database & PDF Paths
DB_PATH = r"C:\Users\marka\Desktop\dealers_and_vins.db"
PDF_TEMPLATE_PATH = r"C:\Users\marka\Downloads\BOND FORMS.pdf"
OUTPUT_DIR = r"C:\Users\marka\Desktop\Mechanic Lien Work Space"

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Required for flash messages


def fetch_vehicle_data(last_six_vin):
    """Fetch vehicle data from the database using the last 6 digits of the VIN."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = """
    SELECT vin, year, make, body, model, buyer, buyer_address1, buyer_address2, odometer
    FROM vins
    WHERE vin LIKE ?
    """
    cursor.execute(query, ('%' + last_six_vin,))
    row = cursor.fetchone()
    conn.close()
    return row


def fill_bond_form(vehicle_data):
    """Fills out the Surety Bond Form with vehicle details from the database."""
    if not vehicle_data:
        return None  # Return None if no data is found

    try:
        # Open the PDF template
        doc = fitz.open(PDF_TEMPLATE_PATH)
        page = doc[0]

        # Extract data from the fetched row
        vin, year, make, body, model, buyer, buyer_address1, buyer_address2, odometer = vehicle_data

        # Combine Buyer Address fields
        full_address = f"{buyer_address1} {buyer_address2}".strip()

        # Define the X, Y coordinates for text insertion
        positions = {
            "VIN": (50, 130),
            "Year": (320, 130),
            "Make": (400, 130),
            "Body": (450, 130),
            "Model": (520, 130),
            "Buyer": (50, 195),
            "FullAddress": (50, 245),  # Combined address
            "Odometer": (320, 150),  # New position for odometer
        }

        # Insert data into the PDF
        page.insert_text(positions["VIN"], f"{vin}", fontsize=12)
        page.insert_text(positions["Year"], f"{year}", fontsize=12)
        page.insert_text(positions["Make"], f"{make}", fontsize=12)
        page.insert_text(positions["Body"], f"{body}", fontsize=12)
        page.insert_text(positions["Model"], f"{model}", fontsize=12)
        page.insert_text(positions["Buyer"], f"{buyer}", fontsize=12)
        page.insert_text(positions["FullAddress"], f"{full_address}", fontsize=12)
        page.insert_text(positions["Odometer"], f"{odometer}", fontsize=12)

        # Generate output filename
        dealer_name = buyer.replace(" ", "_")
        output_filename = f"{dealer_name}_{vin}_Surety_Bond.pdf"
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        # Save the merged PDF
        doc.save(output_path)
        print(f"✅ Surety Bond form saved: {output_path}")
        return output_path

    except Exception as e:
        print(f"❌ Error processing Surety Bond form: {e}")
        return None


@app.route('/vtr130sof_form', methods=['GET', 'POST'])
def vtr130sof_form():
    if request.method == 'POST':
        last_6_vin = request.form.get('last_6_vin', '').strip()

        if not last_6_vin:
            flash("❌ Please enter the last 6 digits of the VIN.", "danger")
            return redirect(url_for('vtr130sof_form'))

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vins WHERE vin LIKE ?", ('%' + last_6_vin,))
        vin_data = cursor.fetchone()
        conn.close()

        if not vin_data:
            flash("❌ No matching VIN found.", "danger")
            return redirect(url_for('vtr130sof_form'))

        # Generate PDF
        output_path = fill_vtr130sof_form(vin_data)

        if output_path:
            flash("✅ VTR-130-SOF Form generated successfully!", "success")
            return send_file(output_path, as_attachment=True)
        else:
            flash("❌ Failed to generate VTR-130-SOF Form.", "danger")

    return render_template("vtr130sof_form.html")


def fill_vtr130sof_form(merged_data):
    """Fills out the VTR-130-SOF form with the given merged VIN and dealer data."""
    form_path = r"C:\Users\marka\Desktop\MECHANIC LIEN FORMS\VTR-130-SOF.pdf"
    dealer_name = merged_data.get('name', 'UnknownDealer').replace(' ', '_')
    vin = merged_data.get('vin', 'UnknownVIN')
    output_path = f"C:/Users/marka/Desktop/Mechanic Lien Work Space/{dealer_name}_{vin}_VTR-130-SOF_Filled.pdf"

    # ✅ Try to delete the file first (if it exists)
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
            print(f"✅ Deleted existing file: {output_path}")
        except PermissionError:
            print(f"❌ Cannot delete {output_path}, retrying...")
            time.sleep(1)  # Wait for 1 second and try again
            try:
                os.remove(output_path)
                print(f"✅ Successfully deleted file on retry: {output_path}")
            except Exception as e:
                print(f"❌ Error deleting file: {e}")
                return  # Exit function if the file can't be deleted

    # ✅ Open the form template
    doc = fitz.open(form_path)
    page = doc[0]  # Get the first page of the PDF

    # ✅ Define all field coordinates
    field_coordinates = {
        'vin': (50, 130),
        'year': (270, 130),
        'make': (350, 130),
        'body': (425, 130),
        'model': (500, 130),
        'dealer_name': (50, 200),
        'dealer_address': (50, 225),
        'associate1': (290, 300),
        'combined_dealer_address': (50, 250),
    }

    # ✅ Insert all data into the form
    for field_name, coord in field_coordinates.items():
        field_value = merged_data.get(field_name, '')

        # Merge Address Fields
        if field_name == 'combined_dealer_address':
            field_value = f"{merged_data.get('address', '')}, {merged_data.get('city', '')}, {merged_data.get('state', '')} {merged_data.get('zip', '')}".strip()

        page.insert_text(coord, f"{field_value}", fontsize=12, fontname="helv")

    # ✅ Try saving the file
    try:
        doc.save(output_path)
        print(f"✅ VTR-130-SOF form saved successfully: {output_path}")
        return output_path
    except Exception as e:
        print(f"❌ Error saving PDF: {e}")
        return None


# ----------------- Main Application -----------------
if __name__ == "__main__":
    app.run(debug=True)
