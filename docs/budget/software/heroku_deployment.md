# Heroku Deployment Guide
## Database Configuration and Management

### 1. Initial Setup

#### 1.1 Heroku PostgreSQL Provisioning
```bash
# Add PostgreSQL to your Heroku budget_sync
heroku addons:create heroku-postgresql:hobby-dev

# For production, consider using a higher tier
heroku addons:create heroku-postgresql:standard-0
```

#### 1.2 Database URL Configuration
The `DATABASE_URL` will be automatically added to your environment variables. Update your `.env` file locally to match Heroku's format:
```
DATABASE_URL=postgresql://[user]:[password]@[host]:[port]/[database]
```

### 2. Connection Pooling

#### 2.1 Enable Connection Pooling
Heroku PostgreSQL uses PgBouncer for connection pooling. To enable it:

```bash
# Enable connection pooling
heroku config:set DATABASE_CONNECTION_POOL=true
```

#### 2.2 Update Database Configuration
Add these settings to `app/config/settings.py`:

```python
class ProductionConfig(Config):
    """Production-specific configuration."""
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,  # Maximum number of connections to keep
        'pool_timeout': 30,  # Timeout for getting connection from pool
        'pool_recycle': 1800,  # Recycle connections after 30 minutes
        'max_overflow': 10  # Allow up to 10 connections beyond pool_size
    }
```

#### 2.3 Connection Pool Best Practices
- Standard-0 and above plans support up to 120 connections
- Keep `pool_size` + `max_overflow` below your plan's connection limit
- Monitor connection usage with:
  ```bash
  heroku pg:info
  ```

### 3. Database Backups

#### 3.1 Automated Backups
Heroku PostgreSQL provides automated backups:
- Hobby-dev: No automated backups
- Standard-0 and above: Daily backups retained for 1 week

To check backup status:
```bash
heroku pg:backups
```

#### 3.2 Manual Backups
Create manual backups:
```bash
# Create a backup
heroku pg:backups:capture

# Download latest backup
heroku pg:backups:download

# Schedule manual backups (if needed)
heroku pg:backups:schedule --at '02:00 America/New_York'
```

#### 3.3 Backup Retention
- Standard-0: 2 weeks retention
- Standard-2: 4 weeks retention
- Premium-0 and above: 6 weeks retention

### 4. Monitoring and Maintenance

#### 4.1 Database Metrics
Monitor database performance:
```bash
# View database metrics
heroku pg:metrics

# Check connection count
heroku pg:ps

# View index usage
heroku pg:index-usage
```

#### 4.2 Database Maintenance
Heroku handles most maintenance automatically:
- Version upgrades
- Security patches
- Infrastructure maintenance

#### 4.3 Performance Monitoring
Enable Heroku PostgreSQL metrics:
```bash
# Enable detailed metrics
heroku addons:create heroku-postgresql:metrics-basic
```

### 5. Disaster Recovery

#### 5.1 Point-in-Time Recovery (PITR)
Available on Standard-0 and above plans:
```bash
# Restore to a specific timestamp
heroku pg:backups:restore --budget_sync=myapp '2023-12-01 12:00:00 UTC'
```

#### 5.2 Follower Databases
For high availability (Premium-0 and above):
```bash
# Create a follower database
heroku addons:create heroku-postgresql:premium-0 --follow HEROKU_POSTGRESQL_MAIN_URL
```

### 6. Security

#### 6.1 SSL Configuration
Heroku PostgreSQL uses SSL by default. Update your database URL:
```python
SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL').replace('postgres://', 'postgresql://')
```

#### 6.2 Database Credentials
Rotate credentials periodically:
```bash
heroku pg:credentials:rotate
```

### 7. Cost Management

#### 7.1 Plan Comparison
- Hobby-dev ($0/month): Development only, 10k rows limit
- Standard-0 ($50/month): Production ready, daily backups
- Standard-2 ($200/month): Higher resources, longer retention
- Premium plans: High availability, PITR, followers

#### 7.2 Resource Monitoring
```bash
# Monitor database size
heroku pg:info

# Check detailed usage
heroku pg:diagnose
```

### 8. Troubleshooting

#### 8.1 Common Issues
1. Connection timeouts
   - Check connection pool settings
   - Monitor active connections
   - Review query performance

2. Backup failures
   - Verify storage limits
   - Check backup logs
   - Contact Heroku support

#### 8.2 Support Resources
- Heroku PostgreSQL Dashboard
- Heroku CLI
- Heroku Support Tickets
- PostgreSQL Logs 