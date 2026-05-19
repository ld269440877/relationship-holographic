/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // macOS 风格颜色
        'apple-gray': {
          50: '#f5f5f7',
          100: '#e8e8ed',
          200: '#d2d2d7',
          300: '#b8b8bf',
          400: '#86868b',
          500: '#6e6e73',
          600: '#424245',
          700: '#2d2d30',
          800: '#1d1d1f',
          900: '#000000',
        },
        'emotion': {
          joy: '#34C759',
          anger: '#FF3B30',
          sadness: '#007AFF',
          fear: '#AF52DE',
          love: '#FF2D55',
          surprise: '#FF9500',
          shame: '#5856D6',
        },
        'accent': {
          primary: '#007AFF',
          secondary: '#5856D6',
          success: '#34C759',
          warning: '#FF9500',
          danger: '#FF3B30',
        }
      },
      backdropBlur: {
        'xs': '2px',
      },
      fontFamily: {
        'sf': ['-apple-system', 'BlinkMacSystemFont', 'SF Pro Display', 'sans-serif'],
      },
      boxShadow: {
        'mac': '0 8px 32px rgba(0, 0, 0, 0.12)',
        'mac-sm': '0 2px 8px rgba(0, 0, 0, 0.08)',
        'mac-inset': 'inset 0 1px 3px rgba(0, 0, 0, 0.1)',
      },
      borderRadius: {
        'mac': '12px',
        'mac-lg': '16px',
        'mac-sm': '8px',
      }
    },
  },
  plugins: [require("daisyui")],
  daisyui: {
    themes: [
      {
        light: {
          "primary": "#007AFF",
          "secondary": "#5856D6",
          "accent": "#FF9500",
          "neutral": "#2d2d30",
          "base-100": "#ffffff",
          "base-200": "#f5f5f7",
          "base-300": "#e8e8ed",
          "info": "#007AFF",
          "success": "#34C759",
          "warning": "#FF9500",
          "error": "#FF3B30",
        },
        dark: {
          "primary": "#0A84FF",
          "secondary": "#5E5CE6",
          "accent": "#FF9F0A",
          "neutral": "#636366",
          "base-100": "#1d1d1f",
          "base-200": "#2d2d30",
          "base-300": "#3a3a3c",
          "info": "#0A84FF",
          "success": "#30D158",
          "warning": "#FF9F0A",
          "error": "#FF453A",
        },
      },
    ],
  },
}