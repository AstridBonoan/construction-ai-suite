# Phase 17: Deployment Guide - Monday.com Integration

## Production Deployment Checklist

### Pre-Deployment (Do Before Going Live)

- [ ] **OAuth Credentials Created**
  - [ ] Monday.com developer account exists
  - [ ] OAuth app created in Monday.com console
  - [ ] Client ID copied
  - [ ] Client Secret copied (saved securely!)
  - [ ] Redirect URI configured

- [ ] **Environment Configuration**
  - [ ] `.env` file has all required variables
  - [ ] Token encryption key generated
  - [ ] No secrets in code repository
  - [ ] Database configured for token storage

- [ ] **Security**
  - [ ] HTTPS enabled on production domain
  - [ ] API rate limiting configured
  - [ ] CORS properly configured
  - [ ] Secret manager (AWS Secrets Manager, HashiCorp Vault) set up
  - [ ] Audit logging enabled

- [ ] **Testing**
  - [ ] OAuth flow tested locally
  - [ ] Token encryption/decryption working
  - [ ] Board sync tested
  - [ ] Schedule analysis integration tested
  - [ ] Webhook signature validation tested

- [ ] **Documentation**
  - [ ] Team trained on Monday.com integration
  - [ ] Support documentation written
  - [ ] Troubleshooting guide created
  - [ ] API documentation updated

---

## Deployment Steps

### 1. Prepare Production Environment

#### AWS Example

```bash
# Create secrets in AWS Secrets Manager
aws secretsmanager create-secret \
  --name prod/monday-oauth-client-id \
  --secret-string "your_client_id"

aws secretsmanager create-secret \
  --name prod/monday-oauth-client-secret \
  --secret-string "your_client_secret"

aws secretsmanager create-secret \
  --name prod/monday-token-encryption-key \
  --secret-string "$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"
```

#### Heroku Example

```bash
# Set environment variables
heroku config:set MONDAY_OAUTH_CLIENT_ID=your_id
heroku config:set MONDAY_OAUTH_CLIENT_SECRET=your_secret
heroku config:set MONDAY_OAUTH_REDIRECT_URI=https://your-app.herokuapp.com/api/monday/oauth/callback
heroku config:set MONDAY_TOKEN_ENCRYPTION_KEY=your_key
```

### 2. Update Monday.com App Settings

1. Go to https://developer.monday.com/
2. Select your app
3. Update OAuth settings:
   - **Redirect URI**: `https://your-production-domain.com/api/monday/oauth/callback`
   - **App URL**: `https://your-production-domain.com`

### 3. Deploy Backend

```bash
# Option A: Docker (Recommended)
docker build -t monday-integration:latest .
docker tag monday-integration:latest your-registry/monday-integration:latest
docker push your-registry/monday-integration:latest

# Deploy with docker-compose
docker-compose -f docker-compose.prod.yml up -d

# Option B: Direct Deployment
git clone <repo>
cd construction-ai-suite
pip install -r backend/requirements.txt
gunicorn --bind 0.0.0.0:5000 backend.app:app
```

### 4. Deploy Frontend

```bash
# Build production bundle
cd frontend
npm run build

# Deploy to CDN/hosting
aws s3 sync build/ s3://your-bucket/
cloudfront create-invalidation --distribution-id YOUR_ID --paths "/*"
```

### 5. Set Up Database for Token Storage

```bash
# Create PostgreSQL table
psql -U postgres -d your_db << EOF
CREATE TABLE monday_tokens (
    id SERIAL PRIMARY KEY,
    workspace_id VARCHAR(255) UNIQUE NOT NULL,
    access_token TEXT NOT NULL,
    token_type VARCHAR(50) DEFAULT 'Bearer',
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    user_id VARCHAR(255),
    user_name VARCHAR(255),
    user_email VARCHAR(255)
);

CREATE INDEX idx_workspace_id ON monday_tokens(workspace_id);
CREATE INDEX idx_expires_at ON monday_tokens(expires_at);
EOF
```

### 6. Set Up Webhooks

```bash
# Register webhook endpoint with Monday.com
curl -X POST https://api.monday.com/v2/webhooks \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-domain.com/api/monday/webhook/events",
    "event": "item.created",
    "app_url": "https://your-domain.com"
  }'

# Repeat for other events:
# - item.updated
# - column.updated
# - board.updated
```

### 7. Enable HTTPS and Security

```bash
# SSL/TLS Certificate (Let's Encrypt example)
certbot certonly --standalone -d your-domain.com

# Update nginx/Apache config
server {
    listen 443 ssl http2;
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}
```

### 8. Monitor and Test

```bash
# Check integration status
curl https://your-domain.com/api/monday/status

# Monitor logs
tail -f logs/monday_integration.log

# Set up alerts
aws cloudwatch put-metric-alarm \
  --alarm-name monday-api-errors \
  --alarm-description "Alert on Monday API errors" \
  --metric-name APIErrors \
  --threshold 5 --comparison-operator GreaterThanThreshold
```

---

## Docker Deployment

### Dockerfile Configuration

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir requests  # For Monday.com API

# Copy application
COPY backend/ .

