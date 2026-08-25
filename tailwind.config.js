/** @type {import('tailwindcss').Config} */
// Design tokens are frozen in tech.md section 7. They come from the existing
// OSK NAWROCKI banner, so the site matches the signage on the building.
module.exports = {
  content: [
    "./templates/**/*.html",
    "./apps/**/*.py",
    "./static/js/**/*.js",
    // crispy-tailwind ships its markup inside site-packages. Without this the
    // form classes get purged and every form renders unstyled. Container path
    // first, host virtualenv second: an unmatched glob is not an error.
    "/venv/lib/python3.12/site-packages/crispy_tailwind/**/*.html",
    "./.venv/Lib/site-packages/crispy_tailwind/**/*.html",
  ],
  theme: {
    extend: {
      colors: {
        brand: { 900: "#2A1F55", 700: "#3B2D71", 500: "#5B47A8", 100: "#EBE6F8" },
        accent: { 500: "#FFD400", 600: "#E0BA00" },
        ink: { 900: "#181328", 700: "#3A3350", 500: "#6B6383" },
        paper: { 0: "#FFFFFF", 50: "#F7F6FA", 100: "#EFEDF4" },
        state: { ok: "#1E7A56", warn: "#B27C00", err: "#B3382B" },
      },
      fontFamily: {
        // Headings: condensed grotesque. Body: humanist sans. Both self hosted
        // and both cover polish latin-ext plus the cyrillic ru and uk need.
        display: ['"Roboto Condensed"', "ui-sans-serif", "system-ui", "sans-serif"],
        sans: ['"Source Sans 3"', "ui-sans-serif", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
