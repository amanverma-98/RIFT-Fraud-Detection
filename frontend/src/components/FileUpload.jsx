import React, { useState } from 'react';
import '../styles/components.css';

function FileUpload({ onUpload, loading }) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = e.dataTransfer.files;
    if (files && files[0]) {
      handleFile(files[0]);
    }
  };

  const handleChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (file) => {
    if (file.name.endsWith('.csv')) {
      setSelectedFile(file);
    } else {
      alert('Please upload a CSV file');
    }
  };

  const handleSubmit = () => {
    if (selectedFile) {
      onUpload(selectedFile);
    }
  };

  return (
    <div className="file-upload">
      <div
        className={`upload-area ${dragActive ? 'active' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          id="file-input"
          onChange={handleChange}
          accept=".csv"
          disabled={loading}
        />
        <label htmlFor="file-input" className="upload-label">
          <div className="upload-icon">📁</div>
          <h3>Drag your CSV file here or click to browse</h3>
          <p>Accepted format: CSV with columns (transaction_id, sender_id, receiver_id, amount, timestamp)</p>
        </label>
      </div>

      {selectedFile && (
        <div className="file-info">
          <div className="file-details">
            <div className="file-icon">✓</div>
            <div>
              <div className="file-name">{selectedFile.name}</div>
              <div className="file-size">{Math.round(selectedFile.size / 1024)} KB</div>
            </div>
          </div>
          <button
            className="btn-upload"
            onClick={handleSubmit}
            disabled={loading}
          >
            {loading ? 'Analyzing...' : 'Analyze Transactions'}
          </button>
        </div>
      )}
    </div>
  );
}

export default FileUpload;
