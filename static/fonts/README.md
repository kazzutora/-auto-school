# Fonts

Self hosted. tech.md section 2 bans third party font hosts on public pages, so
nothing here may be replaced by a link to Google Fonts.

| Family | Role | Licence |
|---|---|---|
| Roboto Condensed | headings, condensed grotesque | SIL Open Font Licence 1.1 |
| Source Sans 3 | body text, humanist sans | SIL Open Font Licence 1.1 |

Both are variable woff2 covering weight 400 to 700, split into four subsets:
`latin`, `latin-ext` (polish ł ą ę ś ć ż ź ń), `cyrillic` and `cyrillic-ext`
(the russian and ukrainian versions of the site). The `@font-face` blocks live
in `static/src/css/app.css` with `font-display: swap`.

To refresh a subset, pull the woff2 from the Google Fonts css2 api with a modern
browser user agent, drop it here under the same name and keep the unicode-range
that came with it.
