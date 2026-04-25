from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

class ResultAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    student_class = db.Column(db.String(50), nullable=False)
    roll_no = db.Column(db.String(50), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    pdf_filename = db.Column(db.String(255), nullable=False)

class MinorDegreeApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    prn_no = db.Column(db.String(50), nullable=False)
    current_department = db.Column(db.String(100), nullable=False)
    preference_1 = db.Column(db.String(100), nullable=False)
    preference_2 = db.Column(db.String(100), nullable=False)
    preference_3 = db.Column(db.String(100), nullable=False)
    preference_4 = db.Column(db.String(100), nullable=True)  # Nullable because CSE/AIML won't have it
