/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0a0b10",
        glass: "rgba(255, 255, 255, 0.04)",
        critical: "#FF4B4B",
        warning: "#FFA500",
        safe: "#00FF88",
        info: "#00A3FF",
      },
      backgroundImage: {
        'cyber-gradient': "radial-gradient(circle at top right, #1a1b26, #0a0b10)",
      },
      backdropBlur: {
        xs: '2px',
      }
    },
  },
  plugins: [],
}
