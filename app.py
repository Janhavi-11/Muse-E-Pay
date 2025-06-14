import os
import io
import qrcode
import base64
import smtplib
import mysql.connector
from io import BytesIO
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from dotenv import load_dotenv
from collections import defaultdict
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY') or 'your_secret_key_here'

# DB connection
try:
    db = mysql.connector.connect(
        host=os.getenv("DB_HOST") or "localhost",
        port=os.getenv("DB_PORT") or "3306",
        user=os.getenv("DB_USER") or "your_db_user",
        password=os.getenv("DB_PASS") or "your_db_password",
        database=os.getenv("DB_NAME") or "your_database_name"
    )
    if not db.is_connected():
        print("Failed to connect to database.")
        quit()
except mysql.connector.Error as e:
    print(e.msg)
    quit()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/museums')
def museums():
    return render_template('museums.html')

# Add all museum routes here as shown above

@app.route("/review", methods=["GET"])
def review():
    return render_template('review.html')

@app.route("/submit_review", methods=["POST"])
def submit_review():
    try:
        data = request.get_json()
        name = data.get("name")
        review = data.get("review")
        stars = data.get("stars")

        if not name or not review or not stars:
            return jsonify({"success": False, "error": "Missing required fields"}), 400

        query = "INSERT INTO reviews (name, review, stars) VALUES (%s, %s, %s)"
        values = (name, review, stars)

        with db.cursor() as cursor:
            cursor.execute(query, values)
            db.commit()

        return jsonify({"success": True})

    except Exception as e:
        print("Error submitting review:", e)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/get_reviews", methods=["GET"])
def get_reviews():
    try:
        with db.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT name, review, stars FROM reviews ORDER BY id DESC")
            reviews = cursor.fetchall()
        return jsonify({"success": True, "reviews": reviews})
    except Exception as e:
        print("Error fetching reviews:", e)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/form', methods=['GET', 'POST'])
def form():
    museum_name = request.args.get('museum_name')
    session['museum_name'] = museum_name

    availability = defaultdict(lambda: {"Morning": 0, "Afternoon": 0, "Evening": 0})
    try:
        with db.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT visitd, timeslot, COUNT(*) as count FROM form GROUP BY visitd, timeslot")
            for row in cursor.fetchall():
                date_str = row['visitd'].strftime("%Y-%m-%d")
                availability[date_str][row['timeslot']] = row['count']
    except Exception as e:
        print("Error fetching availability:", e)

    return render_template('form.html', museum_name=museum_name, availability=availability)

@app.route('/form1', methods=['POST'])
def form1():
    try:
        # Read form values
        data = {k: request.form.get(k, '').strip() for k in ['fname', 'lname', 'phone', 'email', 'age', 'gender', 'timeslot', 'visitd', 'notickets', 'child', 'adult', 'museum_name']}
        session['museum_name'] = data['museum_name']

        # Insert into DB
        query = """
        INSERT INTO form (fname, lname, phone, email, age, gender, timeslot, visitd, notickets, child, adult)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = tuple(data[k] for k in ['fname', 'lname', 'phone', 'email', 'age', 'gender', 'timeslot', 'visitd', 'notickets', 'child', 'adult'])

        with db.cursor(buffered=True) as cursor:
            cursor.execute(query, values)
            db.commit()
            cursor.execute("SELECT LAST_INSERT_ID()")
            ticket_id = cursor.fetchone()[0]

        session['email'] = data['email']
        session['ticket_id'] = ticket_id

        return redirect(url_for("form_print"))

    except Exception as e:
        print("Form submission error:", e)
        return redirect(url_for('form'))

@app.route('/form_print')
def form_print():
    email = session.get('email')
    ticket_id = session.get('ticket_id')
    museum_name = session.get('museum_name', 'Unknown Museum')

    if not email or not ticket_id:
        return redirect(url_for('form'))

    try:
        with db.cursor(buffered=True) as cursor:
            cursor.execute("""
                SELECT id, visitd, timeslot, fname, lname, notickets 
                FROM form WHERE id = %s
            """, (ticket_id,))
            rs = cursor.fetchone()

        if not rs:
            raise Exception("Ticket not found.")

        ticket_id, visitd, timeslot, fname, lname, notickets = rs
        name = f"{fname} {lname}"

        # QR text
        qr_text = f"""DATE: {visitd}\nTime-slot: {timeslot}\nName: {name}\nTicket Number: {ticket_id}\nNo. of People: {notickets}"""

        # Generate QR code
        qr_buffer = BytesIO()
        qr = qrcode.QRCode(version=1, box_size=4, border=1)
        qr.add_data(qr_text)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color='black', back_color='white')
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)

        # Save QR to DB
        with db.cursor() as cursor:
            cursor.execute("""
                INSERT INTO tickets (user_email, museum_name, visit_date, time_slot, qr_data)
                VALUES (%s, %s, %s, %s, %s)
            """, (email, museum_name, visitd, timeslot, qr_text))
            db.commit()

        # Send email
        message = MIMEMultipart('related')
        message['From'] = os.getenv('SMTP_USER')
        message['To'] = email
        message['Subject'] = 'Your Museum Ticket Confirmation'

        html_body = render_template(
            'ticket_email.html',
            user_name=name,
            museum_name=museum_name,
            date=visitd,
            slot_time=timeslot,
            ticket_count=notickets,
            qr_code="cid:qr_code"
        )
        message.attach(MIMEText(html_body, 'html'))

        qr_image = MIMEImage(qr_buffer.getvalue(), _subtype="png")
        qr_image.add_header('Content-ID', '<qr_code>')
        qr_image.add_header('Content-Disposition', 'inline', filename="qrcode.png")
        message.attach(qr_image)

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASS'))
            server.send_message(message)

        img_base64 = base64.b64encode(qr_buffer.getvalue()).decode('utf-8')

        return render_template(
            'form_print.html',
            visitd=visitd,
            timeslot=timeslot,
            name=name,
            id=ticket_id,
            notickets=notickets,
            img=img_base64,
            museum_name=museum_name
        )

    except Exception as e:
        print("Error in form_print:", e)
        return redirect(url_for('form'))

if __name__ == "__main__":
    app.run(debug=True)
