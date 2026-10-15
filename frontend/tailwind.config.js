/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        space: {
          950: '#030712',
          900: '#060b17',
          850: '#0a1024',
          800: '#0f172a',
          700: '#1e293b',
          600: '#334155'
        },
        cyan: {
          400: '#22d3ee',
          500: '#06b6d4',
          accent: '#00f0ff'
        },
        emerald: {
          accent: '#10b981'
        },
        purple: {
          accent: '#8b5cf6'
        },
        rose: {
          accent: '#f43f5e'
        }
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', 'monospace'],
        sans: ['"Space Grotesk"', 'Inter', 'sans-serif']
      },
      boxShadow: {
        'glow-cyan': '0 0 20px -2px rgba(0, 240, 255, 0.25)',
        'glow-emerald': '0 0 20px -2px rgba(16, 185, 129, 0.25)',
        'glow-purple': '0 0 20px -2px rgba(139, 92, 246, 0.25)',
      }
    },
  },
  plugins: [],
}
