from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import click
from flask.cli import with_appcontext
import pandas as pd
from flask_login import LoginManager

# Create instances first
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key_here'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sesa.db'

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"  # name of your login route
    login_manager.login_message_category = "info"

    # Import models AFTER db is initialized
    from . import models
    from .models import Accounts  # Needed for user_loader

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return Accounts.query.get(int(user_id))

    # Register blueprints
    from app.routes.auth_routes import auth_bp as auth_blueprint
    from app.routes.main_routes import main_bp as main_blueprint
    from app.routes.test_routes import test_bp as test_blueprint

    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(test_blueprint)

    # Register CLI commands
    app.cli.add_command(import_students)

    return app

# CLI Command
@click.command('import-students')
@click.argument('school_id')
@click.argument('excel_path')
@with_appcontext
def import_students(school_id, excel_path):
    """Import student accounts from an Excel file."""
    from app.models import Accounts  # Import here to avoid circular imports
    try:
        df = pd.read_excel(excel_path, engine='openpyxl')

        # Expected columns
        expected = {'fname', 'lname', 'email', 'username', 'password', 'level', 'gender', 'birthdate'}
        missing = expected - set(df.columns)
        if missing:
            click.echo(f"Missing required columns: {missing}")
            return

        count = 0
        for _, row in df.iterrows():
            acc = Accounts(
                fname=row['fname'],
                lname=row['lname'],
                email=row['email'],
                username=row['username'],
                password=row['password'],  # Consider hashing
                level=row['level'],
                gender=row['gender'],
                birthdate=row['birthdate'],
                school_id=school_id
            )
            db.session.add(acc)
            count += 1
        db.session.commit()
        click.echo(f"✅ Successfully imported {count} students for school {school_id}!")

    except Exception as e:
        click.echo(f"❌ Error: {e}")
