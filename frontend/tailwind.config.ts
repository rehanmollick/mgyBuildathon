import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/app/**/*.{ts,tsx}",
    "./src/components/**/*.{ts,tsx}",
    "./src/lib/**/*.{ts,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        bg: {
          DEFAULT: "#0A0A0F",
          card: "#12121A",
          hover: "#1A1A24",
          border: "#23232E",
        },
        profit: "#00FF88",
        loss: "#FF3B5C",
        info: "#4C9EFF",
        muted: "#6B6B7B",
      },
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
        mono: ["JetBrains Mono", "Menlo", "Monaco", "Courier New", "monospace"],
      },
      keyframes: {
        "fade-in": {
          "0%": { opacity: "0", transform: "translateY(4px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "pulse-profit": {
          "0%, 100%": { boxShadow: "0 0 0 0 rgba(0, 255, 136, 0.4)" },
          "50%": { boxShadow: "0 0 0 8px rgba(0, 255, 136, 0)" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.5s ease-out",
        "pulse-profit": "pulse-profit 2s ease-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
