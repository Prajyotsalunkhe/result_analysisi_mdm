import os
import json
import threading
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import User, ResultAnalysis, MinorDegreeApplication
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Import faculty modules
from extractor import extract_result_data
from mdm_logic import seat_allotment

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-for-development' # Change in production

if os.environ.get('FIREBASE_CREDENTIALS'):
    # Vercel has a read-only filesystem, so we must use /tmp for uploads
    UPLOAD_FOLDER = '/tmp'
else:
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize Firebase Admin SDK
firebase_creds_json = os.environ.get('FIREBASE_CREDENTIALS')
if firebase_creds_json:
    # Running on Vercel
    cred_dict = json.loads(firebase_creds_json)
    cred = credentials.Certificate(cred_dict)
else:
    # Running locally
    cred = credentials.Certificate("student-portal-9f4f6-firebase-adminsdk-fbsvc-614a27b548.json")

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client(database_id="native-db")

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    try:
        user_ref = db.collection('users').document(str(user_id)).get()
        if user_ref and user_ref.exists:  # type: ignore
            data = user_ref.to_dict()  # type: ignore
            return User.from_dict(data, user_ref.id)  # type: ignore
    except Exception as e:
        print(f"Error loading user: {e}")
    return None

# --- SHARED / PUBLIC ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

# --- STUDENT ROUTES ---

@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('login.html')

        users_ref = db.collection('users').where('username', '==', username).stream()
        user_doc = None
        for doc in users_ref:
            user_doc = doc
            break
        
        if user_doc:
            user = User.from_dict(user_doc.to_dict(), user_doc.id)
            if password and check_password_hash(user.password_hash, password):
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                flash('Login failed. Check your username and password.', 'error')
        else:
            flash('Login failed. Check your username and password.', 'error')
    
    return render_template('login.html')

