"""budget_sync/__init__.py."""

import os
import logging
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_session import Session
from flask_debugtoolbar import DebugToolbarExtension
from redis import Redis
from flask_wtf.csrf import CSRFProtect



# Initializations
toolbar = DebugToolbarExtension()
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app():
    # Load environment variables
    load_dotenv()

    env = os.getenv("FLASK_ENV")  
    print(f"🔧 Flask Environment: {env}")
    
    app = Flask(__name__)
    
    if env == "development":
        from .config.settings import DevelopmentConfig
        app.config.from_object(DevelopmentConfig)
        print("🔧 Using Development Configuration")
    elif env == "testing":
        from .config.settings import TestingConfig
        app.config.from_object(TestingConfig)
        print("🔧 Using Testing Configuration")
    else:
        from .config.settings import ProductionConfig
        app.config.from_object(ProductionConfig)
        print("🔧 Using Production Configuration")
        
    # Check if CSRF is enabled
    print(f"🔧 CSRF Protection enabled: {app.config.get('WTF_CSRF_ENABLED', False)}")
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    CORS(app)

    # Debug Toolbar initialization
    if app.config["DEBUG"]:  # Only activate in debug mode
        app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False
        toolbar.init_app(app)

    # Configure session (Use Redis if available, otherwise default to filesystem)
    session_type = app.config.get("SESSION_TYPE", "filesystem")
    if session_type == "redis":
        try:
            app.config["SESSION_REDIS"] = Redis.from_url(app.config.get("REDIS_URL", "redis://localhost:6379/0"))
            print("✅ Redis is connected for session storage.")
        except Exception as e:
            print(f"❌ Redis connection failed, falling back to filesystem: {e}")
            app.config["SESSION_TYPE"] = "filesystem"
    Session(app)

    login_manager.login_view = "auth.login"

    # Import models (ensure all models are loaded for migrations)
    with app.app_context():
        from budget_sync.models import Budget, User, Profile  # noqa: F401

    # Register blueprints
    from budget_sync.budget.routes import budget_bp
    from budget_sync.main.routes import main_bp
    from budget_sync.auth.routes import auth_bp
    from budget_sync.profile.routes import profile_bp
    from budget_sync.weather.routes import weather_bp

    app.register_blueprint(budget_bp, url_prefix="/budget")
    app.register_blueprint(main_bp, url_prefix="/")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(profile_bp)
    app.register_blueprint(weather_bp, url_prefix="/weather")

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Internal server error"}), 500

    with app.app_context():
        db.create_all()  # Create database tables if they don't exist

        # Populate expense categories and templates
        from budget_sync.helpers.budget_helpers import populate_expense_categories
        populate_expense_categories(db)

    return app


@login_manager.user_loader
def load_user(user_id):
    from budget_sync.models import User
    return User.query.get(int(user_id))


def configure_logging(app):
    """Configure logging for the application."""
    if app.debug or app.testing:
        app.logger.setLevel(logging.DEBUG)
    else:
        # Configure a file handler
        file_handler = logging.FileHandler("budget_sync.log")
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
        )
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)

    app.logger.info("App startup")



# --------------------------------------------------------------------
# Re-export models at package level **after** the package is initialized.
# --------------------------------------------------------------------
def __getattr__(name):
    # Import models only when we need to access model classes
    if name in ['User', 'Profile', 'Budget', 'ExpenseCategory', 'ExpenseTemplate', 'BudgetItem', 'GrossIncome',
                'OtherIncome']:
        from budget_sync.models import User, Profile, Budget, ExpenseCategory, ExpenseTemplate, BudgetItem, GrossIncome, \
            OtherIncome
        models_dict = {
            'User': User,
            'Profile': Profile,
            'Budget': Budget,
            'ExpenseCategory': ExpenseCategory,
            'ExpenseTemplate': ExpenseTemplate,
            'BudgetItem': BudgetItem,
            'GrossIncome': GrossIncome,
            'OtherIncome': OtherIncome
        }
        if name in models_dict:
            return models_dict[name]

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
