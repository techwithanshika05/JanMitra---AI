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
        // Token names (maroon/rose/blush/gold) kept as-is so every existing
        // page/component keeps working unmodified -- only the underlying hex
        // values are reverted to the original civic (indigo/marigold) palette.
        maroon: {
          DEFAULT: "#1B2A4A",   // was primary dark -> old indigo
          dark: "#24365D",      // was maroon-dark -> old indigo-600
        },
        rose: {
          DEFAULT: "#E8871E",   // was accent -> old marigold
        },
        blush: {
          DEFAULT: "#EEF1F7",   // was soft pink -> old indigo-50 (soft neutral tint)
        },
        gold: {
          DEFAULT: "#F0A24C",   // was warm highlight -> old marigold-400
        },
        paper: "#FAF7F2",
      },
      fontFamily: {
        display: ["var(--font-display)", "sans-serif"],
        body: ["var(--font-body)", "sans-serif"],
      },
      borderRadius: {
        card: "20px",
        pill: "999px",
      },
      boxShadow: {
        glow: "0 8px 30px -6px rgba(232, 135, 30, 0.35)",
        glowLg: "0 20px 60px -10px rgba(232, 135, 30, 0.4)",
        card: "0 1px 2px rgba(27,42,74,0.04), 0 12px 32px -8px rgba(27,42,74,0.12)",
      },
      backgroundImage: {
        "gradient-primary": "linear-gradient(135deg, #1B2A4A 0%, #E8871E 100%)",
        "gradient-warm": "linear-gradient(135deg, #E8871E 0%, #F0A24C 100%)",
        "gradient-soft": "linear-gradient(180deg, #FAF7F2 0%, #FFFFFF 100%)",
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-12px)" },
        },
        ripple: {
          "0%": { transform: "scale(0)", opacity: "0.5" },
          "100%": { transform: "scale(2.5)", opacity: "0" },
        },
        blobMove: {
          "0%, 100%": { transform: "translate(0, 0) scale(1)" },
          "33%": { transform: "translate(30px, -40px) scale(1.08)" },
          "66%": { transform: "translate(-20px, 20px) scale(0.95)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
      animation: {
        float: "float 6s ease-in-out infinite",
        ripple: "ripple 0.6s ease-out",
        blob: "blobMove 18s ease-in-out infinite",
        shimmer: "shimmer 1.8s linear infinite",
      },
    },
  },
  plugins: [],
};
