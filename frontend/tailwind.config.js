/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          DEFAULT: '#0D1B2A',
          light: '#1B263B',
          lighter: '#415A77'
        },
        saffron: {
          DEFAULT: '#F4A500',
          hover: '#E59400'
        },
        steel: {
          DEFAULT: '#3D5A73',
          dark: '#2A4054',
          light: '#778DA9',
          lightest: '#E0E1DD'
        }
      },
      fontFamily: {
        sora: ['Sora', 'sans-serif'],
        mono: ['IBM Plex Mono', 'monospace'],
        sans: ['Inter', 'sans-serif'],
      },
      backgroundImage: {
        'pattern': "radial-gradient(circle at 2px 2px, rgba(255,255,255,0.05) 1px, transparent 0)",
      },
      backgroundSize: {
        'pattern': '24px 24px',
      }
    },
  },
  plugins: [],
}