# Environment variables (will be set at runtime)
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/api/monday/status || exit 1

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "app:app"]
```

### Docker Compose Configuration

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    image: your-registry/monday-integration:latest
    ports:
      - "5000:5000"
    environment:
      FLASK_ENV: production
      MONDAY_OAUTH_CLIENT_ID: ${MONDAY_OAUTH_CLIENT_ID}
      MONDAY_OAUTH_CLIENT_SECRET: ${MONDAY_OAUTH_CLIENT_SECRET}
      MONDAY_OAUTH_REDIRECT_URI: ${MONDAY_OAUTH_REDIRECT_URI}
      MONDAY_TOKEN_ENCRYPTION_KEY: ${MONDAY_TOKEN_ENCRYPTION_KEY}
      DATABASE_URL: postgresql://user:password@db:5432/monday_db
    depends_on:
      - db
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/monday/status"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: always

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: monday_db
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

  frontend:
    image: your-registry/monday-frontend:latest
    ports:
      - "3000:3000"
    environment:
      REACT_APP_API_URL: ${API_URL}
    restart: always

volumes:
  postgres_data:
```

---

## Performance Optimization

### API Rate Limiting

```python
# Add to backend/app/__init__.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Apply to Monday.com endpoints
@monday_bp.route('/sync/boards')
@limiter.limit("10 per minute")
def sync_boards():
    ...
```

### Caching

```python
from flask_caching import Cache

cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': os.getenv('REDIS_URL')
})

@monday_bp.route('/sync/boards')
@cache.cached(timeout=300)  # Cache for 5 minutes
def sync_boards():
    ...
```

### Connection Pooling

```python
# Use connection pooling for database
from sqlalchemy.pool import QueuePool

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'poolclass': QueuePool,
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True
}
```

---

## Monitoring and Alerts

### Key Metrics to Monitor

1. **API Response Time**
   - Target: < 500ms
   - Alert if: > 2000ms

2. **OAuth Success Rate**
   - Target: > 99%
   - Alert if: < 95%

3. **Token Refresh Rate**
   - Monitor: How often tokens are refreshed
   - Alert if: Spike in refresh requests

4. **Webhook Events**
   - Monitor: Events received from Monday.com
   - Alert if: No events for > 1 hour

5. **Database Performance**
   - Monitor: Query time, connection pool usage
   - Alert if: Slow queries or pool exhaustion

### Logging Configuration

```python
# backend/app/logging_config.py
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(app):
    if not app.debug:
        file_handler = RotatingFileHandler(
            'logs/monday_integration.log',
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        # Also log to CloudWatch
        import watchtower
        cw_handler = watchtower.CloudWatchLogHandler()
        app.logger.addHandler(cw_handler)
```

---

## Rollback Plan

If issues occur in production:

### 1. Immediate Actions (0-5 minutes)

```bash
# Stop serving traffic to Monday.com endpoints
# Scale down Monday.com backend services
docker-compose -f docker-compose.prod.yml down

# Revert to previous version
git checkout <previous_commit>
docker build -t monday-integration:previous .
docker run -d monday-integration:previous
```

### 2. Investigate (5-30 minutes)

```bash
# Check logs
tail -f logs/monday_integration.log

# Check database connectivity
psql -U postgres -d monday_db -c "SELECT 1"

# Check API status
curl https://your-domain.com/api/monday/status
```

### 3. Communicate (Ongoing)

- Notify Monday.com app users
- Post status update on dashboard
- Contact Monday.com support if needed

### 4. Fix and Re-deploy

```bash
# After fix is tested
git commit -m "Hotfix: <description>"
docker build -t monday-integration:latest .
docker-compose -f docker-compose.prod.yml up -d
```

---

## Post-Deployment

### Validation Checklist

- [ ] OAuth flow works end-to-end
- [ ] User can connect Monday.com account
- [ ] Boards load successfully
- [ ] Schedule analysis processes correctly
- [ ] Results update in Monday.com
- [ ] Webhooks firing correctly
- [ ] Database queries performant
- [ ] Logs showing normal operation
- [ ] No errors in last 24 hours
- [ ] Users reporting success

### Performance Baseline (First 24 Hours)

Record baseline metrics:
- Average API response time
- OAuth success rate
- Database query time
- Error rate
- User satisfaction

Use these to set alert thresholds for future issues.

---

## Ongoing Maintenance

### Weekly
- Review error logs
- Check API quotas
- Monitor performance metrics

### Monthly
- Review user feedback
- Update dependencies
- Security patching
- Performance optimization

### Quarterly
- Capacity planning
- Feature updates
- User surveys
- Team retrospective

---

## Support Escalation

### Tier 1: Common Issues
- Monday.com authentication fails → Check OAuth credentials
- Boards not loading → Check API rate limits
- Database error → Check connection pool

### Tier 2: Complex Issues
- Schedule analysis incorrect → Review Phase 16 integration
- Webhook processing slow → Check queue
- Token encryption issues → Contact security team

### Tier 3: Emergency
- Production outage → Page on-call engineer
- Data loss → Restore from backup
- Security breach → Follow incident response plan

---

**Deployment Ready!** 🚀

Next: Run through deployment checklist and go live!
