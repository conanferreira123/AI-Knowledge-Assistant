import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

function MessageList({ messages }) {
    if (messages.length === 0) {
        return null;
    }

    return (
        <section className="chat-messages">

            {messages.map((msg) => (

                <div
                    key={msg.id}
                    className={`message ${msg.role}`}
                >

                    <div className="message-bubble">

                        {msg.role === "assistant" ? (

                            <ReactMarkdown
                                remarkPlugins={[remarkGfm]}
                            >
                                {msg.content}
                            </ReactMarkdown>

                        ) : (

                            msg.content

                        )}

                    </div>

                    {msg.role === "assistant" &&
                        msg.sources &&
                        msg.sources.length > 0 && (

                            <div className="message-sources">

                                <strong>
                                    Sources:
                                </strong>

                                {msg.sources.map(
                                    (src, idx) => (

                                        <div
                                            key={idx}
                                            className="source-item"
                                        >
                                            📄{" "}
                                            {src.document_title}

                                            {src.page_number
                                                ? ` (Page ${src.page_number})`
                                                : ""}
                                        </div>

                                    )
                                )}

                            </div>

                        )}

                </div>

            ))}

        </section>
    );
}

export default MessageList;