"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface MemoPanelProps {
  memo: string;
  isVisible: boolean;
}

export default function MemoPanel({ memo, isVisible }: MemoPanelProps) {
  if (!isVisible || !memo) return null;

  return (
    <div className="memo-strip">
      <div className="memo-strip-header">
        <div className="memo-strip-title">
          <span className="memo-icon">📄</span>
          Investment Memo — Final Output
        </div>
        <div className="phase-progress">
          <span className="phase-step complete">✓ Data</span>
          <span className="phase-connector complete" />
          <span className="phase-step complete">✓ Debate</span>
          <span className="phase-connector complete" />
          <span className="phase-step complete">✓ Memo</span>
        </div>
      </div>
      <div className="memo-content">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{memo}</ReactMarkdown>
      </div>
    </div>
  );
}