@app.route('/student_register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('register.html')

        users_ref = db.collection('users').where('username', '==', username).stream()
        user_exists = any(True for _ in users_ref)
        
        if user_exists:
            flash('Username already exists.', 'error')
            return redirect(url_for('student_register'))

        # Create new user document
        user_data = {
            'username': username,
            'password_hash': generate_password_hash(password) if password else None
        }
        db.collection('users').add(user_data)

        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('student_login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    if current_user.is_authenticated:
        logout_user()
    session.pop('faculty_logged_in', None)
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Fetch user's existing records
    result_ref = db.collection('result_analysis').where('user_id', '==', str(current_user.id)).stream()
    result_submissions = [ResultAnalysis.from_dict(doc.to_dict(), doc.id) for doc in result_ref]
    
    mdm_ref = db.collection('minor_degree_applications').where('user_id', '==', str(current_user.id)).stream()
    mdm_submissions = [MinorDegreeApplication.from_dict(doc.to_dict(), doc.id) for doc in mdm_ref]
    
    return render_template('dashboard.html', results=result_submissions, mdm=mdm_submissions)

def process_result_background(filepath, user_id, department, roll_no):
    """Background task to extract PDF and save to faculty collection structure"""
    try:
        data = extract_result_data(pdf_path=filepath)
        if data:
            meta = data['metadata']
            # Try to get PRN from text, fallback to user_id if failed
            prn = meta.get('prn')
            if not prn or prn == "UNKNOWN_PRN":
                prn = f"{user_id}_{roll_no}"
            
            sem = meta.get('sem', 'UNKNOWN_SEM')
            dept = meta.get('dept', department)
            
            doc_ref = db.collection("results").document(dept).collection(sem).document(prn)
            doc_ref.set({
                "name": meta.get('name', 'UNKNOWN_NAME'),
                "subjects": data['subjects'],
                "summary": data['summary'],
                "last_updated": datetime.now()
            }, merge=True)
            print(f"Success: Processed result for {prn}")
    except Exception as e:
        print(f"Background Process Error: {e}")

@app.route('/submit_result', methods=['POST'])
@login_required
def submit_result():
    student_class = request.form.get('class')
    roll_no = request.form.get('roll_no')
    department = request.form.get('department')
    
    if 'result_pdf' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('dashboard'))
    
    file = request.files['result_pdf']
    if not file or file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('dashboard'))
        
    if file and file.filename and file.filename.endswith('.pdf'):
        filename = secure_filename(f"{current_user.id}_{roll_no}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Save student submission record
        result_data = {
            'user_id': str(current_user.id),
            'student_class': student_class,
            'roll_no': roll_no,
            'department': department,
            'pdf_filename': filename
        }
        db.collection('result_analysis').add(result_data)
        
        # Trigger background extraction for faculty portal
        thread = threading.Thread(target=process_result_background, args=(filepath, str(current_user.id), department, roll_no))
        thread.start()

        flash('Result submitted successfully! It is now being analyzed.', 'success')
    else:
        flash('Expected a PDF file.', 'error')
        
    return redirect(url_for('dashboard'))

@app.route('/submit_mdm', methods=['POST'])
@login_required
def submit_mdm():
    prn_no = request.form.get('prn_no')
    current_department = request.form.get('current_department')
    preference_1 = request.form.get('preference_1')
    preference_2 = request.form.get('preference_2')
    preference_3 = request.form.get('preference_3')
    preference_4 = request.form.get('preference_4') # Might be none for CSE
    
    # Store in DB (Student portal collection)
    mdm_data = {
        'user_id': str(current_user.id),
        'prn_no': prn_no,
        'current_department': current_department,
        'preference_1': preference_1,
        'preference_2': preference_2,
        'preference_3': preference_3,
        'preference_4': preference_4
    }
    db.collection('minor_degree_applications').add(mdm_data)
    
    # Also store in mdm_preferences collection for faculty portal
    mdm_faculty_data = {
        'Name': 'Student', # Optional, could get from user profile
        'PRN': prn_no,
        'Branch': current_department,
        'Total Marks': 0, # Should ideally be calculated or asked
        'PREFERENCE 1': preference_1,
        'PREFERENCE 2': preference_2,
        'PREFERENCE 3': preference_3,
        'PREFERENCE 4': preference_4
    }
    db.collection('mdm_preferences').add(mdm_faculty_data)
    
    flash('Minor Degree Preferences submitted successfully!', 'success')
    return redirect(url_for('dashboard'))

# --- FACULTY ROUTES ---

from functools import wraps

def faculty_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('faculty_logged_in'):
            return redirect(url_for('faculty_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/faculty_login', methods=['GET'])
def faculty_login():
    return render_template('faculty_login.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    if not data:
        return jsonify({"detail": "Invalid request"}), 400
    
    username = data.get('username')
    password = data.get('password')
    
    if username == "admin" and password == "admin":
        session['faculty_logged_in'] = True
        return jsonify({"status": "success", "message": "Login successful"})
    
    return jsonify({"detail": "Invalid credentials"}), 401

@app.route('/faculty_dashboard')
@faculty_required
def faculty_dashboard():
    return render_template('faculty_dashboard.html')

@app.route('/mdm')
@faculty_required
def faculty_mdm():
    return render_template('faculty_mdm.html')

@app.route('/results_view')
@faculty_required
def faculty_results_view():
    return render_template('faculty_results.html')

@app.route('/api/results')
@faculty_required
def api_results():
    """Fetches all processed results from Firestore."""
    try:
        all_results = []
        depts = db.collection('results').stream()
        for dept in depts:
            dept_id = dept.id
            sems = db.collection('results').document(dept_id).collections()
            for sem_col in sems:
                sem_id = sem_col.id
                docs = sem_col.stream()
                for doc in docs:
                    doc_data = doc.to_dict()
                    doc_data['prn'] = doc.id
                    doc_data['dept'] = dept_id
                    doc_data['sem'] = sem_id
                    
                    # Fix timestamp serialization issue
                    if 'last_updated' in doc_data and doc_data['last_updated']:
                         doc_data['last_updated'] = str(doc_data['last_updated'])
                    all_results.append(doc_data)
        
        return jsonify({"status": "success", "data": all_results})
    except Exception as e:
        import traceback
        error_msg = f"Error fetching results: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return jsonify({"detail": "Failed to fetch results"}), 500

@app.route('/api/mdm_preferences')
@faculty_required
def api_mdm_preferences():
    """Fetches MDM preferences from Firestore."""
    try:
        mdm_ref = db.collection('mdm_preferences').stream()
        mdm_data = []
        for doc in mdm_ref:
            data = doc.to_dict()
            if data:
                data['id'] = doc.id
                mdm_data.append(data)
            
        if not mdm_data:
            return jsonify({"status": "success", "data": []})
            
        df = pd.DataFrame(mdm_data)
        allocated_df = seat_allotment(df)
        allocated_data = allocated_df.to_dict(orient='records')
        
        return jsonify({"status": "success", "data": allocated_data})
    except Exception as e:
        print(f"Error fetching MDM preferences: {e}")
        return jsonify({"detail": "Failed to fetch MDM preferences"}), 500

@app.route('/analyze', methods=['POST'])
@faculty_required
def analyze_endpoint():
    """Fallback endpoint for manual analysis"""
    return jsonify({"status": "Processing", "message": "Endpoint preserved, but handled automatically on student upload."})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
