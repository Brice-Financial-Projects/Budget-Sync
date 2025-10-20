"""budget_sync/profile/__init__.py"""

from flask import Blueprint

profile_bp = Blueprint('profile', __name__, template_folder='templates')

from budget_sync.profile import routes  # noqa: E402, F401
