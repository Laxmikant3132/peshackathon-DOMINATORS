/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: {
          DEFAULT: "#0a0a0f",
          darker: "#050510",
        },
        primary: {
          DEFAULT: "#00ffff", // Cyan
        },
        secondary: {
          DEFAULT: "#10b981", // Emerald
        },
        accent: {
          DEFAULT: "#a855f7", // Purple
        },
        warning: {
          DEFAULT: "#f59e0b", // Amber
        },
        danger: {
          DEFAULT: "#ef4444", // Red
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
      },
    },
  },
  plugins: [],
}
