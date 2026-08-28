/** @type {import('tailwindcss').Config} */
// Design tokens are frozen in FRONTEND.md part A. tech.md section 7 carries an
// earlier sketch of the palette and says outright that FRONTEND.md A.2 wins
// where the two disagree, so this file follows A.2 and nothing else.
//
// Every colour resolves to a CSS variable defined in static/src/css/app.css.
// That is what lets the dark theme be a swap of roles rather than a second set
// of utilities: the class stays bg-paper, the variable underneath changes.
const token = (name) => `rgb(var(--${name}) / <alpha-value>)`;

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

  // The layout classes in app.css live in @layer components, which tailwind
  // purges like anything else. They are the base layer the pages are built on
  // and have to exist before the first page uses one, so they are kept by
  // name rather than by whether a template happens to mention them yet.
  safelist: [{ pattern: /^u-/ }],

  // The dark: variant follows the same two doors the variables do: the system
  // preference unless the reader has explicitly asked for light, and the
  // explicit data-theme="dark". Colour rarely needs it, since the tokens swap
  // themselves; it is here for the cases that are not colour.
  darkMode: [
    "variant",
    [
      "@media (prefers-color-scheme: dark) { :root:not([data-theme='light']) & }",
      "[data-theme='dark'] &",
    ],
  ],

  theme: {
    // FRONTEND.md A.4. Replacing rather than extending: a 2xl breakpoint that
    // is not in the contract has no business being reachable.
    screens: {
      sm: "480px",
      md: "768px",
      lg: "1024px",
      xl: "1280px",
    },

    // A.2. Three colours and a ground for inverted blocks, nothing else.
    //
    // Replacing rather than extending is deliberate: with no `gray` in the
    // palette, `text-gray-400` cannot be typed by accident. The price is two
    // dead literals in the built css. Preflight resolves its own placeholder
    // colour through theme('colors.gray.400', '#9ca3af') and its shadow
    // defaults through '#0000', so both fall back to the literal. Neither
    // paints anything: '#0000' is transparent, and the placeholder rule in
    // app.css matches preflight's selector and comes after it. Adding a `gray`
    // alias would clear them and hand every session an off-contract class in
    // exchange, which is the worse trade.
    colors: {
      transparent: "transparent",
      current: "currentColor",
      inherit: "inherit",
      paper: {
        DEFAULT: token("paper"),
        50: token("paper-50"),
        100: token("paper-100"),
        200: token("paper-200"),
      },
      ink: {
        DEFAULT: token("ink"),
        700: token("ink-700"),
        500: token("ink-500"),
        // Disabled text and hairlines only: 3.4:1 on paper is under the body
        // threshold on purpose, A.2.
        300: token("ink-300"),
      },
      // line.DEFAULT is the heavy frame, line.soft the divider.
      line: {
        DEFAULT: token("line"),
        soft: token("line-soft"),
      },
      accent: {
        DEFAULT: token("accent"),
        600: token("accent-600"),
        100: token("accent-100"),
      },
      // Inverted blocks and the footer. Never a button or a chip fill, A.1.
      deep: {
        DEFAULT: token("deep"),
        700: token("deep-700"),
      },
      state: {
        ok: token("state-ok"),
        warn: token("state-warn"),
        err: token("state-err"),
      },
    },

    // A.3. Display carries the width axis: font-stretch picks Expanded.
    fontFamily: {
      display: ["Archivo", "ui-sans-serif", "system-ui", "sans-serif"],
      sans: ["Public Sans", "ui-sans-serif", "system-ui", "sans-serif"],
      mono: ["Roboto Mono", "ui-monospace", "SFMono-Regular", "monospace"],
    },

    // A.3, the whole scale and only the scale. clamp() carries the step from
    // the 320px phone to the 1280px desktop, so there are no per-breakpoint
    // type utilities to keep in step.
    fontSize: {
      display: ["clamp(2.75rem, 7vw, 5.5rem)", { lineHeight: "0.95", letterSpacing: "-0.02em" }],
      h1: ["clamp(2.25rem, 5vw, 3.75rem)", { lineHeight: "1.02", letterSpacing: "-0.02em" }],
      h2: ["clamp(1.75rem, 3.2vw, 2.5rem)", { lineHeight: "1.08", letterSpacing: "-0.01em" }],
      h3: ["1.25rem", { lineHeight: "1.25", letterSpacing: "0" }],
      "body-lg": ["1.125rem", { lineHeight: "1.6" }],
      body: ["1rem", { lineHeight: "1.65" }],
      small: ["0.875rem", { lineHeight: "1.5" }],
      label: ["0.75rem", { lineHeight: "1.2", letterSpacing: "0.12em" }],
      // A.3 gives data as a range from 1rem to 2rem. Three steps of it: a
      // price in a table, a start date in a row, the number in a fact strip.
      data: ["1rem", { lineHeight: "1.1", letterSpacing: "-0.01em" }],
      "data-lg": ["1.5rem", { lineHeight: "1.1", letterSpacing: "-0.01em" }],
      "data-xl": ["2rem", { lineHeight: "1.1", letterSpacing: "-0.01em" }],
    },

    // A.3 uses exactly five: Public Sans 400/600, Roboto Mono 400/500,
    // Archivo 700/800. The woff2 subsets are sliced to those ranges, so a
    // weight outside this list would be synthesised by the browser.
    fontWeight: {
      normal: "400",
      medium: "500",
      semibold: "600",
      bold: "700",
      extrabold: "800",
    },

    // A.1: 0 for sections and slabs, 2px for buttons, fields and cards.
    // Nothing rounder exists, so rounded-2xl cannot be typed by accident.
    borderRadius: {
      none: "0",
      DEFAULT: "2px",
      full: "9999px",
    },

    borderWidth: {
      DEFAULT: "1px",
      0: "0",
      2: "2px",
    },

    // A.1: borders instead of shadows. The one exception is the hard offset a
    // card grows on hover, and it has no blur.
    boxShadow: {
      none: "none",
      card: "0 2px 0 0 rgb(var(--ink))",
    },

    extend: {
      // A.4 sets the rhythm at 4px with 4 8 12 16 24 32 48 64 96 128 as the
      // layout steps, which are 1 2 3 4 6 8 12 16 24 32 in tailwind units and
      // already in the default scale. The scale is not narrowed to them because
      // component sizes in A.5 (button 40/48/56, touch target 44) sit outside
      // the rhythm and still have to be expressible.
      maxWidth: {
        container: "1200px",
        // A.3: a line of text is 60 to 75 characters.
        narrow: "68ch",
      },
      transitionDuration: {
        // A.6: the only three durations in the design.
        DEFAULT: "120ms",
        panel: "180ms",
        reveal: "300ms",
      },
      transitionTimingFunction: {
        DEFAULT: "ease-out",
      },
    },
  },

  // The focus ring in A.2 is an outline, not a box-shadow. Leaving the ring
  // plugins on would put tailwind's default blue and white into the built css
  // as hex literals nothing on the site ever uses.
  corePlugins: {
    ringWidth: false,
    ringColor: false,
    ringOffsetWidth: false,
    ringOffsetColor: false,
  },

  plugins: [],
};
