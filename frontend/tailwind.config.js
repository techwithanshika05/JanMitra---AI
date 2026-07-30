/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['DM Sans', 'sans-serif'],
        heading: ['Manrope', 'sans-serif'],
      },
      animation: {
        'spin-slow': 'spin 1.2s linear infinite',
        'pulse-soft': 'pulseSoft 1.4s ease-in-out infinite alternate',
        'float': 'float 4s ease-in-out infinite',
        'fade-in': 'fadeIn .55s ease both',
        'skeleton': 'skeleton 1.4s infinite linear',
        'scanner': 'scannerLine 2.4s infinite ease-in-out',
        'mic-pulse': 'micPulse 1.4s infinite',
        'mic-scale': 'micScale .9s ease-in-out infinite alternate',
      },
      keyframes: {
        pulseSoft: {
          '0%': { transform: 'scale(.94) rotate(-3deg)' },
          '100%': { transform: 'scale(1.04) rotate(3deg)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        fadeIn: {
          '0%': { opacity: 0, transform: 'translateY(16px)' },
          '100%': { opacity: 1, transform: 'translateY(0)' },
        },
        skeleton: {
          '0%': { backgroundPosition: '0% 0%' },
          '100%': { backgroundPosition: '200% 0%' },
        },
        scannerLine: {
          '0%, 100%': { top: '8%', opacity: '.4' },
          '50%': { top: '90%', opacity: '1' },
        },
        micPulse: {
          '0%': { boxShadow: '0 0 0 0 rgba(255, 104, 64, .28)' },
          '70%': { boxShadow: '0 0 0 9px rgba(255, 104, 64, 0)' },
          '100%': { boxShadow: '0 0 0 0 rgba(255, 104, 64, 0)' },
        },
        micScale: {
          '0%': { transform: 'scale(1)' },
          '100%': { transform: 'scale(1.12)' },
        },
      },
    },
  },
  plugins: [],
}