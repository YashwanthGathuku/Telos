import { useState, useEffect } from "react";
import { Settings, X } from "lucide-react";

export default function SettingsModal({ isOpen, onClose }: { isOpen: boolean, onClose: () => void }) {
  const [apiToken, setApiToken] = useState("");
  
  useEffect(() => {
    sessionStorage.setItem("telos_provider", "gemini");
    setApiToken(sessionStorage.getItem("telos_api_token") ?? "");
  }, [isOpen]);

  const handleSave = () => {
    sessionStorage.setItem("telos_provider", "gemini");
    if (apiToken.trim()) {
      sessionStorage.setItem("telos_api_token", apiToken.trim());
    } else {
      sessionStorage.removeItem("telos_api_token");
    }
    window.dispatchEvent(new Event("telos-settings-updated"));
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center">
      <div className="bg-telos-surface border border-telos-border rounded-xl p-6 w-full max-w-md shadow-2xl">
        <div className="flex justify-between items-center mb-6">
          <div className="flex items-center gap-2">
            <Settings className="text-telos-accent" />
            <h2 className="text-xl font-bold text-white tracking-widest">SETTINGS</h2>
          </div>
          <button onClick={onClose} className="text-telos-text-muted hover:text-white transition-colors">
            <X size={20} />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-xs font-mono text-telos-text-muted mb-1">AI STACK</label>
            <div className="w-full bg-telos-bg border border-telos-border rounded px-3 py-2 text-white font-mono">
              Gemini + Google ADK
            </div>
            <p className="mt-2 text-xs text-telos-text-muted">
              TELOS is configured for the Gemini submission build.
            </p>
          </div>

          <div>
            <label className="block text-xs font-mono text-telos-text-muted mb-1">API TOKEN</label>
            <input
              value={apiToken}
              onChange={(e) => setApiToken(e.target.value)}
              type="password"
              placeholder="Optional bearer token for protected deployments"
              className="w-full bg-telos-bg border border-telos-border rounded px-3 py-2 text-white font-mono focus:border-telos-accent outline-none"
            />
            <p className="mt-2 text-xs text-telos-text-muted">
              Used for orchestrator, scheduler, and event-stream authentication when enabled server-side.
            </p>
          </div>
        </div>

        <div className="mt-8 flex justify-end gap-3">
          <button onClick={onClose} className="px-4 py-2 text-sm text-telos-text hover:text-white">
            CANCEL
          </button>
          <button onClick={handleSave} className="px-4 py-2 bg-telos-accent hover:bg-telos-accent-bright text-white text-sm font-bold rounded tracking-wider">
            SAVE CONFIG
          </button>
        </div>
      </div>
    </div>
  );
}
