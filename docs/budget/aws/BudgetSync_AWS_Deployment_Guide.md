# BudgetSync — AWS Deployment Guide (Flask + Postgres)

This guide walks you from **local-only** to a **clean, minimal, and professional AWS deployment**. It includes two routes:

- **Route A (simplest / cheapest): Elastic Beanstalk (no Docker required)**
- **Route B (modern container path): App Runner (needs Docker)**

Both routes use:
- **RDS Postgres** (managed database)
- **S3** for static files and (optionally) user uploads
- **CloudWatch Logs** for observability
- **Secrets Manager** for secrets
- **Route 53 + ACM** for domain + HTTPS (optional but recommended)

> Tip: Start with **Route A** to ship quickly and cheaply. Migrate to **Route B** later for container experience.

---

## 0) Architecture at a glance

```
[User] ──HTTPS──> [AWS EB or App Runner] ──SQL──> [RDS Postgres]
                              │
                              ├──S3 (static & uploads)
                              ├──CloudWatch Logs (app logs)
                              └──Secrets Manager (DB creds, API keys)
```

---

## 1) Prerequisites

- AWS account (free tier helps)
- Domain (optional): managed in **Route 53** or elsewhere
- BudgetSync app runs locally with env config (12-factor style)
- A migration tool (e.g., **Flask-Migrate/Alembic**)

**Environment variables / secrets (example):**
```
FLASK_ENV=production
SECRET_KEY=...
DATABASE_URL=postgresql+psycopg2://<user>:<pass>@<host>:5432/<db>
SENDGRID_API_KEY=...
S3_BUCKET=your-budgetsync-bucket
AWS_REGION=us-east-1
# Optional:
SESSION_SECRET=...
SECURITY_PASSWORD_SALT=...
```

> Store these in **AWS Secrets Manager** or EB / App Runner env vars. Avoid committing secrets to Git.

---

## 2) Database — RDS Postgres (common to both routes)

1. **Create RDS Postgres** (choose a small instance first):
   - Engine: **PostgreSQL**
   - Instance class: **db.t4g.micro** (dev) or **db.t4g.small** (small prod)
   - Storage: 20 GB gp3 (can auto-scale later)
   - Public access: **No** (preferred). Use **security groups** to allow access only from your app.
   - Backups: Enable **automated backups** (7–14 days).
   - IAM: standard password auth is fine to start.

2. **Security group** rules:
   - **Inbound** on port 5432 from **your app’s security group** (EB EC2 or App Runner VPC connector).
   - No open 0.0.0.0/0 inbound to the DB.

3. **Get the connection string**:
   - `postgresql+psycopg2://<user>:<pass>@<rds-endpoint>:5432/<dbname>`
   - Save it in **Secrets Manager** (recommended) or inject as env var.

4. **Run migrations** from your workstation or from a one-off app task:
   - Example (Flask-Migrate): `flask db upgrade`

---

## 3) Static & uploads — S3

- Create an **S3 bucket**: `budgetsync-<your-unique-suffix>`
- In app settings:
  - For static: consider building locally then syncing to S3 (or serve via app first, move later).
  - For uploads: write directly to S3 via `boto3`, store keys in DB.

**Minimal config snippet (Python):**
```python
import boto3, os

s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION"))
bucket = os.getenv("S3_BUCKET")

def upload_fileobj(fileobj, key):
    s3.upload_fileobj(fileobj, bucket, key, ExtraArgs={"ACL": "private"})
    return f"s3://{bucket}/{key}"
```

> For public assets, consider **CloudFront** later. Start simple with S3.

---

## 4) Observability — CloudWatch Logs

- EB: enable log streaming to CloudWatch in environment settings.
- App Runner: logs are streamed automatically; view in CloudWatch.
- Add basic **alarms** (CPU high, 5xx rates) for your app service.
- Add RDS **free storage** and **CPU** alarms.

---

## 5) Secrets — AWS Secrets Manager

- Create secrets:
  - `budgetsync/db-url`
  - `budgetsync/sendgrid-api-key`
  - …
- Retrieve them at deploy-time and set as env vars **or** fetch at runtime.
- Pricing note: Secrets Manager is billed **per secret per month**; group related values to control cost.

---

## 6) HTTPS + DNS — Route 53 + ACM (optional but recommended)

1. **Buy or transfer domain** to Route 53 (or keep current registrar).
2. Create a **public hosted zone** and an **A record** pointing to:
   - EB environment URL via CNAME, or
   - App Runner default domain via CNAME (or use a custom domain mapping).
