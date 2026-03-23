/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["Space Grotesk", "sans-serif"],
        body: ["IBM Plex Sans", "sans-serif"]
      },
      colors: {
        ink: "#0f172a",
        cream: "#f8f5f0",
        accent: "#0ea5e9",
        moss: "#0f766e",
        ember: "#ea580c"
      }
    }
  },
  plugins: []
};
