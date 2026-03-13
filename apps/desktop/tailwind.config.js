/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        telos: {
          bg: "#0a0e17",
          surface: "#111827",
          border: "#1f2937",
          accent: "#3b82f6",
          "accent-bright": "#60a5fa",
          success: "#10b981",
          warning: "#f59e0b",
          danger: "#ef4444",
          text: "#e5e7eb",
          "text-dim": "#9ca3af",
          "text-muted": "#6b7280",
        },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Fira Code", "Consolas", "monospace"],
      },
    },
  },
  plugins: [],
};
