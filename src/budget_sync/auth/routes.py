"""backend/budget_sync/auth/routes.py"""

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError
from budget_sync.auth import auth_bp
from budget_sync.auth.forms import LoginForm, RegistrationForm, ForgotPasswordForm, ResetPasswordForm
from budget_sync.models import User, PasswordResetToken
from budget_sync import db, bcrypt
from budget_sync.helpers.email_helpers import send_password_reset_email


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
    
    return render_template('auth/register.html', form=form)




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

    return render_template('auth/login.html', form=form)



@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        # Always show success message to prevent email enumeration
        flash('If an account exists with that email, a password reset link has been sent.', 'info')

        if user:
            # Create password reset token
            reset_token = PasswordResetToken(user_id=user.id, expiration_hours=1)
            db.session.add(reset_token)
            db.session.commit()

            # Generate reset link
            reset_link = url_for('auth.reset_password', token=reset_token.token, _external=True)

            # Send email
            email_sent = send_password_reset_email(user.email, reset_link)

            if email_sent:
                print(f"✅ Password reset email sent to {user.email}")
            else:
                print(f"❌ Failed to send password reset email to {user.email}")

        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html', form=form)


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    # Find the token
    reset_token = PasswordResetToken.query.filter_by(token=token).first()

    if not reset_token:
        flash('Invalid or expired reset link.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if reset_token.used:
        flash('This reset link has already been used.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if reset_token.is_expired():
        flash('This reset link has expired. Please request a new one.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        # Update user password
        user = User.query.get(reset_token.user_id)
        user.password_hash = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

        # Mark token as used
        reset_token.used = True

        db.session.commit()

        flash('Your password has been reset successfully. You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', form=form, token=token)
