# Phase 17: Monday.com Integration - Quick Start Guide

## 5-Minute Setup

### 1. Get OAuth Credentials

```bash
# Go to https://developer.monday.com/
# 1. Sign in with your Monday account
# 2. Create new app OR use existing one
# 3. Copy these 3 values:
#    - Client ID
#    - Client Secret  
#    - Redirect URI (will provide)
```

### 2. Configure Environment

```bash
# Create/edit .env file in project root
cat > .env << EOF
MONDAY_OAUTH_CLIENT_ID=your_client_id_here
MONDAY_OAUTH_CLIENT_SECRET=your_client_secret_here
MONDAY_OAUTH_REDIRECT_URI=http://localhost:5000/api/monday/oauth/callback
EOF
```

### 3. Backend Setup

```bash
# Install dependencies
pip install requests  # For API calls

# Update Flask app to register blueprint
# In backend/app/__init__.py or app.py:
# 
#   from app.phase17_monday_integration import monday_bp
#   app.register_blueprint(monday_bp)
```

### 4. Frontend Setup

```bash
# The component is ready to use:
# frontend/src/components/MondayOAuthComponent.jsx

# Add to your main app:
# import MondayOAuthComponent from './components/MondayOAuthComponent';
# 
# <MondayOAuthComponent />
```

### 5. Run

```bash
# Start backend
python run_server.py

# In browser:
# http://localhost:3000  (or your frontend port)
# 
# You should see "Connect Monday.com" button
```

### 6. Test OAuth Flow

1. Click **"Connect Monday.com"** button
2. You'll be redirected to Monday.com login
3. Grant permissions
4. You'll see list of your boards
5. Click **"Analyze Schedule"** to test integration

---

## Common Tasks

### Check Connection Status

```bash
curl http://localhost:5000/api/monday/status
```

Response:
```json
{
  "configured": true,
  "authenticated_workspaces": ["workspace_123"],
  "features": [...]
}
```

### List User's Boards

```bash
curl http://localhost:5000/api/monday/sync/boards \
  -H "Authorization: Bearer <access_token>"
```

### Analyze a Board's Schedule

```bash
curl -X POST http://localhost:5000/api/monday/sync/analyze/board_123 \
  -H "Authorization: Bearer <access_token>"
```

### Debugging

```bash
# Check logs
tail -f logs/monday_integration.log

# Enable debug mode
export MONDAY_LOG_LEVEL=DEBUG
python run_server.py
```

---

## API Endpoints Cheat Sheet

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/monday/oauth/start` | Start OAuth flow |
| GET | `/api/monday/oauth/callback` | OAuth callback (automatic) |
| GET | `/api/monday/sync/boards` | Get user's boards |
| GET | `/api/monday/sync/board/<id>` | Get board items |
| POST | `/api/monday/sync/analyze/<id>` | Analyze board |
| POST | `/api/monday/webhook/events` | Receive webhooks |
| GET | `/api/monday/status` | Check integration status |
| GET | `/api/monday/config` | Get configuration |

---

## Troubleshooting

### "OAuth credentials not configured"

Add to `.env`:
```
MONDAY_OAUTH_CLIENT_ID=...
MONDAY_OAUTH_CLIENT_SECRET=...
```

### Redirect URI mismatch error

1. Check your `.env` value matches Monday.com app settings
2. Development: use `http://localhost:5000/api/monday/oauth/callback`
3. Production: use your actual domain

### "Cannot read boards" error

1. User hasn't connected (no token stored)
2. Token has expired
3. Try re-connecting: clear browser cookies, click "Connect Monday.com" again

### Boards not syncing

1. Check webhook is registered in Monday.com
2. Verify webhook signature in logs
3. Check network connectivity to Monday.com API

---

## For Production Deployment

### Environment Variables

Set in your cloud platform (AWS, Heroku, etc.):

```
MONDAY_OAUTH_CLIENT_ID=your_prod_id
MONDAY_OAUTH_CLIENT_SECRET=your_prod_secret
MONDAY_OAUTH_REDIRECT_URI=https://your-domain.com/api/monday/oauth/callback
MONDAY_TOKEN_ENCRYPTION_KEY=your_encryption_key
```

### Update Monday.com Settings

In Monday.com developer portal:
1. Change Redirect URI to: `https://your-domain.com/api/monday/oauth/callback`
2. Update app website URL
3. Set up webhook endpoint

### Database Setup

Replace in-memory storage with PostgreSQL:

```python
# backend/app/__init__.py
from flask_sqlalchemy import SQLAlchemy
from app.models.monday_token import db

db.init_app(app)

with app.app_context():
    db.create_all()
```

### Security Checklist

- [ ] OAuth credentials securely stored (not in code)
- [ ] Tokens encrypted at rest
- [ ] HTTPS enabled (redirect URI is https://)
- [ ] Webhook signatures validated
- [ ] Rate limiting enabled
- [ ] Error messages don't expose tokens
- [ ] Audit logging enabled

---

## Next Steps

1. **Test Locally**: Follow setup steps above
2. **Deploy**: Push to your development/staging environment
3. **Publish App**: (Optional) Submit to Monday.com app store
4. **Monitor**: Set up alerts for API errors
5. **Iterate**: Gather user feedback and improve features

---

## Support

- **Questions?** Check [Phase 17 Full Documentation](PHASE_17_MONDAY_SEAMLESS_INTEGRATION.md)
- **Issues?** See troubleshooting section above
- **Monday.com API?** https://api.monday.com/graphql/v2
- **Bug Report?** GitHub Issues in this repo

---

**Ready to go!** 🚀

Next: Connect to Monday.com and start analyzing construction schedules!
