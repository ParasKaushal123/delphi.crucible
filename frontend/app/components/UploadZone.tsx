"use client";

import { useState, useRef, useCallback } from "react";

interface UploadZoneProps {
  onUploadStart: (companyName: string) => void;
  disabled?: boolean;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function UploadZone({ onUploadStart, disabled }: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [companyName, setCompanyName] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    async (file: File) => {
      if (!file.name.toLowerCase().endsWith(".pdf")) {
        setError("Only PDF files are supported.");
        return;
      }
      if (file.size > 50 * 1024 * 1024) {
        setError("File too large. Maximum 50MB.");
        return;
      }

      setError(null);
      setIsUploading(true);

      const formData = new FormData();
      formData.append("file", file);
      formData.append("company_name", companyName.trim());

      try {
        const resp = await fetch(`${API_BASE}/api/analyze/upload`, {
          method: "POST",
          body: formData,
        });

        if (!resp.ok) {
          const err = await resp.json();
          throw new Error(err.detail || "Upload failed");
        }

        const data = await resp.json();
        const name = data.company_name || companyName || file.name.replace(".pdf", "");
        setIsUploading(false);   // ← clears spinner before handing off
        onUploadStart(name);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Upload failed. Please try again.");
        setIsUploading(false);
      }
    },
    [companyName, onUploadStart]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };
  const handleDragLeave = () => setIsDragging(false);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  return (
    <div className="upload-zone-wrapper">
      {/* Optional company name override */}
      <input
        type="text"
        className="upload-company-input"
        placeholder="Company name (optional — we'll detect it)"
        value={companyName}
        onChange={(e) => setCompanyName(e.target.value)}
        disabled={disabled || isUploading}
        id="upload-company-name"
      />

      {/* Drop zone */}
      <div
        className={`upload-dropzone ${isDragging ? "dragging" : ""} ${isUploading ? "uploading" : ""}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => !disabled && !isUploading && fileInputRef.current?.click()}
        role="button"
        aria-label="Upload 10-K PDF"
        id="upload-dropzone"
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          style={{ display: "none" }}
          onChange={handleInputChange}
          disabled={disabled || isUploading}
          id="upload-file-input"
        />

        {isUploading ? (
          <>
            <div className="upload-spinner" />
            <span className="upload-label">Extracting PDF text...</span>
          </>
        ) : isDragging ? (
          <>
            <span className="upload-icon">📂</span>
            <span className="upload-label">Drop to analyze</span>
          </>
        ) : (
          <>
            <span className="upload-icon">📄</span>
            <span className="upload-label">
              Drop 10-K PDF here <span className="upload-or">or click to browse</span>
            </span>
          </>
        )}
      </div>

      {error && <div className="upload-error">{error}</div>}
    </div>
  );
}