3. **ACM certificate** in the same region as your service; validate via DNS.
4. Attach cert to EB load balancer (if used) or to App Runner custom domain mapping.

---

## 7) Route A — Elastic Beanstalk (no Docker required)

**Why EB now?** Fastest way to get a proper Linux host running your Flask app cheaply. Use a **single-instance environment** to avoid load balancer costs initially.

### Steps
1. **Install EB CLI** locally (`pipx install awsebcli` or `pip install awsebcli`).
2. In your project root, run: `eb init`
   - Platform: **Python** (latest)
   - Region: e.g., **us-east-1**
3. Create environment: `eb create budgetsync-dev --single`
   - `--single` avoids the load balancer (cheaper).
   - Choose instance type: `t3.micro` to start.
4. Configure **env vars** in EB console (or via `eb setenv`):
   - `FLASK_ENV=production`
   - `DATABASE_URL=...`
   - `SECRET_KEY=...`
   - `S3_BUCKET=...`
   - etc.
5. **Deploy**: `eb deploy`
6. **Logs**: view in EB console or enable streaming to CloudWatch.
7. **DB migration**: Via SSH into instance or add a one-time EB hook to run `flask db upgrade` after deploy.
8. **HTTPS**: If you need it on day one:
   - Either add an Application Load Balancer (costlier) + ACM cert, or
   - Terminate TLS at a reverse proxy you configure on the instance (advanced; not default).

**Procfile (if using gunicorn):**
```
web: gunicorn "app:create_app()"
```
> Adjust the import to your factory or `wsgi:app`

**.ebextensions example (env, packages, etc.):**
- You can add `.ebextensions/` YAML files to install system packages or run container commands.

---

## 8) Route B — App Runner (Docker required)

**Why App Runner later?** Great DX for containers, HTTPS by default, easy scaling. Typically **more expensive** than EB single-instance but simpler than managing EC2.

### Dockerfile (example)
```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml poetry.lock* requirements.txt* /app/

# Choose your dependency manager. Example with pip:
RUN python -m pip install --upgrade pip \
    && if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

COPY . /app

# Create non-root user
RUN useradd -m appuser
USER appuser

ENV PORT=8080
EXPOSE 8080

# Gunicorn entrypoint (adjust module/factory)
CMD gunicorn "app:create_app()" --bind 0.0.0.0:${PORT} --workers 2 --threads 4 --timeout 60
```

### Steps
1. **Create ECR repo** and push image:
   - `docker build -t budgetsync:latest .`
   - `docker tag budgetsync:latest <aws_account>.dkr.ecr.<region>.amazonaws.com/budgetsync:latest`
   - `docker push <…>/budgetsync:latest`
2. **Create App Runner service** from ECR image.
3. Set **environment variables** in App Runner console.
4. **VPC connector** (recommended) to reach **RDS** privately.
5. **Autoscaling**: start with min = 1 instance.
6. **Custom domain** + **HTTPS** using ACM.
7. Logs available in **CloudWatch**.

---

## 9) CI/CD (optional quick wins)

### GitHub Actions — Elastic Beanstalk (zip deploy)
```yaml
name: Deploy to EB
on:
  push:
    branches: [ main ]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install awsebcli
      - run: eb init budgetsync -p python-3.12 -r us-east-1
      - run: eb deploy budgetsync-dev
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_DEFAULT_REGION: us-east-1
```

### GitHub Actions — App Runner (build & push to ECR)
```yaml
name: Build and Push to ECR
on:
  push:
    branches: [ main ]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Configure AWS creds
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      - name: Login to ECR
        uses: aws-actions/amazon-ecr-login@v2
      - name: Build, Tag, Push
        run: |
          REPO=<aws_account>.dkr.ecr.us-east-1.amazonaws.com/budgetsync
          docker build -t budgetsync:latest .
          docker tag budgetsync:latest $REPO:${{ github.sha }}
          docker push $REPO:${{ github.sha }}
```

---

## 10) Security hardening (phase-in)

- Use **IAM roles** for EB EC2 / App Runner to access S3, Secrets Manager.
- Enforce **HTTPS**.
- Turn on **automatic minor version upgrades** for RDS.
- **Rotate secrets** (manually at first).
- Restrict security groups strictly (no public DB).
- Add **daily snapshots** for RDS + verify restores.

