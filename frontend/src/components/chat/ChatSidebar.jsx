import React, { useState, useEffect, useRef } from "react";

function ChatSidebar({
    sidebarOpen,
    setSidebarOpen,
    conversations,
    createConversation,
    openConversation,
    isAuthenticated,
    user,
    handleLogout,
}) {
    const [showAccountPopup, setShowAccountPopup] = useState(false);
    const accountRef = useRef(null);

    useEffect(() => {
        function handleClickOutside(event) {
            if (accountRef.current && !accountRef.current.contains(event.target)) {
                setShowAccountPopup(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, []);

    const getInitials = (userObj) => {
        if (!userObj) return "U";
        const fullName =
            userObj.first_name && userObj.last_name
                ? `${userObj.first_name} ${userObj.last_name}`
                : userObj.first_name || userObj.username || userObj.email || "";
        const parts = fullName.trim().split(/[\s_.]+/).filter(Boolean);
        if (parts.length >= 2) {
            return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
        } else if (parts.length === 1 && parts[0].length > 0) {
            return parts[0][0].toUpperCase();
        }
        return "U";
    };

    const displayName =
        user?.first_name && user?.last_name
            ? `${user.first_name} ${user.last_name}`
            : user?.first_name || user?.username || "Account";

    return (
        <aside
            className={`sidebar ${
                sidebarOpen ? "open" : ""
            }`}
        >
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

                    <p
                        style={{
                            padding: "1rem",
                            color: "#64748b",
                        }}
                    >
                        No chats yet.
                    </p>

                ) : (

                    conversations.map((conv) => (

                        <button
                            key={conv.id}
                            className="chat-history-item"
                            onClick={() =>
                                openConversation(conv.id)
                            }
                        >
                            {conv.title}
                        </button>

                    ))

                )}

            </div>

            {isAuthenticated && user && (
                <div className="sidebar-footer" ref={accountRef}>
                    {showAccountPopup && (
                        <div className="account-popup">
                            <div className="account-popup-header">Account</div>
                            <div className="account-popup-name">{displayName}</div>
                            {user.email && (
                                <div className="account-popup-email">{user.email}</div>
                            )}
                            <button
                                className="account-popup-logout"
                                onClick={() => {
                                    setShowAccountPopup(false);
                                    handleLogout();
                                }}
                            >
                                Logout
                            </button>
                        </div>
                    )}

                    <button
                        className="account-btn"
                        onClick={() => setShowAccountPopup((prev) => !prev)}
                    >
                        <span className="account-avatar">
                            {getInitials(user)}
                        </span>
                        <span className="account-label">Account</span>
                    </button>
                </div>
            )}
        </aside>
    );
}

export default ChatSidebar;