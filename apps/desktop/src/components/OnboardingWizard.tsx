import { useState, useEffect } from "react";
import { Zap } from "lucide-react";

export default function OnboardingWizard() {
  const [isVisible, setIsVisible] = useState(false);
  
  useEffect(() => {
    const isComplete = localStorage.getItem("telos_setup_complete");
    if (!isComplete) {
      setIsVisible(true);
    }
  }, []);

  const handleComplete = () => {
    localStorage.setItem("telos_setup_complete", "true");
    setIsVisible(false);
  };

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-[100] flex items-center justify-center p-4">
      <div className="bg-telos-surface border border-telos-accent/30 rounded-2xl p-8 max-w-lg w-full text-center shadow-2xl relative overflow-hidden">
        {/* Glow effect */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-64 h-32 bg-telos-accent/20 blur-[60px] pointer-events-none" />
        
        <div className="mx-auto w-16 h-16 bg-telos-accent/10 border border-telos-accent/50 rounded-2xl flex items-center justify-center mb-6">
          <Zap className="text-telos-accent w-8 h-8" />
        </div>
        
        <h1 className="text-3xl font-bold tracking-widest text-white mb-2">TELOS</h1>
        <p className="text-telos-text-muted mb-8 font-mono text-sm uppercase tracking-wide">
          Mission Control Initialization
        </p>

        <div className="text-left bg-telos-bg border border-telos-border rounded-lg p-4 mb-8">
          <h3 className="font-bold text-white mb-2 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-telos-success animate-pulse" />
            SYSTEM READY
          </h3>
          <p className="text-sm text-telos-text">
            Welcome to the TELOS execution harness. 
            Before proceeding to the operations dashboard, please ensure that your orchestrator environment variables (e.g. GEMINI_API_KEY, AZURE_OPENAI_API_KEY) are configured correctly.
          </p>
        </div>

        <button 
          onClick={handleComplete}
          className="w-full bg-telos-accent hover:bg-telos-accent-bright text-white font-bold py-3 rounded-lg tracking-widest transition-all hover:scale-[1.02] active:scale-[0.98]"
        >
          ENTER MISSION CONTROL
        </button>
      </div>
    </div>
  );
}
