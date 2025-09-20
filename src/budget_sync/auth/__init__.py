"""backend/budget_sync/auth/__init__.py"""

from flask import Blueprint

auth_bp = Blueprint('auth', __name__, template_folder='templates')

from src.budget_sync.auth import routes