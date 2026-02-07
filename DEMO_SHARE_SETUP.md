# AI Construction Suite — Shareable Demo URL Setup

## Overview
This guide creates a public, shareable demo URL for the Phase 2.5 Monday.com integration prototype. Your friend can access the fully functional demo from any browser **without needing credentials or API keys**.

---

## Prerequisites

### 1. Install ngrok (Free Tier)
Download from: https://ngrok.com/download

**Windows:**
```powershell
# Extract ngrok.exe to a folder in your PATH, or run it directly
# Test installation
ngrok --version
```

**macOS/Linux:**
```bash
brew install ngrok
# or download from https://ngrok.com/download
```

### 2. Verify Servers Are Ready
- Backend: `python run_server.py` (runs on port 5000)
- Frontend: `cd frontend && npm run dev` (runs on dynamic port)

---

## Quick Setup (5 minutes)

### Step 1: Find Frontend Port
When you run `npm run dev`, Vite prints the local URL. Note the port (usually 5173, 5174, 5175, or 5176).

For this guide, we'll assume **5176** — adjust if yours is different.

### Step 2: Start Backend Server
```bash
python run_server.py
# Runs on http://127.0.0.1:5000
```

### Step 3: Start Frontend Server
```bash
cd frontend && npm run dev
# Note the port printed (e.g., http://localhost:5176)
```

### Step 4: Configure Frontend Backend URL (Critical!)

The frontend needs to know where the backend API is. For ngrok sharing, this is a **separate URL**.

**Edit `frontend/.env.local`:**

```ini
# When sharing via ngrok, update this to your backend ngrok URL
# Local development (default):
VITE_BACKEND_URL=http://localhost:5000

# For ngrok sharing, change to:
VITE_BACKEND_URL=https://abc123-456.ngrok.io  # Replace with your backend ngrok URL
```

⚠️ **Important:** You'll update this AFTER you start the backend ngrok tunnel (so you have the URL).

### Step 5: Open Two Terminal Tabs for ngrok Tunnels

**Terminal 1 — Tunnel Backend (port 5000):**
```bash
ngrok http 5000
```

You'll see output like:
```
ngrok                                                                   (Ctrl+C to quit)

Session Status                online
Account                       [your-account]
Version                        3.x.x
Region                         us (United States)
Forwarding                     https://abc123-456.ngrok.io -> http://localhost:5000
```

**Copy the forwarding URL:** `https://abc123-456.ngrok.io`

**Now update your `frontend/.env.local`:**
```ini
VITE_BACKEND_URL=https://abc123-456.ngrok.io
```

Then **restart the frontend dev server** in Terminal 2:
```bash
cd frontend && npm run dev
```
(It will hot-reload with the new backend URL)

---

**Terminal 2 — Tunnel Frontend (port 5176, replace with your port):**
```bash
ngrok http 5176
```

You'll see:
```
Forwarding                     https://xyz789-012.ngrok.io -> http://localhost:5176
```

**Copy the forwarding URL:** `https://xyz789-012.ngrok.io`

---

## Share These URLs With Your Friend

Send your friend **both URLs**:

### For Testing the Demo:
1. **Frontend URL:** `https://xyz789-012.ngrok.io`
   - Open this in browser
   - Navigate to `/monday/onboard` to see the onboarding flow
   - Main dashboard at `/`

2. **Backend API Docs** (optional):
   - Backend URL: `https://abc123-456.ngrok.io/monday/health`
   - Boards endpoint: `https://abc123-456.ngrok.io/monday/boards?tenant_id=demo_tenant`

### Instructions for Your Friend:
```
Hi! I've set up a demo of the AI Construction Suite Monday.com integration.

👉 **Demo Link:** https://xyz789-012.ngrok.io/monday/onboard

**What to do:**
1. Open the link above
2. Click "Continue in Demo Mode"
3. Select the "Demo Board"
4. Click "Next: Configure Sync"
5. Select which data to sync
6. Click "Start Integration"
7. See the success screen with demo data synced

No login needed — everything is in demo mode with synthetic data.

**Available endpoints:**
- Frontend: https://xyz789-012.ngrok.io
- Backend Health: https://xyz789-012.ngrok.io:5000/monday/health
- (Just kidding above, ngrok exposes as single URL)

The demo is live for the next 2 hours (or until I stop it).
```

---

## Testing the Demo (Verify Before Sharing)

Open your browser and test:

1. **Frontend loads:** `https://xyz789-012.ngrok.io`
   - Should see the dashboard or onboarding page

2. **Backend responds:** Check browser console → should see no CORS errors

3. **Demo flow works:**
   - Click "Continue in Demo Mode"
   - Board selection works
   - Sync completes successfully

If you see CORS errors, see **Troubleshooting** section below.

---

## How Long Does the Demo URL Last?

**Free ngrok:**
- URLs are **temporary** (change each time you restart ngrok)
- Session lasts **2 hours** before auto-disconnect
- Perfect for quick testing/sharing with friends

**Upgrade to ngrok Pro:**
- Persistent static URLs ($12/month)
- Longer session times
- Good for production staging

---

## Stopping the Demo (Security Important!)

When done testing:

