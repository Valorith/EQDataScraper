// Web Worker for handling heavy authentication operations
// This helps prevent the main UI thread from becoming unresponsive

self.addEventListener('message', async (event) => {
  const { type, payload } = event.data;
  
  try {
    switch (type) {
      case 'VERIFY_TOKEN':
        const verifyResult = await verifyTokenInWorker(payload);
        self.postMessage({ type: 'VERIFY_TOKEN_RESULT', payload: verifyResult });
        break;
        
      case 'REFRESH_TOKEN':
        const refreshResult = await refreshTokenInWorker(payload);
        self.postMessage({ type: 'REFRESH_TOKEN_RESULT', payload: refreshResult });
        break;
        
      case 'PARSE_JWT':
        const parseResult = parseJWT(payload.token);
        self.postMessage({ type: 'PARSE_JWT_RESULT', payload: parseResult });
        break;
        
      default:
        self.postMessage({ type: 'ERROR', payload: 'Unknown operation type' });
    }
  } catch (error) {
    self.postMessage({ 
      type: 'ERROR', 
      payload: { 
        message: error.message,
        operation: type 
      }
    });
  }
});

// Parse JWT token without external dependencies
function parseJWT(token) {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) {
      throw new Error('Invalid JWT format');
    }
    
    const payload = JSON.parse(atob(parts[1]));
    const exp = payload.exp * 1000; // Convert to milliseconds
    const isExpired = Date.now() >= exp;
    
    return {
      payload,
      isExpired,
      expiresIn: exp - Date.now()
    };
  } catch (error) {
    throw new Error('Failed to parse JWT: ' + error.message);
  }
}

// Verify token with the backend (simplified for worker context)
async function verifyTokenInWorker(payload) {
  const { token, apiBaseUrl } = payload;
  
  try {
    const response = await fetch(`${apiBaseUrl}/api/auth/verify`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ token })
    });
    
    if (!response.ok) {
      return { valid: false, status: response.status };
    }
    
    const data = await response.json();
    return { valid: true, user: data.user };
  } catch (error) {
    return { valid: false, error: error.message };
  }
}

// Refresh token with the backend
async function refreshTokenInWorker(payload) {
  const { refreshToken, apiBaseUrl } = payload;
  
  try {
    const response = await fetch(`${apiBaseUrl}/api/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ refresh_token: refreshToken })
    });
    
    if (!response.ok) {
      return { success: false, status: response.status };
    }
    
    const data = await response.json();
    return { 
      success: true, 
      accessToken: data.access_token,
      refreshToken: data.refresh_token,
      user: data.user
    };
  } catch (error) {
    return { success: false, error: error.message };
  }
}