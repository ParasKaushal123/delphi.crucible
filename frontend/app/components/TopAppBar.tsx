"use client";
import { useState, useEffect } from "react";
import ProfileModal from "./ProfileModal";
import Link from "next/link";

interface TopAppBarProps {
  connected?: boolean;
}

export default function TopAppBar({ connected }: TopAppBarProps) {
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [isFirstVisit, setIsFirstVisit] = useState(false);

  useEffect(() => {
    const hasVisited = localStorage.getItem("delphi_has_visited");
    if (!hasVisited) {
      setIsFirstVisit(true);
      setIsProfileOpen(true);
    }
  }, []);

  const handleProfileClose = () => {
    setIsProfileOpen(false);
    if (isFirstVisit) {
      localStorage.setItem("delphi_has_visited", "true");
      setIsFirstVisit(false);
    }
  };

  return (
    <>
      <ProfileModal isOpen={isProfileOpen} onClose={handleProfileClose} isFirstVisit={isFirstVisit} />
      <header className="fixed top-0 left-0 flex justify-between items-center w-full px-12 py-4 z-50 bg-gradient-to-b from-black/80 to-transparent">
        <div className="flex items-center gap-4">
          <span className="font-display-xl text-2xl uppercase tracking-tighter text-[#fefef7]">
            Delphi Crucible
          </span>
        </div>
        <nav className="hidden md:flex gap-8 items-center bg-[rgba(29,29,31,0.5)] px-6 py-2 rounded-full border border-white/5 backdrop-blur-md">
          <Link className="text-[#e4e2e4] font-medium text-xs uppercase tracking-wider hover:text-[#f2b98b] transition-colors" href="/">Workspace</Link>
          <Link className="text-[#e4e2e4] font-medium text-xs uppercase tracking-wider hover:text-[#f2b98b] transition-colors" href="/history">History</Link>
          <Link className="text-[#e4e2e4] font-medium text-xs uppercase tracking-wider hover:text-[#f2b98b] transition-colors" href="/portfolio">Portfolio</Link>
        </nav>
        <div className="flex items-center gap-6">
          <button className="text-[#e4e2e4] hover:text-[#fefef7] transition-colors">
            <span className="material-symbols-outlined">settings</span>
          </button>
          <div 
            className="h-8 w-8 rounded-full hollow-avatar overflow-hidden cursor-pointer hover:ring-2 hover:ring-[#f2b98b] transition-all"
            onClick={() => setIsProfileOpen(true)}
          >
            <img alt="User Avatar" className="w-full h-full object-cover" src="https://lh3.googleusercontent.com/aida-public/AB6AXuBr-zkAzm0f8cv4NCBCfQpTxI9tV0iejjCyA_swC4LDb1pifpxji1RPBSud15WRFN1BRjOlgkd9Dig-9ryc6fZ7Iv45vXalI0N8fqYwmy9PWcR3WgL_l5NGh0r1_8wto5Dn_1QpqS1G7XuLD28J1VsuvdfKWMALg2wEtZbkYs_jviJQX6YaXc1pb53dzXbc5cItLfMi3KvTt9J9uGi1BieajhYU_MLWXnRNVoNT_v-Koet7T51kxtsCZOEWgY-oG-HGXKWJO5YNr1E" />
          </div>
          {connected !== undefined && (
            <button className="bg-[#fefef7] text-black px-4 py-2 rounded-[16px] text-xs font-semibold hover:bg-white transition-colors">
              {connected ? "System Online" : "Connecting..."}
            </button>
          )}
        </div>
      </header>
    </>
  );
}
