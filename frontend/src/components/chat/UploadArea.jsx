import React from "react";

function UploadArea({
    messages,
    fileInputRef,
    handleUpload,
}) {
    if (messages.length !== 0) {
        return null;
    }

    return (
        <section className="upload-section">

            <div
                className="upload-card"
                onClick={() =>
                    fileInputRef.current?.click()
                }
            >

                <div className="upload-grid">

                    <div className="grid-cell"></div>
                    <div className="grid-cell"></div>
                    <div className="grid-cell"></div>
                    <div className="grid-cell"></div>

                </div>

                <div className="upload-icon">
                    ⬆️
                </div>

                <h2>
                    Upload your documents
                </h2>

                <p>
                    Drag & drop PDFs, Word files,
                    notes, or research papers here,
                    or click to browse.
                </p>

                <button className="primary-btn">
                    Choose Files
                </button>

                <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    hidden
                    onChange={handleUpload}
                />

            </div>

        </section>
    );
}

export default UploadArea;