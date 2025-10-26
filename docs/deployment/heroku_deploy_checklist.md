# 🧭 BudgetSync Deployment Checklist (Heroku + AWS RDS)

**Goal:** Secure, production-ready deployment of BudgetSync using Heroku for the web app and AWS RDS for the PostgreSQL database.

---

## ⚙️ 1️⃣ Pre-Deployment: Database Hardening (AWS RDS)

- [ ] **Enable SSL**
  - Modify your `.env` `DATABASE_URL`:
    ```bash
    DATABASE_URL=postgresql+psycopg2://budgetsync_admin:<PASSWORD>@budgetsync-db.cp2qu0o24dgl.us-east-2.rds.amazonaws.com:5432/budgetsync?sslmode=require
    ```
  - Confirm SSL is active:
    ```bash
    psql -h <rds-endpoint> -U budgetsync_admin -d budgetsync
    SHOW ssl;
    ```
    → should return `on`.

- [ ] **Strengthen DB Password**
  - Generate a strong password (e.g., 20+ characters, symbols, mixed case).
  - In AWS Console → **RDS → Modify DB instance → Credentials settings**
  - Apply the new password immediately.
  - Update `.env` and Heroku config:
    ```bash
    heroku config:set DATABASE_URL=postgresql+psycopg2://budgetsync_admin:<NEW_PASSWORD>@budgetsync-db.cp2qu0o24dgl.us-east-2.rds.amazonaws.com:5432/budgetsync?sslmode=require
    ```

- [ ] **Restrict Permissions**
  - Create a limited user if desired (no superuser privileges).
  - Example (optional):
    ```sql
    CREATE USER app_user WITH PASSWORD '<strong_pass>';
    GRANT CONNECT ON DATABASE budgetsync TO app_user;
    GRANT USAGE ON SCHEMA public TO app_user;
    GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user;
    ```

- [ ] **Public Access for Heroku**
  - Keep **Public access = Yes** (Heroku needs it).
  - Limit exposure with **strong password** + `sslmode=require`.

---

## 🧰 2️⃣ Application Prep

- [ ] **Update `.env`**
  - Include all required secrets:
    ```bash
    FLASK_ENV=production
    SECRET_KEY=<strong_flask_secret>
    DATABASE_URL=postgresql+psycopg2://budgetsync_admin:<PASSWORD>@budgetsync-db.cp2qu0o24dgl.us-east-2.rds.amazonaws.com:5432/budgetsync?sslmode=require
    SENDGRID_API_KEY=<sendgrid-key>
    ```

- [ ] **Add Gunicorn**
  - Add to `requirements.txt`:
    ```
    gunicorn
    psycopg2-binary
    ```
  - Gunicorn is Heroku’s production-grade WSGI server.

- [ ] **Create `Procfile`**
  ```bash
  web: gunicorn "src.budget_sync.app:create_app()"
  ```

- [ ] **Create `runtime.txt`**
  ```
  python-3.12.5
  ```

- [ ] **Verify Flask Entrypoint**
  - Ensure your `__init__.py` exposes `create_app()` (if using factory pattern).
  - Confirm app runs locally:
    ```bash
    flask run
    ```

---

## 🐳 3️⃣ Dockerization (Optional but Recommended)

- [ ] **Create `Dockerfile`**
  ```dockerfile
  FROM python:3.12-slim
  ENV PYTHONDONTWRITEBYTECODE=1
  ENV PYTHONUNBUFFERED=1
  WORKDIR /app
  RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  COPY . .
  EXPOSE 5000
  CMD ["gunicorn", "src.budget_sync.app:create_app()", "--bind", "0.0.0.0:5000"]
  ```

- [ ] **Add `.dockerignore`**
  ```bash
  __pycache__/
  *.pyc
  *.db
  .env
  budgetsync_backup.sql
  venv/
  .git
  .idea/
  flask_session/
  ```

- [ ] **Build & Test Locally**
  ```bash
  docker build -t budgetsync .
  docker run -p 5000:5000 --env-file .env budgetsync
  ```

---

## 🔐 4️⃣ GitHub Security & Vulnerability Audit

- [ ] **Run Local Vulnerability Check**
  ```bash
  pip install safety
  safety check
  ```
  or
  ```bash
  pip-audit
  ```

- [ ] **Fix Warnings**
  - Upgrade vulnerable dependencies.
  - Pin versions in `requirements.txt` or `pyproject.toml`.

- [ ] **Enable Dependabot**
  - In your GitHub repo → **Settings → Security → Dependabot alerts** → Enable.
  - Create `.github/dependabot.yml` if needed.

- [ ] **Add `.gitignore` Rules**
  - Ensure sensitive files are excluded:
    ```bash
    .env
    budgetsync_backup.sql
    __pycache__/
    flask_session/
    ```

---

## ☁️ 5️⃣ Heroku Deployment

- [ ] **Login**
  ```bash
  heroku login
  ```

- [ ] **Create App**
  ```bash
  heroku create budgetsync
  ```

- [ ] **Set Config Vars**
  ```bash
  heroku config:set FLASK_ENV=production
  heroku config:set SECRET_KEY=<secret>
  heroku config:set DATABASE_URL=postgresql+psycopg2://budgetsync_admin:<PASSWORD>@budgetsync-db.cp2qu0o24dgl.us-east-2.rds.amazonaws.com:5432/budgetsync?sslmode=require
  heroku config:set SENDGRID_API_KEY=<sendgrid-key>
  ```

- [ ] **Deploy via Git**
  ```bash
  git push heroku main
  ```

- [ ] **Or Deploy via Docker**
  ```bash
  heroku container:login
  heroku container:push web
  heroku container:release web
  ```

- [ ] **Open App**
  ```bash
  heroku open
  ```

---

## 🧩 6️⃣ Post-Deployment Validation

- [ ] **Verify RDS Connection**
  - Register a user in the live app → confirm new record in AWS RDS.

- [ ] **Enable HTTPS**
  - Heroku does this automatically for custom domains via Let’s Encrypt.

- [ ] **Check Logs**
  ```bash
  heroku logs --tail
  ```

- [ ] **Monitor**
  - Enable Heroku Metrics in your dashboard.

---

## 🔒 7️⃣ Final Security Pass

- [ ] **Rotate RDS Password** every 90 days.
- [ ] **Enforce SSL connections** on AWS RDS.
- [ ] **Set Public Access → No** *only* if migrating app inside AWS.
- [ ] **Restrict access** to trusted IPs or app networks.
- [ ] **Confirm backups** and snapshot retention (RDS).

---

## ✅ Deployment Complete

When all boxes are checked:
- Your app is **containerized, secure, and live**.
- AWS RDS is **encrypted and hardened**.
- Heroku deployment is **reproducible**.
- GitHub repo is **clean and vulnerability-free**.

---

**Next step:**  
Tag your release — e.g.,  
```bash
git tag -a v1.0.0 -m "Initial Heroku deployment"
git push origin v1.0.0
```
