"""budget_sync/helpers/email_helpers.py"""

import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content


def send_password_reset_email(user_email, reset_link):
    """
    Send a password reset email using SendGrid.

    Args:
        user_email (str): The recipient's email address
        reset_link (str): The password reset link

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
    sender_email = os.getenv('SENDGRID_FROM_EMAIL', 'noreply@budgetsync.com')

    if not sendgrid_api_key:
        print("ERROR: SENDGRID_API_KEY environment variable not set")
        return False

    try:
        from_email = Email(sender_email)
        to_email = To(user_email)
        subject = "Password Reset Request - Budget Sync"

        # HTML content for the email
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #007bff;
                    color: #ffffff !important;
                    text-decoration: none;
                    border-radius: 4px;
                    margin: 20px 0;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    font-size: 12px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Password Reset Request</h2>
                <p>Hello,</p>
                <p>We received a request to reset your password for your Budget Sync account.</p>
                <p>Click the button below to reset your password:</p>
                <a href="{reset_link}" class="button">Reset Password</a>
                <p>Or copy and paste this link into your browser:</p>
                <p><a href="{reset_link}">{reset_link}</a></p>
                <p><strong>This link will expire in 1 hour.</strong></p>
                <p>If you did not request a password reset, please ignore this email and your password will remain unchanged.</p>
                <div class="footer">
                    <p>This is an automated message from Budget Sync. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        content = Content("text/html", html_content)
        mail = Mail(from_email, to_email, subject, content)

        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(mail)

        if response.status_code in [200, 201, 202]:
            print(f"✅ Password reset email sent successfully to {user_email}")
            return True
        else:
            print(f"❌ Failed to send email. Status code: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error sending password reset email: {str(e)}")
        return False
