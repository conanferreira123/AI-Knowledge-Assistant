const API_BASE = 'http://127.0.0.1:8000/api';

export async function apiRequest(endpoint, options = {}) {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    credentials: 'include',
    ...options,
  });

  let data = {};

  try {
    data = await response.json();
  } catch {
    // response had no JSON body
  }

  if (!response.ok) {
    throw new Error(data.message || 'Request failed');
  }

  return data;
}

export async function uploadDocument(conversationId=1, file) {
  const formData = new FormData();  //FormData is a built-in js object that helps the browser send files and form fields in the same HTTP request.
  formData.append('file', file);
  formData.append('title', file.name);
  formData.append('file_type', file.type);

  return apiRequest(
    `/conversations/${conversationId}/upload/`,
    {
      method: 'POST',
      body: formData,
    }
  );
}

export async function sendChatMessage(conversationId, message) {
  const response = await fetch(
    `${API_BASE}/conversations/${conversationId}/chat/`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({ message }),
    }
  );

  const data = await response.json();
  console.log(data)
  if (!response.ok) {
    throw new Error(data.message || 'Chat request failed');
  }

  return data;
}


export async function apiCreateConversation() {
  return apiRequest('/conversations/create/', {
    method: 'POST',
  });
}

export async function apiListConversations() {
  return apiRequest('/conversations/', {
    method: 'GET',
  });
}

export async function apiConversationHistory(conversationId) {
  return apiRequest(
    `/conversations/${conversationId}/history/`,
    {
      method: 'GET',
    }
  );
}