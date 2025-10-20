You are modifying a Flask app (Budget app) with Blueprints, Flask-Login, Flask-Bcrypt, SQLAlchemy, and a config at `backend/app/config/settings.py`. Implement a production-ready password reset flow that supports BOTH HTML form routes and JSON API routes. Use SendGrid for email when configured; otherwise fall back to logging the reset link. Use `itsdangerous.URLSafeTimedSerializer` for time-limited tokens. Keep the UX/email-enumeration safe (return the same response whether the email exists or not).

## Context / Existing Stack
- Auth blueprint: `auth_bp` with URL prefix `/auth`.
- User model: `User` (SQLAlchemy). Fields available: at least `id`, `email` (unique), `password_hash`.
- Password hashing: `Flask-Bcrypt`.
- Sessions: Flask-Login `login_user`, `logout_user`; not relevant for reset.
- Config module: `backend/app/config/settings.py` (DevelopmentConfig / ProductionConfig etc.).
- Templates live under `templates/`.
- Logging already configured; use it.

## Goals
1) Add **HTML** routes and forms:
   - GET `/auth/forgot-password` → simple form (email)
   - POST `/auth/forgot-password` → always show generic success message, send reset email if account exists
   - GET `/auth/reset-password/<token>` → form with new password + confirm
   - POST `/auth/reset-password/<token>` → validate token, update password, flash success, redirect to login

2) Add **JSON API** equivalents (no CSRF, return JSON):
   - `POST /api/auth/forgot-password` with body `{"email": "..."}` → 200 with generic success JSON
   - `POST /api/auth/reset-password` with body `{"token": "...", "password": "...", "password_confirm": "..."}` → 200 on success, 400/401 on errors (do NOT reveal if email exists in the forgot endpoint)

3) Email delivery:
   - Use SendGrid if `SENDGRID_API_KEY` and `MAIL_DEFAULT_SENDER` (or `MAIL_FROM`) are set.
   - Subject: `Reset your Budget App password`
   - Body: include a full absolute link generated via `url_for(..., _external=True)`. If app doesn’t have `SERVER_NAME`, build with `request.url_root`.
   - If SendGrid is not configured, log the link at INFO level and continue (so dev can test flows).

4) Security:
   - Use `itsdangerous.URLSafeTimedSerializer` with:
     - secret key: `app.config["SECRET_KEY"]`
     - salt: `"password-reset-salt"`
     - `max_age` default: 3600 seconds (1 hour)
   - Token payload should be minimal (e.g., `{"uid": user.id, "ver": user.password_hash[:20]}`) so tokens auto-invalidate if the password changes (because `ver` changes).
   - Return identical response for unknown emails on forgot password.
   - Rate-limit (lightweight, optional): basic in-memory cooldown by IP/email to 1 request / 60 seconds in dev; leave TODO/hook for production limiter.
   - Validate password strength minimally (length ≥ 8); leave TODO for stronger checks.

5) Developer UX:
   - Clear logging messages for send attempts and token load errors.
   - Templated emails: both **HTML** and **plain text** versions.
   - Minimal Jinja templates for the two screens.
   - Forms use Flask-WTF for HTML routes. JSON routes use request body validation.
   - CSRF: HTML forms respect CSRF in production; JSON routes exempt from CSRF.
   - Unit-test friendly architecture (functions separated in a `tokens.py` and `email_utils.py`).

## File Changes

### A) Config updates: `backend/app/config/settings.py`
- Add:
  ```python
  class Config:
      # ...
      SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
      MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "no-reply@localhost")
      PASSWORD_RESET_TOKEN_MAX_AGE = int(os.getenv("PASSWORD_RESET_TOKEN_MAX_AGE", "3600"))
      PASSWORD_RESET_SALT = os.getenv("PASSWORD_RESET_SALT", "password-reset-salt")
