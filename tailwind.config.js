/** @type {import('tailwindcss').Config} */
// Design tokens are frozen in REDESIGN.md part B, which replaced FRONTEND.md
// part A at core v25. Where the two disagree, REDESIGN.md wins — part A is kept
// in the repository as the record of why the old decisions were what they were,
// not as a source of values.
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
  // and have to exist before the first page uses one, so they are kept by name
  // rather than by whether a template happens to mention them yet.
  //
  // The motion classes need no entry here: static/src/css/motion.css carries no
  // @tailwind directive, so nothing in it is generated and nothing is purged.
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
    // B.4. Replacing rather than extending: a 2xl breakpoint that is not in the
    // contract has no business being reachable.
    screens: {
      sm: "480px",
      md: "768px",
      lg: "1024px",
      xl: "1280px",
    },

    // B.2. Two accents with separated roles, a ground, two card surfaces and an
    // ink ramp — nothing else.
    //
    // Replacing rather than extending is deliberate: with no `gray` in the
    // palette, `text-gray-400` cannot be typed by accident. The price is two
    // dead literals in the built css. Preflight resolves its own placeholder
    // colour through theme('colors.gray.400', '#9ca3af') and its shadow
    // defaults through '#0000', so both fall back to the literal. Neither
    // paints anything: '#0000' is transparent, and the placeholder rule in
    // app.css matches preflight's selector and comes after it.
    colors: {
      transparent: "transparent",
      current: "currentColor",
      inherit: "inherit",

      // The page itself. Warm grey in the light theme, near black in the dark.
      paper: {
        DEFAULT: token("paper"),
        50: token("paper-50"),
        100: token("paper-100"),
      },

      // The white cards that sit on it.
      surface: {
        DEFAULT: token("surface"),
        muted: token("surface-muted"),
      },

      // Text, and the dark cards. One ramp does both because a dark card is
      // the ink token used as a ground — B.2's role swap in one value.
      ink: {
        DEFAULT: token("ink"),
        800: token("ink-800"),
        700: token("ink-700"),
        500: token("ink-500"),
        // Disabled text and hairlines only. Below the body threshold on
        // purpose: WCAG exempts a disabled control, and a disabled button that
        // reads at full strength is a button people keep pressing.
        300: token("ink-300"),
      },

      // Action. The button that signs somebody up, the submit on a form.
      // Never a badge: B.1 splits the two accents by role and a blue badge
      // would say "press me" about a fact.
      primary: {
        DEFAULT: token("primary"),
        600: token("primary-600"),
        100: token("primary-100"),
      },

      // State. "Nabór otwarty", the slab under a word in the hero, the mark.
      // Never a button fill, for the mirror of the same reason.
      accent: {
        DEFAULT: token("accent"),
        600: token("accent-600"),
        100: token("accent-100"),
      },

      state: {
        ok: token("state-ok"),
        warn: token("state-warn"),
        err: token("state-err"),
      },

      line: {
        DEFAULT: token("line"),
        dark: token("line-dark"),
      },
    },

    // B.3. Display carries the width axis: font-stretch picks Expanded.
    fontFamily: {
      display: ["Archivo", "ui-sans-serif", "system-ui", "sans-serif"],
      sans: ["Manrope", "ui-sans-serif", "system-ui", "sans-serif"],
      mono: ["Roboto Mono", "ui-monospace", "SFMono-Regular", "monospace"],
    },

    // B.3, the whole scale and only the scale. clamp() carries the step from
    // the 320px phone to the 1280px desktop, so there are no per-breakpoint
    // type utilities to keep in step.
    fontSize: {
      display: ["clamp(2.5rem, 6vw, 4.5rem)", { lineHeight: "1.02", letterSpacing: "-0.02em" }],
      h1: ["clamp(2rem, 4.5vw, 3.5rem)", { lineHeight: "1.05", letterSpacing: "-0.02em" }],
      h2: ["clamp(1.6rem, 3vw, 2.25rem)", { lineHeight: "1.1", letterSpacing: "-0.01em" }],
      h3: ["1.25rem", { lineHeight: "1.25", letterSpacing: "0" }],
      "body-lg": ["1.125rem", { lineHeight: "1.6" }],
      body: ["1rem", { lineHeight: "1.65" }],
      small: ["0.875rem", { lineHeight: "1.5" }],
      label: ["0.75rem", { lineHeight: "1.2", letterSpacing: "0.1em" }],
      // B.3 gives data as a range from 1rem to 2.5rem. Four steps of it: a
      // price in a table, a start date in a row, a figure on a card, and the
      // pass-rate numbers that carry their own block.
      data: ["1rem", { lineHeight: "1.05", letterSpacing: "-0.01em" }],
      "data-lg": ["1.5rem", { lineHeight: "1.05", letterSpacing: "-0.01em" }],
      "data-xl": ["2rem", { lineHeight: "1.05", letterSpacing: "-0.01em" }],
      "data-2xl": ["2.5rem", { lineHeight: "1.05", letterSpacing: "-0.01em" }],
    },

    // B.3 uses exactly seven cuts: Archivo 700/800, Manrope 400/500/700,
    // Roboto Mono 400/500. The woff2 subsets are sliced to those ranges, so a
    // weight outside this list would be synthesised by the browser.
    fontWeight: {
      normal: "400",
      medium: "500",
      bold: "700",
      extrabold: "800",
    },

    // B.4. Five radii and the pill, and nothing between them: a card is 20,
    // a hero 28, a control 12, a picture inside a card 16.
    borderRadius: {
      none: "0",
      image: "16px",
      DEFAULT: "12px",
      card: "20px",
      hero: "28px",
      full: "999px",
    },

    borderWidth: {
      DEFAULT: "1px",
      0: "0",
      // B.5 draws a secondary button and a field at 1.5px.
      1.5: "1.5px",
      2: "2px",
    },

    // B.4: exactly two levels, and no third is to be added. Both are the same
    // near black at low alpha, so they read as one light source rather than as
    // two different rooms.
    boxShadow: {
      none: "none",
      card: "0 1px 2px rgba(27, 27, 32, .05), 0 12px 28px -20px rgba(27, 27, 32, .35)",
      "card-hover": "0 2px 4px rgba(27, 27, 32, .06), 0 20px 40px -24px rgba(27, 27, 32, .45)",
    },

    extend: {
      // B.4 sets the rhythm at 4px with 4 8 12 16 24 32 48 64 96 128 as the
      // layout steps, which are 1 2 3 4 6 8 12 16 24 32 in tailwind units and
      // already in the default scale. The scale is not narrowed to them because
      // component sizes in B.5 (button 44/52/60, field 52, badge 26) sit
      // outside the rhythm and still have to be expressible.
      maxWidth: {
        container: "1280px",
        // B.3: a line of text is 60 to 72 characters.
        narrow: "68ch",
      },

      // The three button heights in B.5 are 44, 52 and 60. 44 is h-11 already;
      // the other two fall in the gaps of the default scale, which jumps 12,
      // 14, 16. Named by their step rather than in brackets so the contract
      // value appears once and `h-[52px]` never has to be typed.
      spacing: {
        13: "3.25rem",
        15: "3.75rem",
        // The play target on a video card, B.5. 72px, between the scale's 64
        // and 80.
        18: "4.5rem",
      },

      // C.3 names what may move. transform, colour, background, border and
      // shadow are the whole list — a card lifts, a button fills, an arrow
      // travels. opacity is on it too, for the reveal.
      transitionProperty: {
        DEFAULT:
          "color, background-color, border-color, outline-color, box-shadow, transform, opacity",
      },

      // C.3's table, to the millisecond. Nothing picks a duration of its own.
      //
      // Read out of the variables app.css publishes rather than written twice.
      // static/src/css/motion.css is plain css and cannot call theme(), so the
      // durations had to exist as variables anyway; pointing the config at the
      // same ones is what stops `duration-card` and `var(--dur-card)` drifting.
      transitionDuration: {
        DEFAULT: "var(--dur)",
        card: "var(--dur-card)",
        header: "var(--dur-header)",
        tab: "var(--dur-tab)",
        menu: "var(--dur-menu)",
        panel: "var(--dur-panel)",
        hero: "var(--dur-hero)",
      },

      // C.3: one curve on the whole site. No springs, no bounces, no
      // ease-in-out mixed in.
      transitionTimingFunction: {
        DEFAULT: "cubic-bezier(.22, .61, .36, 1)",
      },
    },
  },

  // The focus ring in B.5 is an outline, not a box-shadow. Leaving the ring
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