1. **Press `Ctrl+C`** in each ngrok terminal
2. **Stop backend:** Press `Ctrl+C` in backend terminal
3. **Stop frontend:** Press `Ctrl+C` in frontend terminal

The tunnels **close immediately** — no activity after stopping.

---

## Troubleshooting

### Issue: "CORS error in browser"
**Fix:** Add CORS headers to backend. In `backend/app/main.py`:
```python
from flask_cors import CORS
app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from ngrok URLs
```

Then restart backend.

### Issue: "ngrok command not found"
**Fix:** Ensure ngrok is in your PATH or use full path:
```bash
./ngrok http 5000  # or C:\path\to\ngrok.exe http 5000
```

### Issue: "Port already in use"
**Fix:** Find and stop the process using the port:
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :5000
kill -9 <PID>
```

### Issue: "Frontend won't load assets"
**Fix:** This usually means Vite is trying to use localhost. Edit `frontend/vite.config.ts`:
```ts
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',  // Allow external access
    port: 5176
  }
})
```

### Issue: "API calls to localhost (backend errors)"
**Symptoms:** Browser console shows errors like:
- `failed to fetch http://localhost:5000/...`
- Network tab shows requests failing
- Demo flow doesn't work

**Fix:** Update `frontend/.env.local` with the backend ngrok URL:
```ini
# Wrong (localhost not accessible from external):
VITE_BACKEND_URL=http://localhost:5000

# Correct (for ngrok sharing):
VITE_BACKEND_URL=https://abc123-456.ngrok.io
```

Then restart the frontend dev server:
```bash
cd frontend && npm run dev
```

**Verify:** Open browser console (F12) → Network tab → check requests are going to `https://abc123-456.ngrok.io` not `localhost:5000`

### Issue: ".env.local changes not taking effect"
**Fix:** Vite should auto-reload, but if not:
1. Kill frontend dev server (Ctrl+C)
2. Wait 2 seconds
3. Restart: `npm run dev`

Or manually refresh browser (Ctrl+R).

---

## Optional: Deploy to Staging for Persistent URL

For a truly persistent, production-like environment:

1. **Vercel (Frontend):** Deploy React frontend
   ```bash
   npm install -g vercel
   vercel --prod
   ```

2. **Heroku/Railway (Backend):** Deploy Flask backend
   - Set `DEMO_MODE=true` in environment variables

3. **Use services URL in frontend:** Update API base URL to staging backend

See `PHASE_2_5_MONDAY_INTEGRATION.md` for deployment details.

---

## Technical Details: Backend URL Configuration

### Why Two Separate ngrok Tunnels?

When you share a demo:
- **Frontend:** Your friend accesses `https://xyz789-012.ngrok.io` 
- **Backend:** Your friend's browser needs to call the backend API

If the frontend was hardcoded to use `http://localhost:5000`, your friend's browser wouldn't be able to reach it (localhost = their machine, not yours).

**Solution:** Frontend now uses an environment variable `VITE_BACKEND_URL` that you can configure.

### How It Works

1. **Local Development** (default in `.env.local`):
   ```ini
   VITE_BACKEND_URL=http://localhost:5000
   ```
   Frontend on your machine calls the backend on your machine.

2. **Remote Sharing via ngrok**:
   ```ini
   VITE_BACKEND_URL=https://abc123-456.ngrok.io
   ```
   Frontend on the ngrok tunnel calls the backend on its ngrok tunnel.

3. **When You Update `.env.local`**:
   - Vite's dev server detects the change
   - Component re-renders with new URL
   - No page refresh needed (hot reload)

### Files Modified

- `frontend/.env.local` — Environment variables (gitignored, safe for local setup)
- `frontend/src/config/api.ts` — Helper functions to read `VITE_BACKEND_URL`
- `frontend/src/components/MondayOnboarding.tsx` — Uses `buildApiUrl()` instead of hardcoded URLs
- `frontend/src/components/OAuthHandler.tsx` — Uses `buildApiUrl()` helper
- `frontend/src/App.tsx` — Uses `buildApiUrl()` helper

---

## Troubleshooting: Backend URL Issues

```bash
# Terminal 1: Backend
python run_server.py

# Terminal 2: Frontend
cd frontend && npm run dev

# Terminal 3: Tunnel Backend
ngrok http 5000

# Terminal 4: Tunnel Frontend
ngrok http 5176  # (or whatever port your frontend uses)
```

---

## What Your Friend Can Test

✅ **Monday.com Integration Demo:**
- OAuth flow scaffolding
- Board selection with demo data
- Sync configuration UI
- Success screen showing synced items
- Backend API responses in real-time

✅ **AI Construction Suite Dashboard:**
- Main dashboards (mock and live modes)
- Risk scoring and KPIs
- Schedule analysis charts
- AI insights and alerts

✅ **No Real Data Exposure:**
- All demo data is synthetic
- No Monday.com API keys needed
- No real projects affected
- Safe for external testing

---

## Support

If your friend has issues:
1. Check browser console for errors (F12)
2. Verify ngrok URLs are still active
3. Reload the page
4. Contact you for help (URLs expire if ngrok stops!)

---

**Happy demoing! 🚀**
