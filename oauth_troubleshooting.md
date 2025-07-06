# OAuth Troubleshooting Guide

## Issue: Redirect to Wrong Port After Google Authentication

### Quick Fix Steps:

1. **Clear Browser Data**:
   - Open Chrome DevTools (F12)
   - Go to Application tab
   - Clear all localStorage data for localhost
   - Clear cookies for accounts.google.com
   - Hard refresh the page (Ctrl+Shift+R or Cmd+Shift+R on Mac)

2. **Test OAuth Flow**:
   - Open `test_oauth.html` in your browser
   - Click "Test OAuth Login" 
   - Verify the redirect_uri shows `http://localhost:3000/auth/callback`

3. **Ensure Services on Correct Ports**:
   ```bash
   python3 run.py status
   ```
   - Frontend should be on port 3000
   - Backend should be on port 5001

### Root Causes Fixed:

1. **Backend Configuration**: 
   - Updated CORS to accept multiple localhost ports
   - Made OAuth redirect URI dynamic based on request origin
   - Added fallback for local development without database

2. **Frontend Configuration**:
   - Centralized API configuration in `/src/config/api.js`
   - Removed hardcoded port references

3. **Google OAuth Settings**:
   - Multiple redirect URIs added (ports 3000, 3001, 3002, 3003)
   - Takes 5-10 minutes to propagate

### If Issue Persists:

1. **Check OAuth State**: In browser console, run:
   ```javascript
   localStorage.getItem('userStore')
   ```
   Look for any references to port 3001 and clear if found.

2. **Force Fresh OAuth Flow**:
   - Sign out of Google accounts
   - Clear all browser data for localhost
   - Try incognito/private browsing mode

3. **Verify Backend Response**: The backend now dynamically sets redirect_uri based on the Origin header, so it should always redirect back to the port you're accessing from.

### Current OAuth Flow:
1. Frontend (port 3000) → Backend API (port 5001) → Google OAuth
2. Google OAuth → Frontend callback (port 3000)
3. Frontend → Backend API to exchange code for tokens
4. Backend creates JWT tokens (with database fallback for local dev)

The system is now configured to be tolerant of port conflicts and should work correctly on port 3000.
</content>
</invoke>