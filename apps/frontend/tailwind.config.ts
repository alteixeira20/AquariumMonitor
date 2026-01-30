import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ocean: {
          950: "#071218",
          900: "#0b1b24",
          850: "#0f2431",
          800: "#132c3b",
          700: "#1b3a4b",
          500: "#4fd1c5",
          400: "#64e2d6"
        },
      },
      boxShadow: {
        ocean: "0 24px 60px rgba(7, 18, 25, 0.45)",
        glow: "0 0 24px rgba(79, 209, 197, 0.35)",
      },
      fontFamily: {
        display: ["var(--font-display)", "serif"],
        body: ["var(--font-body)", "sans-serif"],
      },
      keyframes: {
        pulseGlow: {
          "0%, 100%": { transform: "scale(1)", opacity: "0.8" },
          "50%": { transform: "scale(1.2)", opacity: "1" },
        },
        floatIn: {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        pulseGlow: "pulseGlow 2.4s ease-in-out infinite",
        floatIn: "floatIn 0.4s ease-out",
      },
    },
  },
  plugins: [],
};

export default config;
