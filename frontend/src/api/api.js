const API_BASE = 'http://localhost:8000/api';


// ==================================================
// CSRF helper
// ==================================================

function getCookie(name) {
  const cookies = document.cookie.split(';');

  for (const cookie of cookies) {
    const [key, ...valueParts] = cookie.trim().split('=');

    if (key === name) {
      return decodeURIComponent(
        valueParts.join('=')
      );
    }
  }

  return null;
}


// ==================================================
// Generic API request
// ==================================================

export async function apiRequest(
  endpoint,
  options = {}
) {
  const method = (
    options.method || 'GET'
  ).toUpperCase();

  const headers = new Headers(
    options.headers || {}
  );

  /*
   * Django's CSRF middleware requires the CSRF token
   * on state-changing requests.
   *
   * The sessionid cookie is HttpOnly, so JavaScript
   * does NOT read or manually send it.
   *
   * credentials: 'include' causes the browser to
   * automatically send the sessionid cookie.
   */
  if (
    ![
      'GET',
      'HEAD',
      'OPTIONS',
      'TRACE',
    ].includes(method)
  ) {
    const csrfToken = getCookie(
      'csrftoken'
    );

    if (csrfToken) {
      headers.set(
        'X-CSRFToken',
        csrfToken
      );
    }
  }

  const response = await fetch(
    `${API_BASE}${endpoint}`,
    {
      ...options,

      /*
       * IMPORTANT:
       *
       * This allows the browser to send the Django
       * sessionid cookie to localhost:8000.
       */
      credentials: 'include',

      headers,
    }
  );

  let data = {};

  try {
    data = await response.json();
  } catch {
    // Response did not contain JSON.
  }

  if (!response.ok) {

    const error = new Error(
      data.message || 'Request failed'
    );

    /*
     * Preserve useful backend information so
     * Chat.jsx can identify things like:
     *
     * guest_query_limit
     * login_required
     */
    error.status = response.status;
    error.code = data.code;
    error.data = data;

    throw error;
  }

  return data;
}


// ==================================================
// CSRF
// ==================================================

export async function getCSRFToken() {
  return apiRequest(
    '/csrf/',
    {
      method: 'GET',
    }
  );
}


// ==================================================
// Authentication
// ==================================================

export async function apiRegister(
  username,
  email,
  password
) {
  /*
   * Get a CSRF token before the state-changing POST.
   */
  await getCSRFToken();

  return apiRequest(
    '/register/',
    {
      method: 'POST',

      headers: {
        'Content-Type': 'application/json',
      },

      body: JSON.stringify({
        username,
        email,
        password,
      }),
    }
  );
}


export async function apiLogin(
  username,
  password
) {
  /*
   * First ask Django to set the csrftoken cookie.
   */
  await getCSRFToken();

  /*
   * Login creates the Django session.
   *
   * Django returns:
   *
   * Set-Cookie: sessionid=...
   *
   * The browser stores it automatically.
   *
   * JavaScript never receives or stores the
   * session ID.
   */
  return apiRequest(
    '/login/',
    {
      method: 'POST',

      headers: {
        'Content-Type': 'application/json',
      },

      body: JSON.stringify({
        username,
        password,
      }),
    }
  );
}


export async function apiLogout() {
  /*
   * Logout destroys the authenticated Django session.
   */
  return apiRequest(
    '/logout/',
    {
      method: 'POST',
    }
  );
}


export async function apiGetCurrentUser() {
  return apiRequest(
    '/me/',
    {
      method: 'GET',
    }
  );
}


// ==================================================
// Guest session
// ==================================================

export async function apiStartGuestSession() {
  /*
   * Ensure Django has given the browser a CSRF cookie
   * before making the POST request.
   */
  await getCSRFToken();

  /*
   * Django will:
   *
   * 1. Create a session if necessary.
   * 2. Store the guest conversation ID in that session.
   * 3. Store guest_query_count = 0.
   * 4. Create exactly one guest Conversation.
   *
   * The sessionid itself remains inside an HttpOnly
   * cookie and is never stored by React.
   */
  return apiRequest(
    '/guest/start/',
    {
      method: 'POST',
    }
  );
}


// ==================================================
// Documents
// ==================================================

export async function uploadDocument(
  conversationId,
  file
) {
  const formData = new FormData();

  formData.append(
    'file',
    file
  );

  formData.append(
    'title',
    file.name
  );

  formData.append(
    'file_type',
    file.type
  );

  return apiRequest(
    `/conversations/${conversationId}/upload/`,
    {
      method: 'POST',
      body: formData,
    }
  );
}


// ==================================================
// Chat
// ==================================================

export async function sendChatMessage(
  conversationId,
  message
) {
  return apiRequest(
    `/conversations/${conversationId}/chat/`,
    {
      method: 'POST',

      headers: {
        'Content-Type': 'application/json',
      },

      body: JSON.stringify({
        message,
      }),
    }
  );
}


// ==================================================
// Conversations
// ==================================================

export async function apiCreateConversation() {
  /*
   * Authenticated users can create conversations.
   *
   * Guests will receive:
   *
   * HTTP 403
   * code = "login_required"
   *
   * Django enforces this rule.
   */
  return apiRequest(
    '/conversations/create/',
    {
      method: 'POST',
    }
  );
}


export async function apiListConversations() {
  return apiRequest(
    '/conversations/',
    {
      method: 'GET',
    }
  );
}


export async function apiConversationHistory(
  conversationId
) {
  return apiRequest(
    `/conversations/${conversationId}/history/`,
    {
      method: 'GET',
    }
  );
}