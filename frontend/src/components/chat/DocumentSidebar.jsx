import React from "react";

function DocumentsSidebar({
    docsOpen,
    setDocsOpen,
    uploadedDocs,
    handleUpload,
}) {
    return (
        <aside
            className={`docs-sidebar ${
                docsOpen ? "open" : ""
            }`}
        >

            <div className="docs-header">

                <h3>
                    Uploaded Documents
                </h3>

                <div className="documents-header">

                    <label className="upload-btn">

                        +Upload

                        <input
                            type="file"
                            hidden
                            onChange={handleUpload}
                        />

                    </label>

                </div>

                <button
                    className="icon-btn"
                    onClick={() =>
                        setDocsOpen(false)
                    }
                >
                    ✕
                </button>

            </div>

            {uploadedDocs.length === 0 ? (

                <div className="empty-docs">

                    <p>
                        No documents uploaded yet.
                    </p>

                </div>

            ) : (

                <div className="docs-list">

                    {uploadedDocs.map((doc, index) => (

                        <button
                            key={index}
                            className="doc-item"
                        >

                            <div className="doc-icon">
                                📄
                            </div>

                            <div className="doc-info">

                                <span className="doc-name">
                                    {doc.name}
                                </span>

                                <span className="doc-size">
                                    {doc.size} KB
                                </span>

                            </div>

                        </button>

                    ))}

                </div>

            )}

        </aside>
    );
}

export default DocumentsSidebar;