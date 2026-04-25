import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import User, ResultAnalysis, MinorDegreeApplication
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-for-development' # Change in production

if os.environ.get('FIREBASE_CREDENTIALS'):
    # Vercel has a read-only filesystem, so we must use /tmp for uploads
    UPLOAD_FOLDER = '/tmp'
else:
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

import json

# Initialize Firebase Admin SDK
firebase_creds_json = os.environ.get('FIREBASE_CREDENTIALS')
if firebase_creds_json:
    # Running on Vercel
    cred_dict = json.loads(firebase_creds_json)
    cred = credentials.Certificate(cred_dict)
else:
    # Running locally
    cred = credentials.Certificate("student-portal-9f4f6-firebase-adminsdk-fbsvc-614a27b548.json")

firebase_admin.initialize_app(cred)
db = firestore.client(database_id="native-db")
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    user_ref = db.collection('users').document(str(user_id)).get()
    if user_ref.exists:
        return User.from_dict(user_ref.to_dict(), user_ref.id)
    return None

# --- ROUTES ---

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        users_ref = db.collection('users').where('username', '==', username).stream()
        user_doc = None
        for doc in users_ref:
            user_doc = doc
            break
        
        if user_doc:
            user = User.from_dict(user_doc.to_dict(), user_doc.id)
            if check_password_hash(user.password_hash, password):
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                flash('Login failed. Check your username and password.', 'error')
        else:
            flash('Login failed. Check your username and password.', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        users_ref = db.collection('users').where('username', '==', username).stream()
        user_exists = any(True for _ in users_ref)
        
        if user_exists:
            flash('Username already exists.', 'error')
            return redirect(url_for('register'))

        # Create new user document
        user_data = {
            'username': username,
            'password_hash': generate_password_hash(password)
        }
        db.collection('users').add(user_data)

        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Fetch user's existing records
    result_ref = db.collection('result_analysis').where('user_id', '==', str(current_user.id)).stream()
    result_submissions = [ResultAnalysis.from_dict(doc.to_dict(), doc.id) for doc in result_ref]
    
    mdm_ref = db.collection('minor_degree_applications').where('user_id', '==', str(current_user.id)).stream()
    mdm_submissions = [MinorDegreeApplication.from_dict(doc.to_dict(), doc.id) for doc in mdm_ref]
    
    return render_template('dashboard.html', results=result_submissions, mdm=mdm_submissions)

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
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('dashboard'))
        
    if file and file.filename.endswith('.pdf'):
        filename = secure_filename(f"{current_user.id}_{roll_no}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        result_data = {
            'user_id': str(current_user.id),
            'student_class': student_class,
            'roll_no': roll_no,
            'department': department,
            'pdf_filename': filename
        }
        db.collection('result_analysis').add(result_data)
        flash('Result submitted successfully!', 'success')
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
    
    # Store in DB
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
    
    flash('Minor Degree Preferences submitted successfully!', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
