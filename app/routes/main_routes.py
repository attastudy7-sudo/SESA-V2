from flask import Blueprint, render_template, g, session, redirect, url_for, request, flash, jsonify, current_app
from app import db
from app.models import Accounts, TestResult, Question, School
from app.utils.decorators import login_required
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import or_
import pandas as pd
import os
from collections import Counter
from datetime import datetime
from flask import g, session, redirect, url_for, flash, render_template


main_bp = Blueprint("main", __name__, url_prefix="/")

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

# -------------------------------
# Load logged-in user
# -------------------------------
@main_bp.before_request
def load_logged_in_user():
    # Load logged-in student or school
    g.user = Accounts.query.get(session.get("user_id")) if session.get("user_id") else None
    g.school = School.query.get(session.get("school_id")) if session.get("school_id") else None

    if g.school and not g.school.upload_enabled:
        flash("This school account is disabled. Contact FOPA DILLIGENT CONSULT.", "error")

    # Public endpoints that don't require login
    public_endpoints = {
        'auth.login', 'auth.signup', 'auth.school_signup', 'auth.school_login',
        'main.landing', 'main.landing_page', 'static'
    }

    # Only redirect if accessing a protected endpoint
    if request.endpoint and request.endpoint not in public_endpoints:
        if not g.user and not g.school:
            # If a school is trying to access, redirect to school login
            return redirect(url_for('auth.login'))

# -------------------------------
# Landing page
# -------------------------------
@main_bp.route("/")
def landing():
    return render_template("landing.html")

# -------------------------------
# Student home
# -------------------------------
@main_bp.route("/home")
@login_required
def home():
    user = g.user
    test_results = user.test_results
    total_tests = len(test_results)
    most_recent = max(test_results, key=lambda tr: tr.taken_at) if total_tests else None

    def count_questions(test_type):
        return Question.query.filter_by(test_type=test_type).count()

    return render_template(
        "home.html",
        fname=user.fname,
        lname=user.lname,
        level=user.level,
        last_login=user.last_login,
        total_users=Accounts.query.count(),
        total_tests=total_tests,
        avg_score=round(sum([tr.score for tr in test_results])/total_tests, 2) if total_tests else 0,
        most_recent=most_recent,
        sad_question_count=count_questions("Separation Anxiety Disorder"),
        sp_question_count=count_questions("Social Phobia"),
        gad_question_count=count_questions("Generalised Anxiety Disorder"),
        pd_question_count=count_questions("Panic Disorder"),
        ocd_question_count=count_questions("Obsessive Compulsive Disorder"),
        mdd_question_count=count_questions("Major Depressive Disorder")
    )

# -------------------------------
# Super-admin dashboard
# -------------------------------
from sqlalchemy import func

@main_bp.route('/admin')
@login_required
def admin_dashboard():
    if g.user.id != 1:
        return render_template("404.html")

    total_stage_results = TestResult.query.count()  # total of all stages (all results)

    # Count results grouped by stage
    stage_counts = (
        db.session.query(TestResult.details, func.count(TestResult.id))
        .group_by(TestResult.details)
        .all()
    )
    # Convert to dictionary: {"Clinical": 12, "Normal": 34, ...}
    stage_counts_dict = {stage: count for stage, count in stage_counts}

    return render_template(
        'admin_dashboard.html',
        results=TestResult.query.order_by(TestResult.taken_at.desc()).all(),
        accounts=Accounts.query.all(),
        total_tests=TestResult.query.count(),
        total_users=Accounts.query.count(),
        total_schools=School.query.count(),
        total_stage_results=total_stage_results,  # optional if needed
        stage_counts=stage_counts_dict,  # new variable
        school=School.query.order_by(School.school_name).all(),
        questions=Question.query.order_by(Question.test_type).all()
    )


