import React from 'react';
import '../styles/components.css';

function LoadingSpinner({ message = 'Loading...' }) {
  return (
    <div className="loading-overlay">
      <div className="spinner-container">
        <div className="spinner"></div>
        <p>{message}</p>
      </div>
    </div>
  );
}

export default LoadingSpinner;
