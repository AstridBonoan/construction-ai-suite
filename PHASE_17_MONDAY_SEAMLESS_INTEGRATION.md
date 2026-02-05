# Phase 17: Monday.com Seamless Integration (App-Mode)

## Executive Summary

Phase 17 delivers a **zero-friction Monday.com integration** where users don't need to manually provide API keys. Instead, the system acts like a real Monday.com app with:

✅ **OAuth-based authentication** - Users click one button to connect  
✅ **Automatic sync** - Boards and tasks sync automatically  
✅ **Bidirectional updates** - Risk scores and recommendations push back to Monday.com  
✅ **Webhook support** - Real-time event handling  
✅ **Secure token management** - Tokens stored encrypted, no API key exposure  

---

## Architecture

### 1. OAuth Flow (No API Keys!)

```
User clicks "Connect Monday.com"
    ↓
Redirected to Monday.com OAuth dialog (user clicks "Allow")
    ↓
Monday.com redirects back with authorization code
    ↓
Backend exchanges code for access token
    ↓
Token stored securely in database
    ↓
User can now sync and analyze boards
```

### 2. Components

#### Backend
- **`phase17_monday_integration.py`** - Main Flask blueprint with:
  - `MondayOAuthHandler` - OAuth flow management
  - `MondayAPI` - GraphQL API wrapper
  - Routes for syncing, analyzing, and webhooks

#### Frontend
- **`MondayOAuthComponent.jsx`** - React component for:
  - OAuth button
  - Board listing and selection
  - Analysis trigger

#### Configuration
- **`.env.monday.template`** - Environment variables setup

---

## Setup Instructions

### Step 1: Create Monday.com Developer Account

1. Go to https://developer.monday.com/
2. Sign in with your Monday.com account
3. Create a new app or use existing one

### Step 2: Configure OAuth

1. In app settings, find "OAuth & Permissions"
2. Set **Redirect URI** to your deployment URL:
   - **Development**: `http://localhost:5000/api/monday/oauth/callback`
   - **Production**: `https://your-domain.com/api/monday/oauth/callback`
3. Copy **Client ID** and **Client Secret**
4. Note the scopes you need (see below)

### Step 3: Environment Setup

Create `.env` file in project root:

```bash
# Copy and fill in your OAuth credentials
cp .env.monday.template .env

# Edit .env and add:
MONDAY_OAUTH_CLIENT_ID=your_client_id
MONDAY_OAUTH_CLIENT_SECRET=your_client_secret
MONDAY_OAUTH_REDIRECT_URI=http://localhost:5000/api/monday/oauth/callback
```

### Step 4: Install Backend Integration

```bash
# In backend directory
pip install -r requirements.txt

# Ensure Flask is installed (should already be)
pip install requests  # For API calls
```

### Step 5: Register Blueprint in Flask App

In `backend/app/__init__.py` or `app.py`:

```python
from app.phase17_monday_integration import monday_bp

app = Flask(__name__)
app.register_blueprint(monday_bp)
```

### Step 6: Frontend Integration

```bash
# In frontend directory
npm install axios react

# Add component to your layout
import MondayOAuthComponent from './components/MondayOAuthComponent';

function App() {
  return (
    <div>
      <MondayOAuthComponent />
      {/* rest of app */}
    </div>
  );
}
```

### Step 7: Database Setup (Token Storage)

```bash
# Create token storage table
python -c "
from backend.app.models import db, MondayToken
db.create_all()
"
```

---

## OAuth Scopes

The app requires these Monday.com scopes:

| Scope | Purpose |
|-------|---------|
| `boards:read` | List user's boards |
| `boards:write` | Create/modify boards |
| `items:read` | Read tasks/items |
| `items:write` | Update task status, fields |
| `columns:read` | Read board columns |
| `columns:write` | Create new columns for results |
| `webhooks:write` | Create webhooks for real-time sync |

---

## API Endpoints

### Authentication

