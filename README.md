# 🎟️ MUS-E-TICK: Museum E-Ticketing Web App

**MUS-E-TICK** is a web-based application designed to streamline the experience of booking and validating museum and heritage site tickets — completely paperless. Our platform promotes convenience, reduces fraud, and enhances visitor insights through secure, smart ticketing solutions.

---

## 🌐 Project Overview

- Provides **paperless, pre-booked ticketing** for museums and monuments.
- Users can book tickets anytime using a smartphone, tablet, or computer.
- Eliminates the need to depend on ticket counters and prevents fraudulent transactions.
- Offers ticketing for both **individuals and groups**.
- Admin panel for tracking revenue, validating tickets, and monitoring visitor flow.
- QR-based ticket validation ensures **quick and secure** entry.
- Real-time crowd prediction suggests **optimal time slots** for visitors.
- Provides analytics on visitor demographics, helping museums plan exhibits/events effectively.

---

## 🧠 Key Features

- ✅ Web-based interface for mobile & desktop
- ✅ QR Code generation & scanning for tickets
- ✅ Smart scheduling based on crowd prediction
- ✅ Secure payment gateway integration
- ✅ Admin dashboard for validation and reports

---

## ⚙️ Getting Started

Follow these steps to set up the project locally:

```bash
# Create a virtual environment
python -m venv venv

# Activate the environment
.\venv\Scripts\activate   # On Windows
source venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

## 🗄️ Database Setup

Follow these steps to create and configure the MySQL database:

```sql
-- 🚀 Step 1: Create the Database
CREATE DATABASE bookticket;
USE bookticket;

-- 📋 Step 2: Create Tables

-- Table: form – for ticket booking
CREATE TABLE form (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fname VARCHAR(50),
    lname VARCHAR(50),
    phone VARCHAR(15),
    email VARCHAR(100),
    age INT,
    gender VARCHAR(10),
    timeslot VARCHAR(50),
    visitd DATE,
    notickets INT,
    child INT,
    adult INT,
    is_used BOOLEAN DEFAULT FALSE
);

-- Table: reviews – for user feedback
CREATE TABLE reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    review TEXT,
    stars INT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: tickets – for QR-based ticket validation
CREATE TABLE tickets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_email VARCHAR(100),
    museum_name VARCHAR(100),
    visit_date DATE,
    time_slot VARCHAR(20),
    qr_data VARCHAR(255) UNIQUE,
    used BOOLEAN DEFAULT FALSE,
    booked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
