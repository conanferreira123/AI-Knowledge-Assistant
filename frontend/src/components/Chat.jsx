import React, {
  useRef,
  useState,
  useEffect,
} from "react";

import "../assets/styles/Chat.css";

import {
  uploadDocument,
  sendChatMessage,
  apiCreateConversation,
  apiListConversations,
  apiConversationHistory,
  apiStartGuestSession,
} from "../api/api.js";

import {
  useAuth,
} from "../context/AuthContext.jsx";

import { useNavigate } from "react-router-dom";

// Child components
import ChatSidebar from "./chat/ChatSidebar";
import ChatTopbar from "./chat/ChatTopbar";
import LoginGate from "./chat/LoginGate";
import UploadArea from "./chat/UploadArea";
import MessageList from "./chat/MessageList";
import ChatInput from "./chat/ChatInput";
import DocumentsSidebar from "./chat/DocumentSidebar";


function Chat() {
  const initializedRef = useRef(false);
  const fileInputRef = useRef(null);
  const alertTimeoutRef = useRef(null);

  const navigate = useNavigate();

  // ==================================================
  // State
  // ==================================================

  const [conversationId, setConversationId] =
    useState(null);

  const [conversations, setConversations] =
    useState([]);

  const [sidebarOpen, setSidebarOpen] =
    useState(false);

  const [docsOpen, setDocsOpen] =
    useState(false);

  const [uploadedDocs, setUploadedDocs] =
    useState([]);

  const [uploadAlert, setUploadAlert] =
    useState(null);

  const [prompt, setPrompt] =
    useState("");

  // Guest query tracking
  const [queryCount, setQueryCount] =
    useState(0);

  const [showLoginGate, setShowLoginGate] =
    useState(false);

  // Login form
  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  // Chat history
  const [messages, setMessages] =
    useState([]);


  // ==================================================
  // Authentication
  // ==================================================

  const {
    user,
    loading: authLoading,
    isAuthenticated,
    login,
    logout
  } = useAuth();


  // ==================================================
  // Handle Upload
  // ==================================================

  const handleUpload = async (e) => {
    const files = Array.from(
      e.target.files || []
    );

    if (files.length === 0) return;

    if (!conversationId) {
      console.error(
        "No active conversation selected"
      );
      return;
    }

    setDocsOpen(true);

    if (alertTimeoutRef.current) {
      clearTimeout(alertTimeoutRef.current);
    }
    setUploadAlert({ message: "Uploading...", type: "uploading" });

    let hasError = false;

    for (const file of files) {

      // Optimistic UI item
      const tempId =
        `${file.name}-${Date.now()}`;

      setUploadedDocs((prev) => [
        ...prev,
        {
          id: tempId,
          name: file.name,
          size: (file.size / 1024).toFixed(1),
          status: "Uploading...",
        },
      ]);

      try {

        const result =
          await uploadDocument(
            conversationId,
            file
          );

        setUploadedDocs((prev) =>
          prev.map((doc) =>
            doc.id === tempId
              ? {
                id: result.document.id,
                name: result.document.title,
                size: (
                  file.size / 1024
                ).toFixed(1),
                status:
                  result.document.status,
              }
              : doc
          )
        );

      } catch (err) {

        console.error(err);
        hasError = true;

        setUploadedDocs((prev) =>
          prev.map((doc) =>
            doc.id === tempId
              ? {
                ...doc,
                status: "Failed",
              }
              : doc
          )
        );
      }
    }

    if (hasError) {
      setUploadAlert({ message: "Upload failed! ❌", type: "error" });
      alertTimeoutRef.current = setTimeout(() => {
        setUploadAlert(null);
      }, 4000);
    } else {
      setUploadAlert({ message: "Uploaded! ✅", type: "success" });
      alertTimeoutRef.current = setTimeout(() => {
        setUploadAlert(null);
      }, 3500);
    }

    // Reset file input so the same
    // file can be selected again
    e.target.value = "";
  };


  // ==================================================
  // Load Conversations
  // ==================================================

  const loadConversations = async () => {
    try {

      const data =
        await apiListConversations();

      setConversations(
        data.conversations || []
      );

    } catch (err) {
      console.error(err);
    }
  };

  // ==================================================
  // Create Conversation
  // ==================================================

  const createConversation = async () => {
    // Guest users cannot create another conversation
    if (!isAuthenticated) {
      setShowLoginGate(true);
      return;
    }

    try {
      const result = await apiCreateConversation();

      await loadConversations();
      await openConversation(result.id);

      return result;
    } catch (err) {
      console.error("Create conversation failed:", err);
    }
  };


  // ==================================================
  // Open Conversation
  // ==================================================

  const openConversation = async (id) => {
    try {

      const data =
        await apiConversationHistory(id);

      setConversationId(id);

      setMessages(
        data.messages || []
      );

      setUploadedDocs(
        (data.documents || []).map(
          (doc) => ({
            id: doc.id,
            name: doc.title,
            size: doc.file_size_kb ?? "",
            status: doc.status,
          })
        )
      );

      if (data.query_count !== undefined) {
        setQueryCount(data.query_count);
      }

      setShowLoginGate(false);

    } catch (err) {
      console.error(err);
    }
  };


  // ==================================================
  // Handle Send
  // ==================================================

  const handleSend = async () => {

    if (!prompt.trim()) return;

    if (!conversationId) {
      console.error(
        "No active conversation selected"
      );
      return;
    }

    const userMessage = {
      id: Date.now(),
      role: "user",
      content: prompt,
    };

    // Show user message immediately
    setMessages((prev) => [
      ...prev,
      userMessage,
    ]);

    const currentPrompt = prompt;

    setPrompt("");

    try {

      const result =
        await sendChatMessage(
          conversationId,
          currentPrompt
        );

      const assistantMessage = {
        id: result.message_id,
        role: "assistant",
        content: result.answer,
        sources: result.sources || [],
      };

      setMessages((prev) => [
        ...prev,
        assistantMessage,
      ]);

      // Update sidebar title immediately
      if (result.title) {

        setConversations((prev) =>
          prev.map((conv) =>
            conv.id ===
              result.conversation_id
              ? {
                ...conv,
                title: result.title,
              }
              : conv
          )
        );
      }

      if (result.query_count !== undefined) {
        setQueryCount(result.query_count);
      }

    } catch (err) {

      console.error(err);

      if (
        err.data?.guest_limit_reached ||
        err.status === 403
      ) {
        setShowLoginGate(true);
      }

      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          role: "assistant",
          content:
            err.data?.message ||
            "Sorry, something went wrong while contacting the server.",
          sources: [],
        },
      ]);
    }
  };


  // ==================================================
  // Handle Register
  // ==================================================

  const handleRegister = () => {
    navigate("/register");
  };


  // ==================================================
  // Handle Login
  // ==================================================

  const handleLogin = async () => {

    if (
      !email.trim() ||
      !password.trim()
    ) {
      return;
    }

    try {

      const data = await login(
        email.trim(),
        password
      );

      setShowLoginGate(false);

      setEmail("");
      setPassword("");

      setSidebarOpen(false);
      setDocsOpen(false);

      const listData = await apiListConversations();
      const userConvs = listData.conversations || [];
      setConversations(userConvs);

      const targetId =
        data?.migrated_conversation_id ||
        (userConvs.length > 0 ? userConvs[0].id : null);

      if (targetId) {
        await openConversation(targetId);
      } else {
        await createConversation();
      }

    } catch (err) {

      console.error(
        "Login failed:",
        err
      );
    }
  };

  // ==================================================
  // Handle Logout
  // ==================================================

  const handleLogout = async () => {
    try {
      await logout();

      // Clear current chat UI state
      setConversationId(null);
      setConversations([]);
      setMessages([]);
      setUploadedDocs([]);
      setQueryCount(0);
      setShowLoginGate(false);

      // Close sidebars
      setSidebarOpen(false);
      setDocsOpen(false);

      // Return to landing page
      navigate("/");

    } catch (err) {
      console.error("Logout failed:", err);
    }
  };


  // ==================================================
  // Initialize Chat
  // ==================================================

  const initializeChat = async () => {

    try {

      if (!isAuthenticated) {
        // Guest mode: start/retrieve single guest session
        const guestData = await apiStartGuestSession();

        if (guestData && guestData.conversation_id) {
          setConversations([
            {
              id: guestData.conversation_id,
              title: guestData.title || "New Chat",
            },
          ]);
          setQueryCount(guestData.query_count || 0);
          await openConversation(guestData.conversation_id);
        }
      } else {
        // Authenticated mode: load user's conversations
        const data = await apiListConversations();
        const existing = data.conversations || [];

        setConversations(existing);

        if (existing.length > 0) {
          await openConversation(existing[0].id);
        } else {
          await createConversation();
        }
      }

    } catch (err) {
      console.error("Chat initialization failed:", err);
    }
  };


  // ==================================================
  // Initial Authentication +
  // Chat Initialization
  // ==================================================

  useEffect(() => {

    if (authLoading) {
      return;
    }

    if (initializedRef.current) {
      return;
    }

    initializedRef.current = true;

    initializeChat();

  }, [authLoading]);


  // ==================================================
  // Authentication Loading Screen
  // ==================================================

  if (authLoading) {

    return (
      <div className="chat-page">

        <main className="chat-main">

          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              height: "100%",
            }}
          >
            Loading...
          </div>

        </main>

      </div>
    );
  }


  // ==================================================
  // Main UI
  // ==================================================

  return (
    <div className="chat-page">

      {/* Upload Toast Alert */}
      {uploadAlert && (
        <div className={`upload-toast-alert ${uploadAlert.type}`}>
          <span className="toast-icon">
            {uploadAlert.type === "uploading" && (
              <span className="toast-spinner" />
            )}
            {uploadAlert.type === "success" && "✅"}
            {uploadAlert.type === "error" && "❌"}
          </span>
          <span className="toast-message">{uploadAlert.message}</span>
          <button
            className="toast-close"
            onClick={() => {
              if (alertTimeoutRef.current) clearTimeout(alertTimeoutRef.current);
              setUploadAlert(null);
            }}
            aria-label="Close notification"
          >
            ✕
          </button>
        </div>
      )}

      {/* ========================================= */}
      {/* Left Sidebar */}
      {/* ========================================= */}

      <ChatSidebar
        sidebarOpen={sidebarOpen}
        setSidebarOpen={setSidebarOpen}
        conversations={conversations}
        createConversation={createConversation}
        openConversation={openConversation}
        isAuthenticated={isAuthenticated}
        user={user}
        handleLogout={handleLogout}
      />


      {/* ========================================= */}
      {/* Main Content */}
      {/* ========================================= */}

      <main className="chat-main">

        <ChatTopbar
          setSidebarOpen={setSidebarOpen}
          setDocsOpen={setDocsOpen}
          isAuthenticated={isAuthenticated}
          handleLogout={handleLogout}
        />


        {/* Login Gate */}

        <LoginGate
          showLoginGate={showLoginGate}
          email={email}
          password={password}
          setEmail={setEmail}
          setPassword={setPassword}
          handleLogin={handleLogin}
          handleRegister={handleRegister}
        />


        {/* Upload Area */}

        <UploadArea
          messages={messages}
          fileInputRef={fileInputRef}
          handleUpload={handleUpload}
        />


        {/* Chat Messages */}

        <MessageList
          messages={messages}
        />


        {/* Chat Input */}

        <ChatInput
          prompt={prompt}
          setPrompt={setPrompt}
          handleSend={handleSend}
          disabled={showLoginGate}
        />

      </main>


      {/* ========================================= */}
      {/* Right Documents Sidebar */}
      {/* ========================================= */}

      <DocumentsSidebar
        docsOpen={docsOpen}
        setDocsOpen={setDocsOpen}
        uploadedDocs={uploadedDocs}
        handleUpload={handleUpload}
      />

    </div>
  );
}

export default Chat;