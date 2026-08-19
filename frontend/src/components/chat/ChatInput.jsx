import React from "react";

function ChatInput({
    prompt,
    setPrompt,
    handleSend,
    disabled,
}) {
    return (
        <div className="chat-input-wrapper">

            <div className="chat-input-bar">

                <textarea
                    placeholder="Ask a question about your documents..."
                    value={prompt}
                    onChange={(e) =>
                        setPrompt(e.target.value)
                    }
                    rows={1}
                    disabled={disabled}
                />

                <button
                    className="send-btn"
                    onClick={handleSend}
                    disabled={disabled}
                >
                    ➤
                </button>

            </div>

        </div>
    );
}

export default ChatInput;