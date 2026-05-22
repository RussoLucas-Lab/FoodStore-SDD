/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Design System — Apple-inspired palette
        blue: {
          DEFAULT: '#0071E3',
          dark: '#0055C6',
        },
        surface: '#F5F5F7',
        'border-color': '#D2D2D7',
        'text-primary': '#1D1D1F',
        'text-secondary': '#6E6E73',
        'text-tertiary': '#A1A1A6',
        success: '#34C759',
        error: '#FF3B30',
      },
      fontFamily: {
        sans: [
          'SF Pro Display',
          '-apple-system',
          'BlinkMacSystemFont',
          'system-ui',
          'Helvetica Neue',
          'Arial',
          'sans-serif',
        ],
      },
      borderRadius: {
        sm: '10px',
        md: '18px',
        lg: '28px',
        full: '9999px',
      },
      maxWidth: {
        product: '980px',
        grid: '1200px',
      },
      boxShadow: {
        modal: '0 40px 80px rgba(0, 0, 0, 0.2)',
        card: '0 2px 20px rgba(0, 0, 0, 0.06)',
      },
    },
  },
  plugins: [],
}
