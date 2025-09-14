/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'leadville': {
          primary: '#667eea',
          secondary: '#764ba2',
          accent: '#4f46e5',
        }
      },
      fontFamily: {
        'sans': ['Inter', 'system-ui', 'sans-serif'],
      },
      spacing: {
        'kiosk': '12rem', // Large spacing for kiosk interfaces
      },
      fontSize: {
        'kiosk-xl': ['2rem', '2.5rem'],
        'kiosk-2xl': ['3rem', '3.5rem'],
        'kiosk-3xl': ['4rem', '4.5rem'],
      }
    },
  },
  plugins: [],
}