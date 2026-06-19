"use client";

interface BottomActionBarProps {
  connected: boolean;
  onSimulateCrash: () => void;
  onGenerateMemo: () => void;
  onInvest: () => void;
  isSimulating?: boolean;
  isGenerating?: boolean;
  hasActiveSession?: boolean;
}

export default function BottomActionBar({ 
  connected, 
  onSimulateCrash, 
  onGenerateMemo, 
  onInvest,
  isSimulating,
  isGenerating,
  hasActiveSession
}: BottomActionBarProps) {
  return (
    <div className="fixed bottom-8 left-1/2 -translate-x-1/2 z-50 flex items-center bg-[#2a2a2b] rounded-xl border border-white/10 shadow-2xl px-2 py-1.5 gap-1">
      {/* Invest */}
      <button 
        onClick={onInvest}
        disabled={!hasActiveSession}
        className="flex items-center gap-2 px-4 py-2 hover:bg-white/5 rounded-lg transition-colors border-r border-white/10 pr-6 disabled:opacity-50"
      >
        <span className="material-symbols-outlined text-[#a8a8a8] text-xl">payments</span>
        <span className="text-[11px] font-bold tracking-widest text-[#a8a8a8] uppercase mt-0.5">Invest</span>
      </button>

      {/* Connected Status */}
      <div className={`flex items-center gap-2 px-5 py-2 ml-2 rounded-lg transition-colors ${connected ? 'bg-[#fcfcfc] text-black' : 'bg-red-500/20 text-red-400'}`}>
        <span className="material-symbols-outlined text-xl">{connected ? 'robot_2' : 'power_off'}</span>
        <span className="text-[11px] font-bold tracking-widest uppercase mt-0.5">{connected ? 'Connected' : 'Disconnected'}</span>
      </div>

    </div>
  );
}
