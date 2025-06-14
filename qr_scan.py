import cv2
import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# DB connection
db = mysql.connector.connect(
    host=os.getenv("DB_HOST", "127.0.0.1"),
    port=os.getenv("DB_PORT", "3306"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    database=os.getenv("DB_NAME")
)
cursor = db.cursor()

def check_and_update_validity(qr_data):
    query = "SELECT used FROM tickets WHERE qr_data = %s"
    cursor.execute(query, (qr_data,))
    result = cursor.fetchone()

    if result is None:
        return "❌ Invalid Ticket"

    if result[0] == 1:
        return "❌ Invalid Ticket"

    # Mark ticket as used
    update_query = "UPDATE tickets SET used = 1 WHERE qr_data = %s"
    cursor.execute(update_query, (qr_data,))
    db.commit()
    return "✅ Valid Ticket"

# Initialize webcam
cap = cv2.VideoCapture(0)
detector = cv2.QRCodeDetector()

print("Starting QR code scanner... Press 'q' to quit.")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        data, bbox, _ = detector.detectAndDecode(frame)

        if data:
            validity = check_and_update_validity(data)

            if bbox is not None:
                pts = bbox[0].astype(int)
                for i in range(len(pts)):
                    cv2.line(frame, tuple(pts[i]), tuple(pts[(i + 1) % len(pts)]), (0, 255, 0), 2)

            cv2.putText(frame, validity, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1,
                        (0, 0, 255) if "Invalid" in validity else (0, 255, 0), 2)

            print(f"Scanned QR: {data} -> {validity}")

        cv2.imshow("QR Scanner", frame)
        if cv2.waitKey(1) == ord('q'):
            break

except KeyboardInterrupt:
    print("\nScanner stopped.")

cap.release()
cv2.destroyAllWindows()
cursor.close()
db.close()
