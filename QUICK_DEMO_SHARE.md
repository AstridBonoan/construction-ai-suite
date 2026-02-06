# Quick Demo Share Checklist

## Pre-Launch Checklist ✓

- [ ] ngrok installed and authenticated (`ngrok authtoken <token>`)
- [ ] Both services running in background (or ready to start)
- [ ] Friend has received the Demo Share URL
- [ ] Demo Share URL is the FRONTEND URL with `/monday/onboard` path
- [ ] Backend ngrok URL updated in `frontend/.env.local` (see "Critical Setup" below)

## Critical Setup: Backend URL Configuration

**⚠️ IMPORTANT:** Your friend's browser needs to know where the backend is!

### For Local Testing (your machine only):
```powershell
# frontend/.env.local already defaults to:
VITE_BACKEND_URL=http://localhost:5000
```
No changes needed.

### For ngrok Demo (sharing with friend):

**1. After starting backend ngrok tunnel, copy the URL**
```
# Example output from: ngrok http 5000
# Forwarding    https://abc123def456.ngrok.io -> http://localhost:5000
# ↑ Copy this part ↑
```

**2. Update the frontend .env.local file:**
```powershell
# Edit: frontend/.env.local
VITE_BACKEND_URL=https://abc123def456.ngrok.io
```

**3. Restart the frontend dev server:**
```powershell
cd frontend
npm run dev
```
The frontend will hot-reload with the new backend URL.

**4. Now share the FRONTEND ngrok URL with your friend:**
```
Frontend URL: https://xyz789uvw012.ngrok.io/monday/onboard
```

## Step-by-Step Launch

### Terminal 1: Backend
```powershell
cd c:\Users\astri\OneDrive\Desktop\construction-ai-suite
python run_server.py
```
✓ Wait for: **"WARNING:root:Phase 23 scheduler..."** (or "Running on http://127.0.0.1:5000")

### Terminal 2: Frontend
```powershell
cd c:\Users\astri\OneDrive\Desktop\construction-ai-suite\frontend
npm run dev
```
✓ Wait for: **"VITE v5.x.x ready in XXXms"** and note the port (usually 5176)

### Terminal 3: Backend Tunnel
```powershell
ngrok http 5000
```
✓ **Copy the HTTPS URL** (e.g., `https://abc123def456.ngrok.io`)
✓ **Update frontend/.env.local with this URL**
✓ **Restart frontend dev server** (npm run dev in Terminal 2)

### Terminal 4: Frontend Tunnel  
```powershell
ngrok http 5176
```
✓ Copy the HTTPS URL (e.g., `https://xyz789uvw012.ngrok.io`)

## Send to Friend

**Email/Message Template:**

---

Hey! Try this demo of the Construction AI Suite Monday.com integration:

**Demo URL:** https://xyz789uvw012.ngrok.io/monday/onboard

**Instructions:**
1. Click the link above
2. Click "Continue in Demo Mode"
3. Select "Demo Board"
4. Click "Next: Configure Sync"
5. Choose what data to sync
6. Click "Start Integration"

Everything is synthetic data - no credentials needed!

*Expires when I close the terminal (usually ~2 hours)*

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| ngrok connection closed | Restart both ngrok tunnels (Terminal 3 & 4) |
| Frontend blank page | Check browser console (F12) for CORS errors; verify .env.local is correct |
| "Cannot find module" error | Both services must be running first |
| Backend URL errors | Update frontend/.env.local with correct ngrok URL and restart frontend |
| Friends can't access URL | ngrok free tier expires after 2 hours - restart tunnels |
| CORS error in browser console | Optional: See DEMO_SHARE_SETUP.md CORS section for backend config|

## Graceful Shutdown

1. Press **Ctrl+C** in Terminal 1 (backend)
2. Press **Ctrl+C** in Terminal 2 (frontend)
3. Press **Ctrl+C** in Terminal 3 (backend tunnel)
4. Press **Ctrl+C** in Terminal 4 (frontend tunnel)
5. All services stop, demo URLs become invalid

## Advanced Options

- **Different frontend port:** `ngrok http 5175` (if 5176 conflicts)
- **Persistent URL:** Upgrade to [ngrok Pro](https://ngrok.com/pricing) ($12/month)
- **Staging deployment:** See PHASE_2_5_MONDAY_INTEGRATION.md

---

**Questions?** Check DEMO_SHARE_SETUP.md for full documentation.
