/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          light: '#42a5f5',
          main: '#1976d2',
          dark: '#1565c0',
        },
      },
      spacing: {
        '72': '18rem',
        '84': '21rem',
        '96': '24rem',
      },
    },
  },
  plugins: [require("daisyui")],
  daisyui: {
    themes: [
      {
        light: {
          ...require("daisyui/src/theming/themes")["light"],
          primary: "#2196f3",
          secondary: "#90caf9",
          accent: "#1976d2",
          "base-100": "#ffffff",
          "base-200": "#f5f5f5", 
          "base-300": "#e0e0e0",
          "base-content": "#212121"
        },
        dark: {
          ...require("daisyui/src/theming/themes")["dark"],
          primary: "#2196f3",
          secondary: "#90caf9",
          accent: "#1976d2",
          neutral: "#2a2a2a",
          "base-100": "#121212",
          "base-200": "#1e1e1e", 
          "base-300": "#2c2c2c",
          "base-content": "#ffffff"
        },
      },
    ],
  },
}

