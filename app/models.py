from datetime import datetime
from app import db  # <- use the db instance from __init__.py
from flask_login import UserMixin
from datetime import datetime
from app import db

class School(db.Model):
    __tablename__ = 'school'

    id = db.Column(db.Integer, primary_key=True)
    school_name = db.Column(db.String(200), nullable=False)
    admin_name = db.Column(db.String(100), nullable=False)
    admin_password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    subscription_paid = db.Column(db.Boolean, default=False)  # True if payment is confirmed
    upload_enabled = db.Column(db.Boolean, default=False)  

    accounts = db.relationship(
        'Accounts',
        backref='school',
        lazy=True,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<School {self.school_name}>"

class Accounts(UserMixin, db.Model):
    __tablename__ = 'accounts'

    id = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(100), nullable=False)
    lname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    level = db.Column(db.String(50))
    gender = db.Column(db.String(20))
    birthdate = db.Column(db.Date)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    school_id = db.Column(
        db.Integer,
        db.ForeignKey('school.id', ondelete='CASCADE', name='fk_accounts_school_id'),
        nullable=True
    )

    test_results = db.relationship('TestResult', backref='account', lazy=True, cascade="all, delete-orphan")


    def __repr__(self):
        return f"<Account {self.username}>"

class TestResult(db.Model):
    __tablename__ = "test_results"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("accounts.id"), nullable=False)
    test_type = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    max_score = db.Column(db.Integer, nullable=True)
    feedback = db.Column(db.Text, nullable=True)  # ✅ NEW FIELD
    details = db.Column(db.Text, nullable=True)
    taken_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<TestResult User:{self.user_id} Test:{self.test_type} Score:{self.score}>"
        
class Question(db.Model):
    __tablename__ = 'question'

    id = db.Column(db.Integer, primary_key=True)
    test_type = db.Column(db.String(100), nullable=False)
    question_content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Question {self.id} - {self.test_type}>"