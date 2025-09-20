"""backend/budget_sync/auth/routes.py"""

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError
from src.budget_sync.auth import auth_bp
from src.budget_sync.auth.forms import LoginForm, RegistrationForm
from src.budget_sync.models import User
from src.budget_sync import db, bcrypt


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            # Create new user (User model hashes the password)
            new_user = User(
                username=form.username.data,
                email=form.email.data,
                password=form.password.data
            )
            db.session.add(new_user)
            db.session.commit()

            flash('Account created successfully. You can now log in.', 'success')
            return redirect(url_for('auth.login'))

        except IntegrityError:
            db.session.rollback()
            flash('An account with this email already exists. Please log in.', 'danger')
            return redirect(url_for('auth.login'))
    
    return render_template('auth/../templates/auth/register.html', form=form)




@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if request.method == "POST" and not form.validate_on_submit():
        print(f"❌ Form validation failed: {form.errors}")

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        # Debugging information
        print(f"DEBUG: Attempting login for email: {form.email.data}")

        if not user:
            print("❌ No user found with this email.")
            flash("No account found with that email.", "danger")
            return redirect(url_for("auth.login"))

        print(f"DEBUG: Found user {user.email}, checking password...")

        # FIXED: Use `password_hash` instead of `password`
        if not bcrypt.check_password_hash(user.password_hash, form.password.data):  
            print("❌ Password mismatch.")
            flash("Incorrect password. Try again.", "danger")
            return redirect(url_for("auth.login"))

        # Successful login
        login_user(user, remember=form.remember_me.data)
        print(f"✅ User {user.email} logged in successfully!")

        flash("Login successful!", "success")
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))

    return render_template('auth/../templates/auth/login.html', form=form)



@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
