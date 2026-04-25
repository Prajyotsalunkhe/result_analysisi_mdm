import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, User, ResultAnalysis, MinorDegreeApplication

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-for-development' # Change in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__name__)), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Login failed. Check your username and password.', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('Username already exists.', 'error')
            return redirect(url_for('register'))

        new_user = User(username=username, password_hash=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()

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
    result_submissions = ResultAnalysis.query.filter_by(user_id=current_user.id).all()
    mdm_submissions = MinorDegreeApplication.query.filter_by(user_id=current_user.id).all()
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
        
        new_result = ResultAnalysis(
            user_id=current_user.id,
            student_class=student_class,
            roll_no=roll_no,
            department=department,
            pdf_filename=filename
        )
        db.session.add(new_result)
        db.session.commit()
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
    new_mdm = MinorDegreeApplication(
        user_id=current_user.id,
        prn_no=prn_no,
        current_department=current_department,
        preference_1=preference_1,
        preference_2=preference_2,
        preference_3=preference_3,
        preference_4=preference_4
    )
    db.session.add(new_mdm)
    db.session.commit()
    
    flash('Minor Degree Preferences submitted successfully!', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
