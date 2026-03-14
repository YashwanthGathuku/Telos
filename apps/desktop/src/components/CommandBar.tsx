/**
 * TELOS Command Bar — task submission interface.
 * Not a chat bubble. A command line for desktop operations.
 */

import { useState } from "react";
import { useTelosStore } from "../store";
import { submitTask } from "../api";
import { Send, Loader2, Mic } from "lucide-react";

export default function CommandBar() {
  const { commandInput, setCommandInput, isSubmitting, setIsSubmitting } = useTelosStore();
  const [error, setError] = useState<string | null>(null);
  const [isListening, setIsListening] = useState(false);

  const startListening = () => {
    // @ts-ignore
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setError("Speech recognition not supported in this browser");
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.onresult = (event: any) => {
      const transcript = event.results[event.results.length - 1][0].transcript;
      setCommandInput(commandInput ? `${commandInput} ${transcript}` : transcript);
    };
    recognition.onend = () => setIsListening(false);
    recognition.start();
    setIsListening(true);
  };


  const handleSubmit = async () => {
    const trimmed = commandInput.trim();
    if (!trimmed || isSubmitting) return;

    // Basic sanitization
    const sanitized = trimmed
      .replace(/<script[^>]*>.*?<\/script>/gi, "")
      .replace(/<[^>]+>/g, "");

    if (sanitized.length > 10000) {
      setError("Task too long (max 10,000 characters)");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      await submitTask(sanitized);
      setCommandInput("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to submit task");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="bg-telos-surface border border-telos-border rounded-lg p-3 h-full">
      <div className="text-[10px] text-telos-text-muted font-mono uppercase tracking-wider mb-2">
        MISSION COMMAND
      </div>
      <div className="flex items-center gap-2">
        <div className="flex-1 relative">
          <input
            type="text"
            value={commandInput}
            onChange={(e) => setCommandInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Enter a desktop operation task..."
            className="w-full bg-telos-bg border border-telos-border rounded px-3 py-2
                       text-sm text-telos-text placeholder-telos-text-muted
                       focus:outline-none focus:border-telos-accent focus:ring-1 focus:ring-telos-accent/30
                       font-mono"
            maxLength={10000}
            disabled={isSubmitting}
          />
          {error && (
            <div className="absolute -bottom-5 left-0 text-xs text-telos-danger">
              {error}
            </div>
          )}
        </div>
        <button
          onClick={startListening}
          disabled={isSubmitting || isListening}
          className={`px-3 py-2 rounded text-sm transition-colors border
            ${isListening 
              ? "bg-red-500/20 text-red-500 border-red-500/50 animate-pulse" 
              : "bg-telos-surface hover:bg-telos-bg text-telos-text-muted border-telos-border hover:text-white"
            }`}
          title="Voice Command"
        >
          <Mic size={16} />
        </button>
        <button
          onClick={handleSubmit}
          disabled={isSubmitting || !commandInput.trim()}
          className="bg-telos-accent hover:bg-telos-accent-bright disabled:bg-telos-border
                     text-white px-4 py-2 rounded text-sm font-medium
                     transition-colors flex items-center gap-2 shrink-0"
        >
          {isSubmitting ? (
            <Loader2 size={16} className="animate-spin" />
          ) : (
            <Send size={16} />
          )}
          EXECUTE
        </button>
      </div>
    </div>
  );
}