---

## 11) Estimated monthly costs (ballpark)

> **Assumptions**: us-east-1, very low traffic dev environment, 20GB RDS storage, minimal data transfer. Prices change; these are **ballpark** numbers to help you reason about tradeoffs.

### Dev (cheapest path) — **Elastic Beanstalk (single instance)**
| Item                          | Choice / Notes                       | Est. Monthly |
|-------------------------------|--------------------------------------|--------------|
| **Compute (EB EC2)**          | t3.micro single-instance             | **$8–12**    |
| **RDS Postgres**              | db.t4g.micro + 20GB gp3              | **$13–20**   |
| **EBS storage (EC2 root)**    | 8–16GB                               | ~$1–2        |
| **S3**                        | Static + light uploads               | ~$0.5–2      |
| **Secrets Manager**           | 1–3 secrets                          | ~$0.40–$1.20 |
| **CloudWatch Logs**           | Low volume                           | ~$1–3        |
| **Route 53 (optional)**       | Hosted zone + domain                 | ~$0.50 + domain fee |
| **Total (dev)**               |                                      | **~$25–40**  |

> Avoid a load balancer initially. An ALB adds ~$16–20/month idle cost.

### Small Prod — EB with ALB (more robust)
| Item                          | Choice / Notes                       | Est. Monthly |
|-------------------------------|--------------------------------------|--------------|
| **Compute (EB EC2)**          | t3.small                             | **$15–25**   |
| **ALB**                       | For HTTPS/health checks              | **$16–25**   |
| **RDS Postgres**              | db.t4g.small + 50GB gp3              | **$25–45**   |
| **EBS storage**               | 16–30GB                              | ~$2–4        |
| **S3**                        | Static + modest uploads              | ~$2–5        |
| **Secrets Manager**           | 3–6 secrets                          | ~$1.20–$2.40 |
| **CloudWatch Logs**           | Moderate                             | ~$3–6        |
| **Route 53**                  | Hosted zone + domain                 | ~$0.50 + domain fee |
| **Total (small prod)**        |                                      | **~$65–110** |

### App Runner (always-on container)
| Item                          | Choice / Notes                       | Est. Monthly |
|-------------------------------|--------------------------------------|--------------|
| **App Runner compute**        | 1 instance (typical baseline)        | **~$40–70**  |
| **RDS Postgres**              | db.t4g.micro/small                   | **$13–45**   |
| **S3 + Secrets + Logs**       | Similar to EB                        | ~$3–8        |
| **Route 53**                  | Optional                             | ~$0.50 + domain fee |
| **Total (dev/small prod)**    |                                      | **~$60–120** |

> App Runner pricing depends on vCPU/GB-hr and active instances. It’s super convenient, but typically a bit pricier than EB single-instance for tiny apps.

---

## 12) Rollout plan

1. **Ship quickly with EB single-instance** (no ALB). Verify app health, logging, RDS connectivity, migrations.
2. Add **S3** for static/uploads.
3. Add **Secrets Manager** and remove any plaintext secrets.
4. Add **alarms** in CloudWatch for CPU, 5xx, RDS storage.
5. When traffic grows, upgrade to **ALB** and a slightly larger EC2.
6. Later, if you want container DX: **migrate to App Runner** with a Dockerfile.

---

## 13) Common gotchas

- Security groups: make sure the **app SG** can reach **RDS SG** on 5432.
- Timeouts: set gunicorn workers/threads sensibly; ensure health checks don’t hit slow endpoints.
- Migrations: run them **after** setting `DATABASE_URL` to RDS.
- File storage: if you initially stored files locally, migrate to S3 and update any path logic.
- Costs: watch for idle ALB or oversized RDS classes; right-size monthly.

---

## 14) “Am I done?” checklist

- [ ] App reachable over HTTP (and HTTPS if configured)
- [ ] Logs visible in CloudWatch
- [ ] RDS reachable from app; migrations applied
- [ ] Static and/or uploads confirmed in S3
- [ ] Secrets in Secrets Manager (not in Git)
- [ ] Backups & alarms turned on
- [ ] README docs updated with runbooks (how to deploy, roll back, rotate secrets)

---

### Final advice

Start with **Elastic Beanstalk single-instance** to keep cost + complexity low. Once BudgetSync is live and steady, you can iterate toward **ALB**, **CloudFront**, **App Runner**, or even **ECS/EKS**. The key is to **ship**, then **tighten**.
