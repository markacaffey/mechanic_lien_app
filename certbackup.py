import sys
sys.stdout.reconfigure(encoding='utf-8')
from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# 🔑 Secure Flask Session Key
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate a secure key

# 📂 Database Path
DB_PATH = r"C:\Users\marka\Desktop\dealers_and_vins.db"

# 📧 Email Configurations
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "markacaffey@gmail.com"  # Change this
EMAIL_PASSWORD = "zggb kioj fdcx kwvf"  # Use App Password for Gmail

# ✅ Function to get database connection
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Dictionary-like access
    return conn

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

# ✅ Homepage
@app.route("/")
def index():
    return render_template("main_menu.html")  # Ensure main_menu.html exists

@app.route("/certify_tracking", methods=["GET", "POST"])
def certify_tracking():
    vin_data_list = []
    selected_vin_data = None
    full_cert = None
    status_field = None

    if request.method == "POST":
        cert_last6 = request.form.get("cert_last6", "").strip()
        confirm_cert = request.form.get("confirm_cert")
        selected_vin = request.form.get("selected_vin")

        if not cert_last6:
            flash("❌ Please enter the last 6 digits of a certified letter.", "danger")
            return render_template("certify_tracking.html")

        print(f"🔍 Searching for Certified Letter ending in: {cert_last6}")

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
            print(f"✅ Matching VINs Found: {vin_data_list}")

            if selected_vin:
                selected_vin_data = next((vin for vin in vin_data_list if vin["vin"] == selected_vin), None)

                if selected_vin_data:
                    for i in range(1, 7):
                        cert_key = f"cert{i}"
                        if selected_vin_data.get(cert_key) and selected_vin_data[cert_key].endswith(cert_last6):
                            full_cert = selected_vin_data[cert_key]
                            status_field = f"cert{i}_status"
                            break

                    print(f"🔍 Matched Cert: {full_cert} for VIN: {selected_vin}, updating {status_field}")

                    if confirm_cert and full_cert and selected_vin and status_field:
                        new_status = f"DELIVERED ON {datetime.today().strftime('%Y-%m-%d')}"
                        update_query = f"UPDATE vins SET {status_field} = ? WHERE vin = ? AND dealer_id = ?"

                        print(f"🔹 Attempting to update {status_field} for VIN: {selected_vin}, Dealer ID: {selected_vin_data['dealer_id']}")
                        print(f"🔹 SQL Query: {update_query}")
                        print(f"🔹 Values: {new_status}, {selected_vin}, {selected_vin_data['dealer_id']}")

                        try:
                            cursor.execute(update_query, (new_status, selected_vin, selected_vin_data["dealer_id"]))
                            conn.commit()

                            # ✅ Verify the update
                            cursor.execute(
                                f"SELECT vin, {status_field} FROM vins WHERE vin = ? AND dealer_id = ?", 
                                (selected_vin, selected_vin_data["dealer_id"])
                            )
                            updated_record = cursor.fetchone()

                            print(f"✅ Database Response: {updated_record}")

                            if not updated_record or updated_record[1] != new_status:
                                print(f"❌ ERROR: {status_field} was not updated correctly.")
                                flash("❌ Database update failed. Please check logs.", "danger")
                            else:
                                print(f"✅ {status_field} successfully updated to {new_status}.")
                                flash("✅ Certification updated successfully!", "success")

                        except sqlite3.Error as e:
                            print(f"❌ Database update failed: {e}")
                            flash(f"❌ Database update error: {e}", "danger")

                        # ✅ Checking Database Lock Issues
                        cursor.execute("PRAGMA journal_mode;")
                        print(f"🔍 SQLite Journal Mode: {cursor.fetchone()}")

                        cursor.execute("PRAGMA integrity_check;")
                        print(f"🔍 SQLite Integrity Check: {cursor.fetchone()}")

                        dealer_id = selected_vin_data.get("dealer_id")

                        if dealer_id:
                            print(f"🔎 Looking for dealer with ID: {dealer_id}")
                            dealer_query = "SELECT dealer_id, email, email2, name FROM dealers WHERE dealer_id = ?"
                            cursor.execute(dealer_query, (dealer_id,))
                            dealer_info = cursor.fetchone()

                            if dealer_info:
                                dealer_email = dealer_info["email"]
                                dealer_email2 = dealer_info["email2"]
                                dealer_name = dealer_info["name"]

                                print(f"📧 Dealer Found: {dealer_name}, Email: {dealer_email}, Email2: {dealer_email2}")

                                if dealer_email or dealer_email2:
                                    subject = f"Mechanic Lien Update: {selected_vin_data['vin']}"
                                    email_body = f"""
                                    <p>Vehicle {selected_vin_data['vin']} has been updated to '{new_status}'.</p>
                                    """

                                    try:
                                        if dealer_email:
                                            print(f"📤 Sending Email to: {dealer_email}")
                                            send_email(dealer_email, subject, email_body)
                                        if dealer_email2:
                                            print(f"📤 Sending Email to: {dealer_email2}")
                                            send_email(dealer_email2, subject, email_body)
                                    except Exception as e:
                                        print(f"❌ Failed to send email: {e}")
                            else:
                                print(f"❌ ERROR: Dealer ID {dealer_id} not found in DB")

                        conn.close()
                        flash("✅ Certification marked as Delivered and Email Sent!", "success")
                        return redirect(url_for("certify_tracking"))

        conn.close()
    return render_template(
        "certify_tracking.html", 
        vin_data_list=vin_data_list, 
        selected_vin_data=selected_vin_data, 
        full_cert=full_cert, 
        status_field=status_field
    )

# ✅ List All Dealers
@app.route("/view_dealers")
def view_dealers():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM dealers ORDER BY name ASC")
    dealers = cursor.fetchall()
    conn.close()
    return render_template("view_dealers.html", dealers=dealers)

# ✅ Add Dealer
@app.route("/add_dealer", methods=["GET", "POST"])
def add_dealer():
    if request.method == "POST":
        dealer_data = {key: request.form.get(key, "") for key in request.form}
        conn = get_db_connection()
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

# ✅ Other Pages
@app.route("/generate_forms")
def generate_forms():
    return render_template("generate_forms.html")

@app.route("/select_dealer_for_vin")
def select_dealer_for_vin():
    return render_template("select_dealer_for_vin.html")

@app.route("/search_vin")
def search_vin():
    return render_template("search_vin.html")

@app.route("/generate_mechanic_lien")
def generate_mechanic_lien():
    return render_template("generate_mechanic_lien.html")

# ✅ Show All Routes for Debugging
@app.route("/routes")
def show_routes():
    return str(app.url_map)

# 🚀 Run the Flask App
if __name__ == "__main__":
    app.run(debug=True)
