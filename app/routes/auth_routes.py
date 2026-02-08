# app/routes/auth_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from app.models import School, Accounts
from app import db
from werkzeug.security import generate_password_hash
from flask import session, redirect, url_for, request, flash, render_template
from werkzeug.security import check_password_hash
from app.models import School
from collections import Counter
from datetime import datetime
from flask import g, session, redirect, url_for, flash, render_template


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# -------------------------------
# Landing Page
# -------------------------------
@auth_bp.route("/landing_page")
def landing_page():
    return render_template("landing_page.html")


# -------------------------------
# User Signup
# -------------------------------
@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        fname = request.form.get("fname")
        lname = request.form.get("lname")
        email = request.form.get("email")
        username = request.form.get("username")
        gender = request.form.get("gender")
        birthdate_str = request.form.get("birthdate")
        password = request.form.get("password")
        level = request.form.get("level")

        # Validate inputs
        if Accounts.query.filter_by(email=email).first():
            flash("Email already registered.", "error")
            return redirect(url_for("auth.signup"))
        if Accounts.query.filter_by(username=username).first():
            flash("Username already taken.", "error")
            return redirect(url_for("auth.signup"))
        if len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
            return redirect(url_for("auth.signup"))

        birthdate = datetime.strptime(birthdate_str, "%Y-%m-%d").date()
        hashed_password = generate_password_hash(password)

        new_account = Accounts(
            fname=fname,
            lname=lname,
            email=email,
            username=username,
            gender=gender,
            birthdate=birthdate,
            password=hashed_password,
            level=level
        )

        try:
            db.session.add(new_account)
            db.session.commit()
            flash("Account created successfully.", "success")
            return redirect(url_for("auth.login"))
        except Exception as e:
            db.session.rollback()
            return f"Error creating account: {e}"

    return render_template("signup.html")




# -------------------------------
# School Signup
# -------------------------------
@auth_bp.route("/school_signup", methods=["GET", "POST"])
def school_signup():
    if request.method == "POST":
        school_name = request.form.get("school_name")
        admin_name = request.form.get("admin_name")
        password = request.form.get("admin_password")
        email = request.form.get("email")

        if len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
            return redirect(url_for("auth.school_signup"))
        if School.query.filter_by(school_name=school_name).first():
            flash("School already registered.", "error")
            return redirect(url_for("auth.school_signup"))

        hashed_password = generate_password_hash(password)
        new_school = School(
            school_name=school_name,
            admin_name=admin_name,
            admin_password=hashed_password,
            email=email
        )

        try:
            db.session.add(new_school)
            db.session.commit()
            flash("School registered successfully.", "success")
            return redirect(url_for("auth.school_login"))
        except Exception as e:
            db.session.rollback()
            flash("Error registering school.", "error")
            return redirect(url_for("auth.school_signup"))

    return render_template("school_signup.html")




@auth_bp.route("/school_login", methods=["GET", "POST"])
def school_login():
    if request.method == "POST":
        admin_name = request.form.get("admin_name", "").strip()
        password = request.form.get("password", "").strip()

        if not admin_name or not password:
            flash("Please enter both admin name and password.", "error")
            return redirect(url_for("auth.school_login"))

        school = School.query.filter_by(admin_name=admin_name).first()

        if school and check_password_hash(school.admin_password, password):
            # Log the school in
            session.clear()  # remove previous session data
            session["school_id"] = school.id
            session["user_id"] = None  # ensure g.user is None for school login
            flash("Logged in successfully as school admin.", "success")
            return redirect(url_for("main.school_dashboard", school_id=school.id))
        else:
            flash("Invalid school admin name or password.", "error")
            return redirect(url_for("auth.school_login"))

    return render_template("school_login.html")

# -------------------------------
# Login
# -------------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = Accounts.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            user.last_login = datetime.utcnow()
            db.session.commit()

            # Super admin check
            if user.id == 1:
                return redirect(url_for("main.admin_dashboard"))
            else:
                return redirect(url_for("main.home", fname=user.fname, lname=user.lname))
        else:
            flash("Invalid username or password.", "error")
            return redirect(url_for("auth.login"))

    return render_template("login.html")


# -------------------------------
# Logout
# -------------------------------
@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("auth.login"))
