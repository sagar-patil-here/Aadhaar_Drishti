/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  // StatCard in Dashboard.js composes classes at runtime as
  //   `bg-${color}-500/10 text-${color}-500 bg-${color}-500/20 bg-${color}-500`
  // Tailwind's JIT scanner cannot see these interpolated tokens, so any
  // new colour passed to StatCard must be safelisted here for its CSS
  // to be generated.
  safelist: [
    ...["red", "orange", "yellow", "blue", "purple", "green", "teal"].flatMap((c) => [
      `bg-${c}-500`,
      `bg-${c}-500/10`,
      `bg-${c}-500/20`,
      `text-${c}-500`,
    ]),
  ],
  theme: {
    extend: {
      colors: {
        background: '#0f172a', // Slate 900
        surface: '#1e293b',    // Slate 800
        primary: '#3b82f6',    // Blue 500
        accent: '#f43f5e',     // Rose 500
        success: '#10b981',    // Emerald 500
        warning: '#f59e0b',    // Amber 500
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.6s ease-out forwards',
        'slide-up': 'slideUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'shimmer': 'shimmer 2s linear infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '200% 0' },
          '100%': { backgroundPosition: '-200% 0' },
        }
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'glass': 'linear-gradient(180deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%)',
      }
    },
  },
  plugins: [],
}