**GET** `/api/monday/oauth/start`
- Initiates OAuth flow
- Returns authorization URL
- User is redirected to Monday.com

**GET** `/api/monday/oauth/callback`
- OAuth callback (automatic)
- Exchanges code for token
- Redirects to success page

### Data Sync

**GET** `/api/monday/sync/boards`
- Get all boards for authenticated user
- Returns: user info + board list

**GET** `/api/monday/sync/board/<board_id>`
- Get all items and columns in a board
- Used to fetch schedule data

**POST** `/api/monday/sync/analyze/<board_id>`
- Run schedule analysis on board
- Integrates with Phase 16 analyzer
- Returns risk scores and recommendations

### Webhooks

**POST** `/api/monday/webhook/events`
- Receives real-time events from Monday.com
- Events: `item.created`, `item.updated`, `column.updated`
- Triggers automatic re-analysis

### Status

**GET** `/api/monday/status`
- Check if Monday.com is configured
- List authenticated workspaces
- Show available features

**GET** `/api/monday/config`
- Get configuration info
- Used by frontend to discover endpoints

---

## Usage Examples

### Example 1: User Connects Account

```javascript
// User clicks button in React component
// Component calls /api/monday/oauth/start
// Backend returns authorization_url
// User redirected to: 
//   https://auth.monday.com/oauth2/authorize?client_id=...&redirect_uri=...

// User grants permission
// Redirected back to callback
// Token stored securely
// User sees "Connected!" message
```

### Example 2: Analyze Board Schedule

```bash
# Frontend: User selects board
# Calls: POST /api/monday/sync/analyze/{board_id}
# 
# Backend does:
# 1. Fetch all items from board via GraphQL
# 2. Extract schedule data (dates, durations)
# 3. Pass to Phase 16 ScheduleDependencyAnalyzer
# 4. Calculate critical path and risks
# 5. Update board items with risk scores
# 6. Return summary to frontend
```

### Example 3: Real-Time Updates

```
Monday.com user updates a task status
    ↓
Monday.com sends webhook to /api/monday/webhook/events
    ↓
Backend validates signature
    ↓
Triggers re-analysis of schedule
    ↓
Results pushed back to Monday.com
    ↓
User sees updated risk scores in board
```

---

## Integration with Phase 16

The Monday.com integration seamlessly integrates with Phase 16 (Schedule Dependencies):

```python
# When analyzing board:
from backend.ml.schedule_analyzer import ScheduleDependencyAnalyzer

analyzer = ScheduleDependencyAnalyzer()

# Convert Monday.com items to Task objects
for item in items:
    task = Task(
        task_id=item['id'],
        name=item['name'],
        duration_days=extract_duration(item),  # From Monday.com column
        dependencies=extract_dependencies(item)  # From Monday.com links
    )
    analyzer.add_task(task)

# Calculate critical path
cp = analyzer.calculate_critical_path()

# Push results back to Monday.com
for task in analyzer.tasks:
    api.update_item_column(
        item_id=task.task_id,
        column_id='risk_score_column_id',
        value=str(task.risk_score)
    )
```

---

## Security Considerations

### Token Storage

Tokens are stored securely:

```python
# DO: Encrypted in database
token = MondayToken(
    workspace_id=workspace_id,
    access_token=encrypted_token,  # AES-256 encrypted
    expires_at=expires_at,
    user_id=user_id
)
db.session.add(token)
db.session.commit()

# DON'T: Expose in logs
logger.info(f"Token: {token}")  # NEVER!

# DON'T: Send in response
return jsonify({"token": access_token})  # NEVER!
```

### Webhook Validation

All incoming webhooks are validated with HMAC-SHA256:

```python
# Monday.com signs with client secret
signature = request.headers.get('X-Monday-Signature')

# Backend validates
expected = hmac.new(
    client_secret.encode(),
    request.data,
    hashlib.sha256
).hexdigest()

if not hmac.compare_digest(expected, signature):
    return 401  # Reject unsigned requests
```