# -------------------------------
# School dashboard
# -------------------------------
@main_bp.route("/school/<int:school_id>")
@login_required
def school_dashboard(school_id):
    # Super-admin can view any school
    if g.user and g.user.id == 1:
        school = School.query.get_or_404(school_id)
    # School admin can only view their own dashboard
    elif g.school.id == school_id:
        school = g.school
    else:
        flash("Not authorized to view this school dashboard.", "danger")
        return redirect(url_for('auth.school_login'))

    # Fetch all students in the school
    accounts = Accounts.query.filter_by(school_id=school.id).all()

    # Fetch all test results for students in the school
    results = TestResult.query.join(Accounts)\
        .filter(Accounts.school_id == school.id)\
        .order_by(TestResult.taken_at.desc()).all()

    # Count stages for current month
    now = datetime.utcnow()
    stage_counter = Counter(
        (result.details or "Unknown").strip().title()
        for result in results
        if result.taken_at and result.taken_at.month == now.month and result.taken_at.year == now.year
    )

    # Upload access
    upload_enabled = bool(school.upload_enabled)

    return render_template(
        "school_dashboard.html",
        school=school,
        accounts=accounts,
        results=results,
        stage_counts=stage_counter,
        upload_enabled=upload_enabled,
        now=now
    )

# -------------------------------
# Upload & create student accounts
# -------------------------------

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    """Check if uploaded file has an allowed Excel extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

from werkzeug.security import generate_password_hash
from app.models import db, Accounts, School
import pandas as pd
import os
from datetime import datetime
from flask import request, redirect, flash, session
from app.utils.decorators import login_required

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main_bp.route('/toggle_upload/<int:school_id>', methods=['POST'])
@login_required
def toggle_upload(school_id):
    if g.user.id != 1:
        return render_template("404.html")
    
    school = School.query.get_or_404(school_id)
    school.upload_enabled = not school.upload_enabled
    db.session.commit()
    flash(f"Upload access for {school.school_name} is now {'enabled' if school.upload_enabled else 'disabled'}.", "success")
    return redirect(url_for('main.admin_dashboard'))


@main_bp.route('/upload_students', methods=['POST'])
@login_required
def upload_students():
    school = School.query.filter_by(id=session.get('school_id')).first()
    
    # Check if upload is enabled for this school
    if not school.upload_enabled:
        flash("Upload not enabled. Please wait for admin approval after payment.", "danger")
        return redirect(request.referrer)

    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(request.referrer)

    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(request.referrer)

    if not allowed_file(file.filename):
        flash('Invalid file type. Please upload an Excel file.', 'danger')
        return redirect(request.referrer)

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    try:
        df = pd.read_excel(filepath)
        df.columns = [col.strip().lower() for col in df.columns]

        required_columns = ['first name', 'last name', 'email', 'username', 'password', 'birthdate', 'gender', 'level']
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            flash(f"Missing required columns: {', '.join(missing)}", "danger")
            return redirect(request.referrer)

        allowed_levels = ['primaryschool', 'middleschool', 'highschool']
        created_count = 0
        skipped_invalid_level = 0

        for _, row in df.iterrows():
            level_value = str(row['level']).strip().lower()
            if level_value not in allowed_levels:
                skipped_invalid_level += 1
                continue

            # Skip if user already exists
            if Accounts.query.filter_by(email=row['email']).first():
                continue

            birthdate_value = None
            if not pd.isna(row['birthdate']):
                try:
                    birthdate_value = pd.to_datetime(row['birthdate']).date()
                except Exception:
                    pass

            account = Accounts(
                fname=row['first name'],
                lname=row['last name'],
                email=row['email'],
                username=row['username'],
                password=generate_password_hash(str(row['password'])),
                level=level_value,
                gender=row.get('gender', ''),
                birthdate=birthdate_value,
                school_id=school.id
            )

            db.session.add(account)
            created_count += 1

        db.session.commit()

        message = f"Created {created_count} student accounts for {school.school_name}."
        if skipped_invalid_level:
            message += f" ⚠️ Skipped {skipped_invalid_level} rows with invalid level values."
        flash(message, "success")

    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {e}", "danger")

    return redirect(request.referrer)

# -------------------------------
# Edit, delete accounts
# -------------------------------
@main_bp.route("/edit_account/<int:account_id>", methods=["GET", "POST"])
@login_required
def edit_account(account_id):
    account = Accounts.query.get_or_404(account_id)
    if request.method == "POST":
        account.fname = request.form.get("fname")
        account.lname = request.form.get("lname")
        account.email = request.form.get("email")
        db.session.commit()
        flash("Account updated successfully!", "success")
        return redirect(url_for("main.admin_dashboard"))
    return render_template("edit_account.html", account=account)

@main_bp.route("/delete_account/<int:account_id>", methods=["POST"])
@login_required
def delete_account(account_id):
    if not g.user or g.user.id != 1:
        flash("Not authorized.", "danger")
        return redirect(url_for("main.admin_dashboard"))
    account = Accounts.query.get_or_404(account_id)
    db.session.delete(account)
    db.session.commit()
    flash(f"Account {account.username} deleted successfully.", "success")
    return redirect(url_for("main.admin_dashboard"))

# -------------------------------
# Edit, delete schools
# -------------------------------
@main_bp.route("/edit_school/<int:school_id>", methods=["GET", "POST"])
@login_required
def edit_school(school_id):
    if not g.user or g.user.id != 1:
        flash("Not authorized to edit schools.", "danger")
        return redirect(url_for("main.admin_dashboard"))
    school = School.query.get_or_404(school_id)
    if request.method == "POST":
        school.school_name = request.form.get("school_name")
        school.email = request.form.get("email")
        school.admin_name = request.form.get("admin_name")
        school.admin_password = generate_password_hash(request.form.get("admin_password"))
        db.session.commit()
        flash("School updated successfully.", "success")
        return redirect(url_for("main.admin_dashboard"))
    return render_template("edit_school.html", school=school)

@main_bp.route("/delete_school/<int:school_id>", methods=["POST"])
@login_required
def delete_school(school_id):
    if not g.user or g.user.id != 1:
        flash("Not authorized.", "danger")
        return redirect(url_for("main.admin_dashboard"))
    school = School.query.get_or_404(school_id)
    db.session.delete(school)
    db.session.commit()
    flash(f"School '{school.school_name}' deleted successfully.", "success")
    return redirect(url_for("main.admin_dashboard"))

# -------------------------------
# Add, edit, delete questions
# -------------------------------
@main_bp.route("/add_question", methods=["GET", "POST"])
@login_required
def add_question():
    if not g.user or g.user.id != 1:
        flash("Not authorized.", "danger")
        return redirect(url_for("main.admin_dashboard"))
    if request.method == "POST":
        test_type = request.form.get("test_type")
        question_content = request.form.get("question_content")
        if not test_type or not question_content:
            flash("Please fill in all fields.", "danger")
            return redirect(url_for("main.add_question"))
        db.session.add(Question(test_type=test_type, question_content=question_content))
        db.session.commit()
        flash("Question added successfully!", "success")
        return redirect(url_for("main.admin_dashboard"))
    return render_template("add_question.html")

@main_bp.route("/edit_question/<int:id>", methods=["GET", "POST"])
@login_required
def edit_question(id):
    if not g.user or g.user.id != 1:
        flash("Not authorized.", "danger")
        return redirect(url_for("main.admin_dashboard"))
    question = Question.query.get_or_404(id)
    if request.method == "POST":
        question.test_type = request.form.get("test_type")
        question.question_content = request.form.get("question_content")
        db.session.commit()
        flash("Question updated successfully!", "success")
        return redirect(url_for("main.admin_dashboard"))
    return render_template("edit_question.html", question=question)

@main_bp.route("/delete_question/<int:id>", methods=["POST"])
@login_required
def delete_question(id):
    if not g.user or g.user.id != 1:
        flash("Not authorized.", "danger")
        return redirect(url_for("main.admin_dashboard"))
    question = Question.query.get_or_404(id)
    db.session.delete(question)
    db.session.commit()
    flash("Question deleted successfully!", "success")
    return redirect(url_for("main.admin_dashboard"))

# -------------------------------
# AJAX search students
# -------------------------------
@main_bp.route("/school/<int:school_id>/search_students")
@login_required
def search_students(school_id):
    query = request.args.get('query', '').strip()
    if not query:
        return jsonify([])
    if session.get('school_id') != school_id and (not g.user or g.user.id != 1):
        return jsonify([])
    q = "%{}%".format(query.lower())
    students = Accounts.query.filter(
        Accounts.school_id == school_id,
        or_(
            Accounts.fname.ilike(q),
            Accounts.lname.ilike(q),
            Accounts.username.ilike(q),
            Accounts.email.ilike(q)
        )
    ).limit(20).all()
    return jsonify([{"id": s.id, "fname": s.fname, "lname": s.lname, "username": s.username} for s in students])
