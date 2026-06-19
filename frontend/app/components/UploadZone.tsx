"use client";

import { useState, useCallback } from "react";

interface Props {
  onUploadStart: (file: File) => void;
  disabled?: boolean;
}

export default function UploadZone({ onUploadStart, disabled }: Props) {
  const [isDragging, setIsDragging] = useState(false);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      if (disabled) return;

      const file = e.dataTransfer.files[0];
      if (file && file.type === "application/pdf") {
        import("react-hot-toast").then((module) => { module.toast.success("PDF Selected! Initiating upload..."); });
        onUploadStart(file);
      } else {
        alert("Please upload a valid PDF file.");
      }
    },
    [disabled, onUploadStart]
  );

  return (
    <div
      className={`border border-dashed rounded-lg p-4 text-center transition-colors cursor-pointer group
        ${isDragging ? "border-secondary bg-secondary/10" : "border-white/20"}
        ${disabled ? "opacity-50 cursor-not-allowed pointer-events-none" : "hover:border-secondary/50"}
      `}
      onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
      onDragLeave={(e) => { e.preventDefault(); setIsDragging(false); }}
      onDrop={handleDrop}
      onClick={() => {
        if (disabled) return;
        const input = document.createElement("input");
        input.type = "file";
        input.accept = ".pdf";
        input.onchange = (e) => {
          const file = (e.target as HTMLInputElement).files?.[0];
          if (file) {
            import("react-hot-toast").then((module) => { module.toast.success("PDF Selected! Initiating upload..."); });
            onUploadStart(file);
          }
        };
        input.click();
      }}
    >
      {disabled ? (
        <svg className="animate-spin h-6 w-6 text-secondary mb-2 mx-auto" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      ) : (
        <span className="material-symbols-outlined text-on-surface-variant group-hover:text-secondary mb-2 block transition-colors">upload_file</span>
      )}
      <span className="font-label-sm text-label-sm text-on-surface-variant group-hover:text-secondary transition-colors">
        {disabled ? "Uploading & Processing PDF..." : isDragging ? "Drop here!" : "Drop 10-K PDF"}
      </span>
    </div>
  );
}
