/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.js"],
  theme: {
    extend: {},
  },
  plugins: ["tailwindcss", "autoprefixer"],
  plugins: [require("tailwind-scrollbar-hide")],
};
