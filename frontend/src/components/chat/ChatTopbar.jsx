import React from "react";

function ChatTopbar({
    setSidebarOpen,
    setDocsOpen,
    isAuthenticated,
    handleLogout,
}) {
    return (
        <header className="chat-topbar">

            <button
                className="icon-btn"
                onClick={() => setSidebarOpen(true)}
            >
                ☰
            </button>

            <div className="brand">

                <div className="brand-logo">
                    AI
                </div>

                <span>
                    Knowledge Assistant
                </span>

            </div>

            <div className="topbar-right-actions">
                {isAuthenticated && (
                    <button
                        className="topbar-logout-btn"
                        onClick={handleLogout}
                    >
                        Logout
                    </button>
                )}

                <button
                    className="icon-btn"
                    onClick={() => setDocsOpen(true)}
                >
                    📁
                </button>
            </div>

        </header>
    );
}

export default ChatTopbar;