import React from "react";
import "../assets/styles/Landing.css";
import { Link } from 'react-router-dom';

function Landing() {
  return (
    <div className="landing">
      {/* Navbar */}
      <header className="navbar">
        <div className="navbar-container">
          <div className="brand">
            <div className="brand-logo">AI</div>
            <span className="brand-name">Knowledge Assistant</span>
          </div>

          <nav className="nav-links">
            <a href="#features">Features</a>
            <a href="#how-it-works">How it works</a>
            <a href="#faq">FAQ</a>
          </nav>

          <div className="nav-actions">
            <button className="btn btn-ghost">Sign in</button>
            <button className="btn btn-primary">Get started</button>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="hero">
        <div className="hero-badge">
          AI-powered • Ask questions across your documents instantly
        </div>

        <h1>
          Your personal <span>AI Knowledge Assistant</span>
        </h1>

        <p>
          Upload documents, manuals, notes, and reports. Ask questions in
          natural language and get accurate answers grounded in your own
          knowledge base.
        </p>

        <div className="hero-actions">
          <Link to="/chat"><button className="btn btn-primary">Try it free</button></Link>
          <button className="btn btn-secondary">Watch demo</button>
        </div>

        {/* Demo card */}
        <div className="demo-card">
          <div className="window-dots">
            <div className="dot red"></div>
            <div className="dot yellow"></div>
            <div className="dot green"></div>
          </div>

          <div className="chat-bubble chat-user">
            <p className="chat-title">You</p>
            <p>
              “Summarize the key points from the uploaded API documentation.”
            </p>
          </div>

          <div className="chat-bubble chat-ai">
            <p className="chat-title">Knowledge Assistant</p>
            <p>
              “Here are the five most important endpoints, authentication rules,
              rate limits, and common integration pitfalls extracted from your
              documents.”
            </p>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="section">
        <div className="section-header">
          <h2>Everything you need to work with knowledge</h2>
          <p>Built for students, researchers, developers, and teams.</p>
        </div>

        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">📄</div>
            <h3>Document Q&A</h3>
            <p>
              Ask questions across PDFs, Word files, notes, and reports.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">🔍</div>
            <h3>Semantic Search</h3>
            <p>
              Find relevant information even when exact keywords are missing.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">⚡</div>
            <h3>Instant Summaries</h3>
            <p>
              Generate concise summaries, action items, and study notes in
              seconds.
            </p>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="how-section">
        <div className="section">
          <div className="section-header">
            <h2>How it works</h2>
            <p>From upload to answer in three simple steps.</p>
          </div>

          <div className="steps">
            <div className="step">
              <div className="step-number">1</div>
              <h3>Upload</h3>
              <p>Add your PDFs, notes, manuals, or research papers.</p>
            </div>

            <div className="step">
              <div className="step-number">2</div>
              <h3>Ask</h3>
              <p>Ask questions in plain English.</p>
            </div>

            <div className="step">
              <div className="step-number">3</div>
              <h3>Get Answers</h3>
              <p>Receive grounded answers with source-backed context.</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="cta">
        <h2>Ready to build your private AI knowledge base?</h2>
        <p>
          Start asking questions across your documents in less than a minute.
        </p>
        <button className="btn">Start for free</button>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div className="footer-container">
          <p>© 2026 Knowledge Assistant. All rights reserved.</p>

          <div className="footer-links">
            <a href="#">Privacy</a>
            <a href="#">Terms</a>
            <a href="#">Contact</a>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default Landing;