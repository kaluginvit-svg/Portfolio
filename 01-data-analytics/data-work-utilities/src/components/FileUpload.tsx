import React, { useRef } from 'react';

interface FileUploadProps {
  onFileSelect: (file: File) => void;
}

export const FileUpload: React.FC<FileUploadProps> = ({ onFileSelect }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      onFileSelect(file);
    }
  };

  const handleLabelClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <section className="upload-section">
      <div className="upload-box">
        <input
          ref={fileInputRef}
          type="file"
          className="upload-input"
          accept=".xlsx,.xls,.csv,.pdf"
          onChange={handleFileChange}
        />
        <label htmlFor="fileInput" className="upload-label" onClick={handleLabelClick}>
          <span className="upload-icon">📁</span>
          <span>Выберите файл (CSV, xlsx, xls или PDF)</span>
        </label>
      </div>
    </section>
  );
};
