import { useState, useEffect } from "react";
import { Settings, X } from "lucide-react";

export default function SettingsModal({ isOpen, onClose }: { isOpen: boolean, onClose: () => void }) {
  const [provider, setProvider] = useState("azure");
  const [apiToken, setApiToken] = useState("");
  
  useEffect(() => {
    const saved = localStorage.getItem("telos_provider");
    if (saved) setProvider(saved);
    setApiToken(localStorage.getItem("telos_api_token") ?? "");
  }, [isOpen]);

  const handleSave = () => {
    localStorage.setItem("telos_provider", provider);
    if (apiToken.trim()) {
      localStorage.setItem("telos_api_token", apiToken.trim());
    } else {
      localStorage.removeItem("telos_api_token");
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
            <label className="block text-xs font-mono text-telos-text-muted mb-1">AI PROVIDER</label>
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              className="w-full bg-telos-bg border border-telos-border rounded px-3 py-2 text-white font-mono focus:border-telos-accent outline-none"
            >
              <option value="azure">Azure OpenAI (HTTP adapter)</option>
              <option value="gemini">Google Gemini (GenAI SDK)</option>
              <option value="azure_sk">Azure OpenAI (Semantic Kernel)</option>
            </select>
            <p className="mt-2 text-xs text-telos-text-muted">
              Applies to new task submissions and health checks immediately.
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
