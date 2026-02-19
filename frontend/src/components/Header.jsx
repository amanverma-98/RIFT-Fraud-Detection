import React from 'react';
import '../styles/components.css';

function Header({ onReset }) {
  return (
    <header className="header">
      <div className="header-content">
        <div className="logo">
          <div className="logo-icon">🕸️</div>
          <div className="logo-text">
            <h1>RIFT 2026</h1>
            <p>Money Muling Detection Engine</p>
          </div>
        </div>
        <nav className="nav">
          <a href="#" className="nav-link">Documentation</a>
          <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="nav-link">
            GitHub
          </a>
        </nav>
      </div>
    </header>
  );
}

export default Header;
