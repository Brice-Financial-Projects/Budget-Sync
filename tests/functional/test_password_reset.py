"""Functional tests for password reset functionality."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from unittest.mock import patch
from datetime import datetime, timedelta
from budget_sync import db
from budget_sync.models import User, PasswordResetToken


def test_forgot_password_page_loads(client):
    """
    GIVEN a Flask application
    WHEN the '/auth/forgot-password' page is requested (GET)
    THEN check that the response is valid and the page loads
    """
    response = client.get('/auth/forgot-password')
    assert response.status_code == 200
    assert b'Forgot Password' in response.data
    assert b'email' in response.data


def test_forgot_password_with_valid_email(client, test_user):
    """
    GIVEN a registered user
    WHEN submitting forgot password form with valid email
    THEN check that a reset token is created and email is sent
    """
    with patch('budget_sync.auth.routes.send_password_reset_email') as mock_send_email:
        mock_send_email.return_value = True

        response = client.post('/auth/forgot-password', data={
            'email': 'test@example.com'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'If an account exists with that email' in response.data

        # Check that a token was created
        token = PasswordResetToken.query.filter_by(user_id=test_user.id).first()
        assert token is not None
        assert not token.used
        assert not token.is_expired()

        # Check that email function was called
        mock_send_email.assert_called_once()


def test_forgot_password_with_nonexistent_email(client):
    """
    GIVEN a Flask application
    WHEN submitting forgot password form with non-existent email
    THEN check that the same success message is shown (to prevent email enumeration)
    """
    with patch('budget_sync.auth.routes.send_password_reset_email') as mock_send_email:
        response = client.post('/auth/forgot-password', data={
            'email': 'nonexistent@example.com'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'If an account exists with that email' in response.data

        # Check that no token was created
        token = PasswordResetToken.query.first()
        assert token is None

        # Check that email function was NOT called
        mock_send_email.assert_not_called()


def test_forgot_password_with_invalid_email_format(client):
    """
    GIVEN a Flask application
    WHEN submitting forgot password form with invalid email format
    THEN check that validation error is shown
    """
    response = client.post('/auth/forgot-password', data={
        'email': 'invalid-email'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Forgot Password' in response.data


def test_forgot_password_when_authenticated(auth_client):
    """
    GIVEN an authenticated user
    WHEN trying to access forgot password page
    THEN check that user is redirected to dashboard
    """
    response = auth_client.get('/auth/forgot-password', follow_redirects=True)
    assert response.status_code == 200
    # Should be redirected to dashboard


def test_reset_password_page_with_valid_token(client, test_user, app):
    """
    GIVEN a valid password reset token
    WHEN the reset password page is requested
    THEN check that the page loads correctly
    """
    with app.app_context():
        # Create a reset token
        reset_token = PasswordResetToken(user_id=test_user.id, expiration_hours=1)
        db.session.add(reset_token)
        db.session.commit()
        token_value = reset_token.token

        response = client.get(f'/auth/reset-password/{token_value}')
        assert response.status_code == 200
        assert b'Reset Password' in response.data
        assert b'New Password' in response.data


def test_reset_password_with_invalid_token(client):
    """
    GIVEN an invalid token
    WHEN the reset password page is requested
    THEN check that user is redirected with error message
    """
    response = client.get('/auth/reset-password/invalid_token', follow_redirects=True)
    assert response.status_code == 200
    assert b'Invalid or expired reset link' in response.data


def test_reset_password_with_expired_token(client, test_user, app):
    """
    GIVEN an expired password reset token
    WHEN the reset password page is requested
    THEN check that user is redirected with error message
    """
    with app.app_context():
        # Create an expired token
        reset_token = PasswordResetToken(user_id=test_user.id, expiration_hours=1)
        reset_token.expires_at = datetime.utcnow() - timedelta(hours=1)
        db.session.add(reset_token)
        db.session.commit()
        token_value = reset_token.token

        response = client.get(f'/auth/reset-password/{token_value}', follow_redirects=True)
        assert response.status_code == 200
        assert b'expired' in response.data.lower()


def test_reset_password_with_used_token(client, test_user, app):
    """
    GIVEN a used password reset token
    WHEN the reset password page is requested
    THEN check that user is redirected with error message
    """
    with app.app_context():
        # Create a used token
        reset_token = PasswordResetToken(user_id=test_user.id, expiration_hours=1)
        reset_token.used = True
        db.session.add(reset_token)
        db.session.commit()
        token_value = reset_token.token

        response = client.get(f'/auth/reset-password/{token_value}', follow_redirects=True)
        assert response.status_code == 200
        assert b'already been used' in response.data


def test_reset_password_successful(client, test_user, app):
    """
    GIVEN a valid password reset token
    WHEN submitting new password
    THEN check that password is updated and token is marked as used
    """
    with app.app_context():
        # Create a reset token
        reset_token = PasswordResetToken(user_id=test_user.id, expiration_hours=1)
        db.session.add(reset_token)
        db.session.commit()
        token_value = reset_token.token
        user_id = test_user.id

        new_password = 'NewPassword@123456789'

        response = client.post(f'/auth/reset-password/{token_value}', data={
            'password': new_password,
            'confirm_password': new_password
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'password has been reset successfully' in response.data

        # Check that password was updated
        user = User.query.get(user_id)
        assert user.check_password(new_password)

        # Check that old password no longer works
        assert not user.check_password('Password@123456789')

        # Check that token is marked as used
        token = PasswordResetToken.query.filter_by(token=token_value).first()
        assert token.used


def test_reset_password_with_weak_password(client, test_user, app):
    """
    GIVEN a valid password reset token
    WHEN submitting a weak password
    THEN check that validation error is shown
    """
    with app.app_context():
        # Create a reset token
        reset_token = PasswordResetToken(user_id=test_user.id, expiration_hours=1)
        db.session.add(reset_token)
        db.session.commit()
        token_value = reset_token.token

        response = client.post(f'/auth/reset-password/{token_value}', data={
            'password': 'weak',
            'confirm_password': 'weak'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Reset Password' in response.data


def test_reset_password_with_mismatched_passwords(client, test_user, app):
    """
    GIVEN a valid password reset token
    WHEN submitting mismatched passwords
    THEN check that validation error is shown
    """
    with app.app_context():
        # Create a reset token
        reset_token = PasswordResetToken(user_id=test_user.id, expiration_hours=1)
        db.session.add(reset_token)
        db.session.commit()
        token_value = reset_token.token

        response = client.post(f'/auth/reset-password/{token_value}', data={
            'password': 'NewPassword@123456789',
            'confirm_password': 'DifferentPassword@123456789'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Reset Password' in response.data


def test_reset_password_when_authenticated(auth_client, test_user, app):
    """
    GIVEN an authenticated user
    WHEN trying to access reset password page
    THEN check that user is redirected to dashboard
    """
    with app.app_context():
        # Create a reset token
        reset_token = PasswordResetToken(user_id=test_user.id, expiration_hours=1)
        db.session.add(reset_token)
        db.session.commit()
        token_value = reset_token.token

        response = auth_client.get(f'/auth/reset-password/{token_value}', follow_redirects=True)
        assert response.status_code == 200
        # Should be redirected to dashboard


def test_multiple_password_reset_requests(client, test_user, app):
    """
    GIVEN a user who requests password reset multiple times
    WHEN multiple tokens are created
    THEN check that each token is unique and valid
    """
    with patch('budget_sync.auth.routes.send_password_reset_email') as mock_send_email:
        mock_send_email.return_value = True

        # First request
        client.post('/auth/forgot-password', data={
            'email': 'test@example.com'
        }, follow_redirects=True)

        # Second request
        client.post('/auth/forgot-password', data={
            'email': 'test@example.com'
        }, follow_redirects=True)

        # Check that two tokens were created
        with app.app_context():
            tokens = PasswordResetToken.query.filter_by(user_id=test_user.id).all()
            assert len(tokens) == 2
            assert tokens[0].token != tokens[1].token


def test_password_reset_token_cleanup(client, test_user, app):
    """
    GIVEN an expired or used token
    WHEN attempting to use it
    THEN check that it cannot be used
    """
    with app.app_context():
        # Create an expired token
        expired_token = PasswordResetToken(user_id=test_user.id, expiration_hours=1)
        expired_token.expires_at = datetime.utcnow() - timedelta(hours=2)
        db.session.add(expired_token)

        # Create a used token
        used_token = PasswordResetToken(user_id=test_user.id, expiration_hours=1)
        used_token.used = True
        db.session.add(used_token)

        db.session.commit()

        expired_token_value = expired_token.token
        used_token_value = used_token.token

        # Try to use expired token
        response = client.get(f'/auth/reset-password/{expired_token_value}', follow_redirects=True)
        assert b'expired' in response.data.lower()

        # Try to use used token
        response = client.get(f'/auth/reset-password/{used_token_value}', follow_redirects=True)
        assert b'already been used' in response.data
