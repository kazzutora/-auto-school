/** @type {import('tailwindcss').Config} */
// Design tokens are frozen in ROSE.md part B, which replaced REDESIGN.md part B
// at core v29. Where they disagree ROSE.md wins — the older parts stay in the
// repository as the record of why the old decisions were what they were, not as
// a source of values.
//
// Every colour resolves to a CSS variable defined in static/src/css/app.css.
// That is what lets the dark theme be a swap of roles rather than a second set
// of utilities: the class stays bg-brand-100, the variable underneath changes.
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
    // Replacing rather than extending: a 2xl breakpoint that is not in the
    // contract has no business being reachable.
    screens: {
      sm: "480px",
      md: "768px",
      lg: "1024px",
      xl: "1280px",
    },

    // B.2 as amended at core v43. One red family, one blue, an ink ramp, a
    // hairline and two states.
    // Nothing else, and nothing from the palette this replaced: with no
    // `primary`, `accent`, `paper` or `surface` here, a leftover `bg-paper` in
    // a template generates nothing and shows up, rather than quietly painting
    // the wrong colour.
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

      brand: {
        // Card faces and the page ground. B.8: no section is white.
        50: token("brand-50"),
        100: token("brand-100"),
        // The pink of the tiles, the icon rings and the brush strokes. Ink on
        // it is 10.0; white on it is 1.69 and forbidden outright.
        200: token("brand-200"),
        // Action, and headings of 24px and up. Not small text: on the page it
        // measures 4.08, which B.3 allows a heading and refuses a paragraph.
        DEFAULT: token("brand-500"),
        500: token("brand-500"),
        // The button's hover fill. A fill, so it is the same crimson in both
        // themes.
        600: token("brand-600"),
        // The crimson as text: a link, a price, a small red line. One token
        // for the fill and the text would have made every hovered button in
        // the dark theme unreadable — B.2 lightens the red text there to
        // #FF8FAB so it reads on the near-black page, and white on that is
        // 1.90.
        link: token("brand-link"),
        // The crimson of the school's own mark.
        700: token("brand-700"),
        // Wine: one dark band on a page, never two.
        900: token("brand-900"),
      },

      ink: {
        DEFAULT: token("ink"),
        500: token("ink-500"),
        // Disabled text and hairlines only, below the body threshold on
        // purpose.
        300: token("ink-300"),
      },

      // What sits on a crimson fill. It does not swap with the theme, because
      // the fill does not either.
      fixed: {
        paper: token("fixed-paper"),
        ink: token("fixed-ink"),
      },

      // What sits on the wine band.
      wine: {
        DEFAULT: token("on-wine"),
        muted: token("on-wine-muted"),
      },

      state: {
        ok: token("state-ok"),
        warn: token("state-warn"),
        err: token("state-err"),
      },

      line: token("line"),
    },

    // B.4. Rubik carries the display steps and is always italic — the slant is
    // the face, not an emphasis, so app.css sets it once instead of every
    // heading asking for it. Nunito is the text face, Caveat the handwriting.
    // All three carry cyrillic, and scripts/check_fonts.py proves it on every
    // build.
    fontFamily: {
      display: ["Rubik", "ui-sans-serif", "system-ui", "sans-serif"],
      sans: ["Nunito", "ui-sans-serif", "system-ui", "sans-serif"],
      script: ["Caveat", "ui-sans-serif", "system-ui", "cursive"],
    },

    // B.4, the whole scale and only the scale. clamp() carries the step from
    // the 320px phone to the 1280px desktop, so there are no per-breakpoint
    // type utilities to keep in step.
    fontSize: {
      display: ["clamp(3rem, 8vw, 6rem)", { lineHeight: "0.95", letterSpacing: "-0.02em" }],
      h1: ["clamp(2.25rem, 5vw, 3.75rem)", { lineHeight: "1", letterSpacing: "-0.01em" }],
      h2: ["clamp(1.75rem, 3.2vw, 2.5rem)", { lineHeight: "1.05", letterSpacing: "0" }],
      h3: ["1.25rem", { lineHeight: "1.25", letterSpacing: "0" }],
      // The handwritten note in the margin of a section.
      script: ["clamp(1.5rem, 3vw, 2.25rem)", { lineHeight: "1.1" }],
      "script-sm": ["1.25rem", { lineHeight: "1.15" }],
      "body-lg": ["1.125rem", { lineHeight: "1.6" }],
      body: ["1rem", { lineHeight: "1.65" }],
      small: ["0.875rem", { lineHeight: "1.5" }],
      label: ["0.8125rem", { lineHeight: "1.2", letterSpacing: "0.06em" }],
      // Prices, phone numbers and the figures in the stat band: Nunito 800
      // with tabular figures, B.4.
      data: ["1rem", { lineHeight: "1.05", letterSpacing: "-0.01em" }],
      "data-lg": ["1.5rem", { lineHeight: "1.05", letterSpacing: "-0.01em" }],
      "data-xl": ["2rem", { lineHeight: "1.05", letterSpacing: "-0.01em" }],
      "data-2xl": ["2.5rem", { lineHeight: "1.05", letterSpacing: "-0.01em" }],
    },

    // B.4 uses Rubik 800, Nunito 400/600/700/800 and Caveat 600/700. The woff2
    // subsets are sliced to those ranges, so a weight outside this list would
    // be synthesised by the browser.
    fontWeight: {
      normal: "400",
      semibold: "600",
      bold: "700",
      extrabold: "800",
    },

    // B.5. A card is 20, a tile 18, a field 14, a polaroid 4, and a button is
    // a pill — the shape the owner's own mockup gives every control.
    borderRadius: {
      none: "0",
      polaroid: "4px",
      DEFAULT: "14px",
      field: "14px",
      image: "16px",
      tile: "18px",
      card: "20px",
      hero: "28px",
      full: "999px",
    },

    borderWidth: {
      DEFAULT: "1px",
      0: "0",
      // B.5 draws the outline button and a focused field at 1.5px.
      1.5: "1.5px",
      2: "2px",
    },

    // Exactly two levels, and no third is to be added. Both are neutral black
    // at low alpha. They were wine — a warm shadow under a warm page — and a
    // warm shadow under a neutral one is a smudge of a colour the palette no
    // longer contains: at core v43 the page is grey-white and the only warm
    // thing on it is the red itself.
    boxShadow: {
      none: "none",
      card: "0 1px 2px rgba(16, 18, 22, .05), 0 14px 30px -18px rgba(16, 18, 22, .22)",
      "card-hover": "0 2px 4px rgba(16, 18, 22, .07), 0 22px 40px -20px rgba(16, 18, 22, .30)",
    },

    extend: {
      // B.5 sets the rhythm at 4px with 4 8 12 16 24 32 48 64 96 128 as the
      // layout steps, which are 1 2 3 4 6 8 12 16 24 32 in tailwind units and
      // already in the default scale. The scale is not narrowed to them because
      // component sizes in B.5 (button 44/52/60, field 52, badge 26) sit
      // outside the rhythm and still have to be expressible.
      maxWidth: {
        container: "1280px",
        // B.4: a line of text is 60 to 72 characters.
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

      // REDESIGN.md C.3 names what may move — the motion contract survived the
      // palette change untouched. transform, colour, background, border and
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
