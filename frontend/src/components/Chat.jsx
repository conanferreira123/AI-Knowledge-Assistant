import React, { useRef, useState,useEffect } from "react";
import "../assets/styles/Chat.css";
import { uploadDocument, sendChatMessage, apiCreateConversation, apiListConversations, apiConversationHistory, } from '../api/api.js';

function Chat() {
  const initializedRef = useRef(false); //to mount components only once to nullify the effect of ReactStrictMode.
  const [conversationId, setConversationId] = useState(null); 
  const [conversations, setConversations] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [docsOpen, setDocsOpen] = useState(false);
  const [uploadedDocs, setUploadedDocs] = useState([]);
  const [prompt, setPrompt] = useState("");

  // New states
  const [queryCount, setQueryCount] = useState(0);
  const [showLoginGate, setShowLoginGate] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  // Chat history must be state now
  const [messages, setMessages] = useState([]);

  const fileInputRef = useRef(null);

//HandleUpload
const handleUpload = async (e) => {
  const files = Array.from(e.target.files || []);

  if (files.length === 0) return;

  setDocsOpen(true);

  for (const file of files) {
    // optimistic UI item
    const tempId = `${file.name}-${Date.now()}`;

    setUploadedDocs((prev) => [
      ...prev,
      {
        id: tempId,
        name: file.name,
        size: (file.size / 1024).toFixed(1),
        status: 'Uploading...',
      },
    ]);

    try {
      //conversationId=1; // Replace with the actual conversation ID you want to use
      const result = await uploadDocument(conversationId, file);

      setUploadedDocs((prev) =>
        prev.map((doc) =>
          doc.id === tempId
            ? {
                id: result.document.id,
                name: result.document.title,
                size: (file.size / 1024).toFixed(1),
                status: result.document.status,
              }
            : doc
        )
      );
    } catch (err) {
      console.error(err);

      setUploadedDocs((prev) =>
        prev.map((doc) =>
          doc.id === tempId
            ? { ...doc, status: 'Failed' }
            : doc
        )
      );
    }
  }

  // reset file input so the same file can be selected again
  e.target.value = '';
};

//LoadConversations
const loadConversations = async () => {
  try {
    const data = await apiListConversations();
    setConversations(data.conversations || []);
  } catch (err) {
    console.error(err);
  }
};

const createConversation = async () => {
  try {
    const result = await apiCreateConversation();

    await loadConversations();

    // Open the new conversation immediately
    await openConversation(result.id);

    return result;
  } catch (err) {
    console.error(err);
  }
};

//OpenConversation
const openConversation = async (id) => {
  try {
    const data = await apiConversationHistory(id);

    setConversationId(id);
    setMessages(data.messages || []);
    setUploadedDocs(data.documents || []);
  } catch (err) {
    console.error(err);
  }
};

const handleSend = async () => {
  if (!prompt.trim()) return;
  if (!conversationId) {
      console.error('No active conversation selected');
      return;
    }

  const nextCount = queryCount + 1;

  // Show login gate on the 4th query
  if (!isLoggedIn && nextCount > 3) {
    setShowLoginGate(true);
    return;
  }

  const userMessage = {
    id: Date.now(),
    role: 'user',
    content: prompt,
  };

  // Show user message immediately
  setMessages((prev) => [...prev, userMessage]);

  const currentPrompt = prompt;
  setPrompt('');

  try {
    const result = await sendChatMessage(conversationId,currentPrompt);

    const assistantMessage = {
      id: result.message_id,
      role: 'assistant',
      content: result.answer,
      sources: result.sources || [],
    };

    setMessages((prev) => [...prev, assistantMessage]);

    setQueryCount(nextCount);

  } catch (err) {
    console.error(err);

    setMessages((prev) => [
      ...prev,
      {
        id: Date.now() + 1,
        role: 'assistant',
        content: 'Sorry, something went wrong while contacting the server.',
        sources: [],
      },
    ]);
  }
};

//HandleLogin
const handleLogin = () => {
  // Temporary frontend-only login
  if (!email.trim() || !password.trim()) return;

  setIsLoggedIn(true);
  setShowLoginGate(false);

  // Optional: clear guest state after login
  setMessages([]);
  setUploadedDocs([]);
  setQueryCount(0);

  setEmail('');
  setPassword('');

  setSidebarOpen(false);
  setDocsOpen(false);
};

const initializeChat = async () => {
  try {
    const data = await apiListConversations();

    const existing = data.conversations || [];

    setConversations(existing);

    if (existing.length > 0) {
      // Open the most recent conversation
      await openConversation(existing[0].id);
    } else {
      // First visit: create a new conversation
      await createConversation();
    }

  } catch (err) {
    console.error(err);
  }
};

//UseEffect
useEffect(() => {
  if (initializedRef.current) return;   //so that InitializedRef mounts only once

  initializedRef.current = true;

  initializeChat();
}, []);

//Main HTML:
  return (
    <div className="chat-page">
      {/* Left Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? "open" : ""}`}>
        <div className="sidebar-header">
          <button
            className="icon-btn"
            onClick={() => setSidebarOpen(false)}
          >
            ✕
          </button>
          <h3>Chats</h3>
        </div>

        <button
          className="new-chat-btn"
          onClick={createConversation}
        >
          + New Chat
        </button>

        <div className="chat-history">
        {conversations.length === 0 ? (
          <p style={{ padding: '1rem', color: '#64748b' }}>
            No chats yet.
          </p>
        ) : (
          conversations.map((conv) => (
            <button
              key={conv.id}
              className="chat-history-item"
              onClick={() => openConversation(conv.id)}
            >
              {conv.title}
            </button>
          ))
        )}
      </div>
      </aside>

      {/* Main Content */}
      <main className="chat-main">
        {/* Top Bar */}
        <header className="chat-topbar">
          <button
            className="icon-btn"
            onClick={() => setSidebarOpen(true)}
          >
            ☰
          </button>

          <div className="brand">
            <div className="brand-logo">AI</div>
            <span>Knowledge Assistant</span>
          </div>

          <button className="icon-btn" onClick={() => setDocsOpen(true)}>
            📁
          </button>
        </header>

        {/* Login Gate */}
        {showLoginGate && (
          <div className="login-gate">
            <div className="login-card">
              <h2>Login required</h2>
              <p>
                You have used your free queries. Please log in to continue using
                the assistant.
              </p>

              <input
                type="email"
                placeholder="Email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />

              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />

              <button className="login-btn" onClick={handleLogin}>
                Login
              </button>
            </div>
          </div>
        )}

        {/* Center Upload Area */}
        {messages.length===0 &&(<section className="upload-section">
          <div
            className="upload-card"
            onClick={() => fileInputRef.current?.click()}
          >
            <div className="upload-grid">
              <div className="grid-cell"></div>
              <div className="grid-cell"></div>
              <div className="grid-cell"></div>
              <div className="grid-cell"></div>
            </div>

            <div className="upload-icon">⬆️</div>

            <h2>Upload your documents</h2>

            <p>
              Drag & drop PDFs, Word files, notes, or research papers here,
              or click to browse.
            </p>

            <button className="primary-btn">Choose Files</button>

            <input
              ref={fileInputRef}
              type="file"
              multiple
              hidden
              onChange={handleUpload}
            />
          </div>
        </section>)}
        {messages.length > 0 && (
  <section className="chat-messages">
    {messages.map((msg) => (
      <div key={msg.id} className={`message ${msg.role}`}>
        <div className="message-bubble">
          {msg.content}
        </div>

        {msg.role === 'assistant' &&
          msg.sources &&
          msg.sources.length > 0 && (
            <div className="message-sources">
              <strong>Sources:</strong>
              {msg.sources.map((src, idx) => (
                <div key={idx} className="source-item">
                  📄 {src.document_title}
                  {src.page_number
                    ? ` (Page ${src.page_number})`
                    : ''}
                </div>
              ))}
            </div>
          )}
      </div>
    ))}
  </section>
)}
        {/* Chat Input */}
        <div className="chat-input-wrapper">
          <div className="chat-input-bar">
            <textarea
              placeholder="Ask a question about your documents..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={1}
              disabled={showLoginGate}
            />

            <button
              className="send-btn"
              onClick={handleSend}
              disabled={showLoginGate}
            >
              ➤
            </button>
          </div>
        </div>
      </main>

      {/* Right Documents Sidebar */}
      <aside className={`docs-sidebar ${docsOpen ? "open" : ""}`}>
        <div className="docs-header">
          <h3>Uploaded Documents</h3>

          <button className="icon-btn" onClick={() => setDocsOpen(false)}>
            ✕
          </button>
        </div>

        {uploadedDocs.length === 0 ? (
          <div className="empty-docs">
            <p>No documents uploaded yet.</p>
          </div>
        ) : (
          <div className="docs-list">
            {uploadedDocs.map((doc, index) => (
              <button key={index} className="doc-item">
                <div className="doc-icon">📄</div>

                <div className="doc-info">
                  <span className="doc-name">{doc.name}</span>
                  <span className="doc-size">{doc.size} KB</span>
                </div>
              </button>
            ))}
          </div>
        )}
      </aside>
    </div>
  );
}

export default Chat;