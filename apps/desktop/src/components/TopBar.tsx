/**
 * TELOS Top Bar — branding, connection status, provider indicator.
 */

import { useTelosStore } from "../store";
import { Shield, Wifi, WifiOff, Zap, Settings as SettingsIcon } from "lucide-react";

interface TopBarProps {
  onOpenSettings?: () => void;
}

export default function TopBar({ onOpenSettings }: TopBarProps) {
  const { connected, systemState } = useTelosStore();

  return (
    <div className="h-12 bg-telos-surface border-b border-telos-border flex items-center px-4 gap-4 shrink-0">
      {/* Logo */}
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded bg-telos-accent flex items-center justify-center">
          <Zap size={16} className="text-white" />
        </div>
        <span className="text-lg font-bold tracking-wider text-white">TELOS</span>
        <span className="text-xs text-telos-text-muted tracking-wide">MISSION CONTROL</span>
      </div>

      <div className="flex-1" />

      {/* Provider badge */}
      {systemState && (
        <div className="flex items-center gap-2 text-xs">
          <span className="text-telos-text-muted">PROVIDER</span>
          <span className={`px-2 py-0.5 rounded text-xs font-mono font-bold ${
            systemState.provider_healthy
              ? "bg-telos-success/20 text-telos-success"
              : "bg-telos-warning/20 text-telos-warning"
          }`}>
            {systemState.provider.toUpperCase()}
          </span>
        </div>
      )}

      {/* Privacy mode */}
      <div className="flex items-center gap-1 text-xs text-telos-text-muted">
        <Shield size={14} className="text-telos-success" />
        <span>STRICT</span>
      </div>

      {/* Connection status */}
      <div className="flex items-center gap-1 border-r border-telos-border pr-4 mr-1">
        {connected ? (
          <>
            <Wifi size={14} className="text-telos-success" />
            <span className="text-xs text-telos-success">LIVE</span>
            <div className="w-2 h-2 rounded-full bg-telos-success animate-telos-pulse" />
          </>
        ) : (
          <>
            <WifiOff size={14} className="text-telos-danger" />
            <span className="text-xs text-telos-danger">OFFLINE</span>
          </>
        )}
      </div>

      {/* Settings Button */}
      <button 
        onClick={onOpenSettings}
        className="text-telos-text-muted hover:text-white transition-colors"
        title="Settings & Configuration"
      >
        <SettingsIcon size={18} />
      </button>
    </div>
  );
}
