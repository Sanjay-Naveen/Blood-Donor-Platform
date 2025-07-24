from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from pymongo import MongoClient
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os # Import the os module for environment variables

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)


# ✅ MongoDB Atlas Connection
# Get MongoDB URI from environment variable for deployment, fallback to your hardcoded URI for local development
uri = os.environ.get(
    "MONGO_URI",
    "mongodb+srv://sanjaynaveen477:9025879408@cluster0.an0tz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
try:
    client = MongoClient(uri)  # Connect to MongoDB Atlas
    db = client["Sanjaynaveen"]  # Database Name
    student_collection = db["Sanjay"]  # Collection Name
    print("[INFO] Connected to MongoDB Atlas successfully!")
except Exception as e:
    print(f"[ERROR] Failed to connect to MongoDB Atlas: {e}")
    # In a real production app, you might want to exit or log this more severely

# ✅ Email Configuration
# Get email credentials from environment variables for deployment, fallback for local testing
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "sanjaynaveen477@gmail.com")
# IMPORTANT: Use your Gmail App Password here for SENDER_PASSWORD (refer to previous instructions)
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD", "ddbtycrtkqkqsacz") 

def send_email(receiver_email, student_name):
    """Function to send an email notification"""
    subject = "Urgent: Blood Donation Request"
    body = f"""
Dear {student_name},

We are urgently looking for blood donors, and your blood type matches the requirement.
If you're available, please contact us as soon as possible.
Contact : +91XXXXXXXXXX

Thank you for your support!

Regards,
proffessor : Ravi.K 
    """

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = receiver_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, receiver_email, msg.as_string())
        print(f"[INFO] Email successfully sent to {receiver_email}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        return False

# --- HTML Serving Routes (Define these first if they are your primary entry points) ---
@app.route('/')
def login():
    return render_template('login.html')  # Show login page

@app.route('/search')
def search():
    return render_template('search.html')  # Show search page

@app.route('/aboutus')
def aboutus():
    return render_template('aboutus.html')  # Show about us page

# --- API Routes ---
# ✅ Add a Student (POST)
@app.route("/add_student", methods=["POST"])
def add_student():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        name = data.get("name")
        roll_no = data.get("roll_no")
        phone = data.get("phone")
        department = data.get("department")
        blood_group = data.get("blood_group")
        email = data.get("email")

        if not all([name, roll_no, phone, department, blood_group, email]):
            return jsonify({"error": "Missing fields"}), 400

        student_data = {
            "name": name,
            "roll_no": roll_no,
            "phone": phone,
            "department": department,
            "blood_group": blood_group,
            "email": email
        }

        student_collection.insert_one(student_data)  # Store in MongoDB Atlas
        print(f"[INFO] Student {name} added to MongoDB Atlas!")
        return jsonify({"message": "Student added successfully!"}), 201
    except Exception as e:
        print(f"[ERROR] Failed to add student: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

# ✅ Get All Students (GET)
@app.route("/get_students", methods=["GET"])
def get_students():
    try:
        students = list(student_collection.find({}, {"_id": 0}))  # Fetch all students
        print(f"[INFO] Retrieved {len(students)} students from MongoDB Atlas.")
        return jsonify(students)
    except Exception as e:
        print(f"[ERROR] Failed to fetch students: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

# ✅ Delete student by roll_no
@app.route('/delete_student/<roll_no>', methods=['DELETE'])
def delete_student(roll_no):
    print(f"Received request to delete roll_no: {roll_no}")
    result = student_collection.delete_one({"roll_no": str(roll_no)})

    if result.deleted_count > 0:
        print(f"Deleted student: {roll_no}")
        return jsonify({"message": f"Student with roll_no {roll_no} deleted successfully!"})
    else:
        print(f"Student with roll_no {roll_no} not found!")
        return jsonify({"message": "Student not found!"}), 404


# ✅ Send Email to a Student (POST)
@app.route("/send_email", methods=["POST"])

def send_mail():
    try:
        data = request.json
        # Only 'name' is directly used to query student in database for email
        # The other fields (roll_no, phone, department, blood_group, email)
        # from the frontend are useful for local context/debugging but not strictly needed for DB lookup here.
        student_name = data.get("name") 

        # Find student in MongoDB to get their email
        student = student_collection.find_one({"name": student_name}, {"_id": 0, "email": 1})

        if not student:
            print(f"[WARNING] Student '{student_name}' not found for email sending.")
            return jsonify({"message": "Student email not found"}), 404

        receiver_email = student["email"]
        print(f"[INFO] Attempting to send email to {receiver_email} for student {student_name}.")

        if send_email(receiver_email, student_name):
            return jsonify({"message": f"Email sent to {student_name} ({receiver_email})"}), 200
        else:
            return jsonify({"message": "Failed to send email"}), 500
    except Exception as e:
        print(f"[ERROR] Email sending endpoint error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

# ✅ Test Route (API Status Route for Deployment Check)
@app.route("/api/status", methods=["GET"])
def api_status():
    return jsonify({"message": "Flask API is running with MongoDB Atlas & Email System!"})


# ✅ Run Flask App
# This block is primarily for local development.
# When deploying with Gunicorn (or another WSGI server), this block is often not executed
# as the WSGI server handles starting the 'app' instance directly.
if __name__ == "__main__":
    print("🔥 Flask server starting for local development...")
    # Uncomment the line below to run locally.
    # For deployment, the WSGI server (like Gunicorn) will run the 'app' instance.
    app.run(debug=True, host="0.0.0.0", port=5000)