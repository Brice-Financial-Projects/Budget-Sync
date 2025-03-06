"""backend/app/main/routes.py"""

from flask import Blueprint, render_template
from flask_login import login_required, current_user

main_bp = Blueprint('main', __name__, template_folder='templates')

@main_bp.route('/')
def home():
    return render_template('home.html')  # Landing page with app descriptions and links

@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Fetch all budgets associated with the current user
    budgets = current_user.budgets
    return render_template('main/dashboard.html', budgets=budgets)  # Correct path for your template
