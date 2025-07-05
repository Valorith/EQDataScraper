# Local OAuth Testing Guide

## Setup Complete ✅

The OAuth system is now ready for local testing! Here's what's configured:

### Backend (Port 5001)
- ✅ OAuth routes enabled at `http://localhost:5001/api/auth/*`
- ✅ Google OAuth client configured
- ✅ Database tables created for users
- ✅ JWT authentication working
- ✅ Rate limiting applied

### Frontend (Port 3005)
- ✅ OAuth components loaded (GoogleAuthButton, UserMenu)
- ✅ User store with state persistence
- ✅ OAuth callback route `/auth/callback`

## Testing Steps

### 1. Access the Application
Open your browser and go to: **http://localhost:3005**

You should see:
- The familiar EQDataScraper interface
- A "Sign in with Google" button in the top-right corner

### 2. Test OAuth Login Flow

1. **Click "Sign in with Google"** button
   - Should redirect you to Google's OAuth consent screen
   - Google will ask you to sign in and grant permissions

2. **Complete Google Authorization**
   - Sign in with your Google account
   - Grant permissions for email and profile access
   - Google will redirect back to: `http://localhost:3005/auth/callback`

3. **Verify Successful Login**
   - Should see a success page briefly
   - Then redirect to the main app
   - The "Sign in with Google" button should be replaced with your user avatar/menu

### 3. Test User Features

After successful login:

1. **User Menu**
   - Click your avatar in the top-right
   - Should see dropdown with Profile, Preferences, and Sign out options

2. **Profile Page**
   - Navigate to `/profile` or click "Profile" in user menu
   - Should show your Google profile information

3. **Preferences Page**
   - Navigate to `/preferences` or click "Preferences" in user menu
   - Should allow you to set default class, theme, and results per page

4. **Logout**
   - Click "Sign out" in the user menu
   - Should return to anonymous state with "Sign in with Google" button

### 4. Test Data Persistence

1. **Login and Set Preferences**
   - Login with Google
   - Set some preferences (default class, theme)
   - Logout

2. **Verify Persistence**
   - Login again
   - Your preferences should be preserved

3. **Test Browser Session**
   - Login and close browser
   - Reopen browser and go to the app
   - Should still be logged in (token persistence)

## What to Look For

### ✅ Success Indicators
- Smooth redirect to Google OAuth
- Successful callback handling
- User avatar appears after login
- Profile information displays correctly
- Preferences save and persist
- Logout clears authentication state

### ❌ Potential Issues
- **Redirect URI mismatch**: Check browser console for errors
- **CORS errors**: Backend should allow `http://localhost:3005`
- **Token errors**: Check if JWT tokens are being created correctly
- **Database errors**: User tables should be accessible

## Troubleshooting

### If OAuth Fails
1. Check browser console for JavaScript errors
2. Check backend logs: `tail -f backend/backend.log`
3. Verify Google Cloud Console redirect URI includes: `http://localhost:3005/auth/callback`

### If Database Errors Occur
```bash
cd backend
python3 run_migration.py --check
```

### If Ports Conflict
- Frontend runs on first available port (3005, 3006, etc.)
- Update backend `.env` file with correct redirect URI
- Restart backend after changing redirect URI

## API Endpoints Available

- `GET /api/auth/google/login` - Start OAuth flow
- `POST /api/auth/google/callback` - Complete OAuth flow
- `GET /api/auth/status` - Check authentication status
- `GET /api/user/profile` - Get user profile
- `PUT /api/user/preferences` - Update user preferences
- `POST /api/auth/logout` - Logout user

## Environment Files Created

- `backend/.env` - Backend OAuth configuration
- `.env` - Frontend OAuth configuration
- Both files are gitignored for security

## Next Steps

After successful local testing:
1. Add any final features or improvements
2. Update Google Cloud Console with production redirect URIs
3. Deploy to Railway with environment variables
4. Test production OAuth flow

## Reset Instructions

To reset the OAuth system completely:
```bash
cd backend
python3 run_migration.py --rollback
rm .env
cd ..
rm .env
git checkout master
git branch -D feature/oauth-user-accounts
```

This will remove all user data and OAuth configuration, returning to the original state.