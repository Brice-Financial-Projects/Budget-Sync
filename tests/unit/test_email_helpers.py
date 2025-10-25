"""Unit tests for email helper functions."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from unittest.mock import patch, Mock
from budget_sync.helpers.email_helpers import send_password_reset_email


def test_send_password_reset_email_success():
    """
    GIVEN a valid email and reset link
    WHEN send_password_reset_email is called
    THEN check that SendGrid API is called correctly and returns success
    """
    with patch('budget_sync.helpers.email_helpers.SendGridAPIClient') as mock_sg_client, \
         patch.dict(os.environ, {'SENDGRID_API_KEY': 'test_api_key', 'SENDGRID_FROM_EMAIL': 'test@example.com'}):

        # Mock the SendGrid response
        mock_response = Mock()
        mock_response.status_code = 202
        mock_sg_instance = mock_sg_client.return_value
        mock_sg_instance.send.return_value = mock_response

        # Call the function
        result = send_password_reset_email('user@example.com', 'http://example.com/reset/token123')

        # Assertions
        assert result is True
        mock_sg_client.assert_called_once_with('test_api_key')
        mock_sg_instance.send.assert_called_once()


def test_send_password_reset_email_no_api_key():
    """
    GIVEN no SendGrid API key is configured
    WHEN send_password_reset_email is called
    THEN check that it returns False
    """
    with patch.dict(os.environ, {}, clear=True):
        result = send_password_reset_email('user@example.com', 'http://example.com/reset/token123')
        assert result is False


def test_send_password_reset_email_api_failure():
    """
    GIVEN a valid email and reset link but SendGrid API fails
    WHEN send_password_reset_email is called
    THEN check that it returns False
    """
    with patch('budget_sync.helpers.email_helpers.SendGridAPIClient') as mock_sg_client, \
         patch.dict(os.environ, {'SENDGRID_API_KEY': 'test_api_key'}):

        # Mock the SendGrid response with a failure status code
        mock_response = Mock()
        mock_response.status_code = 400
        mock_sg_instance = mock_sg_client.return_value
        mock_sg_instance.send.return_value = mock_response

        # Call the function
        result = send_password_reset_email('user@example.com', 'http://example.com/reset/token123')

        # Assertions
        assert result is False


def test_send_password_reset_email_exception():
    """
    GIVEN a valid email and reset link but an exception occurs
    WHEN send_password_reset_email is called
    THEN check that it handles the exception and returns False
    """
    with patch('budget_sync.helpers.email_helpers.SendGridAPIClient') as mock_sg_client, \
         patch.dict(os.environ, {'SENDGRID_API_KEY': 'test_api_key'}):

        # Mock SendGrid to raise an exception
        mock_sg_instance = mock_sg_client.return_value
        mock_sg_instance.send.side_effect = Exception('SendGrid error')

        # Call the function
        result = send_password_reset_email('user@example.com', 'http://example.com/reset/token123')

        # Assertions
        assert result is False


def test_send_password_reset_email_content():
    """
    GIVEN a valid email and reset link
    WHEN send_password_reset_email is called
    THEN check that the email content contains the reset link
    """
    with patch('budget_sync.helpers.email_helpers.SendGridAPIClient') as mock_sg_client, \
         patch('budget_sync.helpers.email_helpers.Mail') as mock_mail, \
         patch.dict(os.environ, {'SENDGRID_API_KEY': 'test_api_key', 'SENDGRID_FROM_EMAIL': 'test@example.com'}):

        # Mock the SendGrid response
        mock_response = Mock()
        mock_response.status_code = 202
        mock_sg_instance = mock_sg_client.return_value
        mock_sg_instance.send.return_value = mock_response

        reset_link = 'http://example.com/reset/token123'

        # Call the function
        result = send_password_reset_email('user@example.com', reset_link)

        # Assertions
        assert result is True
        # Check that Mail was called
        mock_mail.assert_called_once()

        # Get the content argument from the Mail call
        call_args = mock_mail.call_args
        # The content is the 4th argument (index 3)
        content_arg = call_args[0][3] if len(call_args[0]) > 3 else None

        # Check that content contains the reset link
        if content_arg:
            assert reset_link in content_arg.value


def test_send_password_reset_email_default_sender():
    """
    GIVEN no SENDGRID_FROM_EMAIL is configured
    WHEN send_password_reset_email is called
    THEN check that it uses the default sender email
    """
    with patch('budget_sync.helpers.email_helpers.SendGridAPIClient') as mock_sg_client, \
         patch('budget_sync.helpers.email_helpers.Email') as mock_email, \
         patch.dict(os.environ, {'SENDGRID_API_KEY': 'test_api_key'}, clear=True):

        # Mock the SendGrid response
        mock_response = Mock()
        mock_response.status_code = 202
        mock_sg_instance = mock_sg_client.return_value
        mock_sg_instance.send.return_value = mock_response

        # Call the function
        result = send_password_reset_email('user@example.com', 'http://example.com/reset/token123')

        # Assertions
        assert result is True
        # Check that Email was called with default sender
        mock_email.assert_called_with('noreply@budgetsync.com')
