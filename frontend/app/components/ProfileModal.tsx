import { useState, useEffect } from "react";
import { toast } from "react-hot-toast";

interface UserProfile {
  income: number;
  risk_tolerance: string;
  experience: string;
}

interface ProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
  isFirstVisit?: boolean;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ProfileModal({ isOpen, onClose, isFirstVisit = false }: ProfileModalProps) {
  const [profile, setProfile] = useState<UserProfile>({
    income: 0,
    risk_tolerance: "moderate",
    experience: "beginner"
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetchProfile();
    }
  }, [isOpen]);

  const fetchProfile = async () => {
    setLoading(true);
    try {
      const resp = await fetch(`${API_BASE}/api/user/profile`);
      if (resp.ok) {
        const data = await resp.json();
        setProfile({
          income: data.income,
          risk_tolerance: data.risk_tolerance,
          experience: data.experience
        });
      }
    } catch (e) {
      console.error("Failed to fetch profile", e);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const resp = await fetch(`${API_BASE}/api/user/profile`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(profile)
      });
      if (!resp.ok) throw new Error("Failed to save profile");
      toast.success("Profile saved successfully");
      onClose();
    } catch (e) {
      toast.error("Failed to save profile");
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center w-screen h-screen bg-[#0f0f10]/80 backdrop-blur-md p-4">
      <div className="w-full sm:w-[500px] min-w-[350px] p-8 rounded-[24px] flex flex-col gap-6 shrink-0" style={{
        background: "rgba(20, 20, 22, 0.95)",
        border: "1px solid rgba(255, 255, 255, 0.1)",
        boxShadow: "inset 0 1px 0 0 rgba(255, 255, 255, 0.05), 0 25px 50px -12px rgba(0, 0, 0, 0.5)",
      }}>
        <h2 className="text-2xl font-display-xl uppercase tracking-widest text-primary">
          {isFirstVisit ? "Welcome to Delphi" : "Your Profile"}
        </h2>
        {isFirstVisit && (
          <p className="text-sm text-on-surface-variant font-body-md">
            Before we begin, please tell us a bit about your investment profile so our agents can tailor their memos to you.
          </p>
        )}

        {loading ? (
          <p className="text-on-surface-variant opacity-50">Loading profile...</p>
        ) : (
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <label className="text-xs font-eyebrow tracking-widest text-secondary uppercase">Annual Income ($)</label>
              <input 
                type="number" 
                value={profile.income}
                onChange={e => setProfile({...profile, income: Number(e.target.value)})}
                className="bg-surface/50 border border-white/10 rounded-lg p-3 text-on-surface focus:outline-none focus:border-secondary transition-colors"
              />
            </div>
            <div className="flex flex-col gap-2">
              <label className="text-xs font-eyebrow tracking-widest text-secondary uppercase">Risk Tolerance</label>
              <select 
                value={profile.risk_tolerance}
                onChange={e => setProfile({...profile, risk_tolerance: e.target.value})}
                className="bg-surface/50 border border-white/10 rounded-lg p-3 text-on-surface focus:outline-none focus:border-secondary transition-colors appearance-none"
              >
                <option value="conservative">Conservative</option>
                <option value="moderate">Moderate</option>
                <option value="aggressive">Aggressive</option>
              </select>
            </div>
            <div className="flex flex-col gap-2">
              <label className="text-xs font-eyebrow tracking-widest text-secondary uppercase">Experience Level</label>
              <select 
                value={profile.experience}
                onChange={e => setProfile({...profile, experience: e.target.value})}
                className="bg-surface/50 border border-white/10 rounded-lg p-3 text-on-surface focus:outline-none focus:border-secondary transition-colors appearance-none"
              >
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
              </select>
            </div>
          </div>
        )}

        <div className="flex justify-end gap-3 mt-4">
          {!isFirstVisit && (
            <button onClick={onClose} className="px-4 py-2 text-on-surface-variant hover:text-primary transition-colors text-sm uppercase tracking-wider font-label-sm">
              Cancel
            </button>
          )}
          <button 
            onClick={handleSave} 
            disabled={saving || loading}
            className="px-6 py-2 bg-[#f2b98b] text-black font-semibold rounded-lg hover:bg-white transition-colors text-sm uppercase tracking-wider font-label-sm disabled:opacity-50"
          >
            {saving ? "Saving..." : (isFirstVisit ? "Get Started" : "Save Profile")}
          </button>
        </div>
      </div>
    </div>
  );
}
