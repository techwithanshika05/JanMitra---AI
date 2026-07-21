/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // --- JanMitra civic palette (chosen to avoid generic AI-default
        // cream+terracotta or dark+neon looks; grounded in Indian civic
        // identity: indigo (trust/governance), marigold (welfare/warmth),
        // teal (growth) ---
        ink: "#10192E",        // near-black navy for dark mode bg / text
        indigo: {
          DEFAULT: "#1B2A4A",
          50: "#EEF1F7",
          100: "#D6DCEA",
          600: "#24365D",
          900: "#10192E",
        },
        marigold: {
          DEFAULT: "#E8871E",
          50: "#FDF3E7",
          400: "#F0A24C",
          600: "#C96E0E",
        },
        teal: {
          DEFAULT: "#0F6A5D",
          50: "#E7F3F1",
          600: "#0B5347",
        },
        paper: "#FAF7F2",
      },
      fontFamily: {
        display: ["var(--font-display)", "serif"],
        body: ["var(--font-body)", "sans-serif"],
      },
      borderRadius: {
        card: "14px",
      },
      boxShadow: {
        card: "0 1px 2px rgba(16,25,46,0.04), 0 8px 24px rgba(16,25,46,0.06)",
      },
    },
  },
  plugins: [],
};