### API Key Management

- ✅ OAuth - No API keys exposed to users
- ✅ Tokens encrypted at rest
- ✅ Tokens automatically refreshed
- ✅ User can revoke access anytime
- ✅ No token sharing between users

---

## Deployment

### Development

```bash
# Start backend with Monday.com integration
python run_server.py

# Backend available at: http://localhost:5000
# OAuth callback: http://localhost:5000/api/monday/oauth/callback
```

### Production (Docker)

```dockerfile
# Add to backend/Dockerfile
RUN pip install requests

# Add environment variables
ENV MONDAY_OAUTH_CLIENT_ID=${MONDAY_OAUTH_CLIENT_ID}
ENV MONDAY_OAUTH_CLIENT_SECRET=${MONDAY_OAUTH_CLIENT_SECRET}
ENV MONDAY_OAUTH_REDIRECT_URI=https://your-domain.com/api/monday/oauth/callback
```

```bash
# Deploy with docker-compose
docker-compose -f docker-compose.prod.yml up
```

### AWS/Cloud Deployment

```bash
# Set environment variables in cloud platform:
# - MONDAY_OAUTH_CLIENT_ID
# - MONDAY_OAUTH_CLIENT_SECRET
# - MONDAY_OAUTH_REDIRECT_URI (must be your prod domain)

# Update Monday.com app settings:
# - Redirect URI: https://your-api-domain.com/api/monday/oauth/callback
```

---

## Troubleshooting

### Issue: "Monday.com app not configured"

**Cause**: Missing OAuth credentials in environment

**Solution**:
```bash
# Check environment variables
echo $MONDAY_OAUTH_CLIENT_ID

# If empty, add to .env:
MONDAY_OAUTH_CLIENT_ID=your_id
MONDAY_OAUTH_CLIENT_SECRET=your_secret

# Restart application
```

### Issue: OAuth redirect fails

**Cause**: Redirect URI mismatch between app config and environment

**Solution**:
1. Go to Monday.com developer portal
2. Check "Redirect URI" setting
3. Ensure it matches `MONDAY_OAUTH_REDIRECT_URI` in `.env`
4. For development, use: `http://localhost:5000/api/monday/oauth/callback`

### Issue: Cannot update board items

**Cause**: App doesn't have `items:write` scope

**Solution**:
1. Go to Monday.com app settings
2. Add `items:write` to scopes
3. User must re-authorize (revoke and reconnect)

### Issue: Webhooks not firing

**Cause**: Webhook not registered or signature validation failing

**Solution**:
```bash
# Check webhook registration
curl http://localhost:5000/api/monday/status

# Enable debug logging
export MONDAY_LOG_LEVEL=DEBUG

# Verify webhook signature validation in logs
```

---

## Feature Roadmap

### Phase 17.1: Advanced Analytics
- [ ] Predictive risk scoring from historical data
- [ ] Team collaboration tracking
- [ ] Budget integration with construction costs

### Phase 17.2: Mobile App
- [ ] Monday.com mobile view support
- [ ] Push notifications for risk alerts
- [ ] Offline board view

### Phase 17.3: Automation
- [ ] Automatic alerts when risks detected
- [ ] Auto-escalation to project managers
- [ ] Integration with Slack/Teams

---

## Support & Documentation

- **Developer Portal**: https://developer.monday.com/
- **API Reference**: https://monday.com/developers/v2
- **GitHub Issues**: Report bugs in construction-ai-suite repo
- **Community**: Join Monday.com developer community

---

## Version

**Phase 17 - Version 1.0**  
Released: 2024  
Status: Production Ready  
OAuth-Based: ✅  
No Manual API Keys: ✅  

---

**Next Steps**: 
1. Set up OAuth credentials on Monday.com developer portal
2. Configure environment variables
3. Test OAuth flow locally
4. Deploy to production
5. Publish app to Monday.com app store (optional)
