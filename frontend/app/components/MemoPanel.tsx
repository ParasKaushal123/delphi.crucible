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
    <div className="w-full glass-window rounded-3xl border border-white/10 p-8 flex flex-col shadow-2xl relative overflow-hidden mt-8 transform transition-all duration-500 hover:border-white/20">
      <div className="flex justify-between items-center mb-6 border-b border-white/10 pb-4">
        <div className="font-display-xl text-sm tracking-widest text-[#f2b98b] uppercase flex items-center gap-2">
          <span className="material-symbols-outlined text-lg">description</span>
          INVESTMENT MEMO — FINAL SYNTHESIS
        </div>
        <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-green-400 bg-green-400/10 px-3 py-1.5 rounded-full">
          <span className="material-symbols-outlined text-sm">check_circle</span>
          Pipeline Complete
        </div>
      </div>
      <div className="prose prose-invert max-w-3xl mx-auto w-full pb-8">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{memo}</ReactMarkdown>
      </div>
    </div>
  );
}
