# Fonts

Self hosted. tech.md section 2 bans third party font hosts on public pages, so
nothing here may be replaced by a link to Google Fonts. The three families and
the weights are frozen in FRONTEND.md A.3.

| Family | Role | Weights | Subsets | Licence |
|---|---|---|---|---|
| Archivo | display: h1, h2, big numbers, category codes | 700, 800 | latin, latin-ext | SIL OFL 1.1 |
| Archivo Expanded | the `display` step of the scale | 800 | latin, latin-ext | SIL OFL 1.1 |
| Public Sans | text: paragraphs, lists, fields, buttons | 400, 600 | latin, latin-ext | SIL OFL 1.1 |
| Roboto Mono | data: prices, phones, dates, hours, labels | 400, 500 | latin, latin-ext, cyrillic, cyrillic-ext | Apache 2.0 |

All four are variable woff2 sliced to the weight range in use. The slice is
what keeps them small: the full two axis Archivo is 86 KB for one subset,
against 31 KB once it is cut to 700–800, and the expanded instance is another
12 KB on top. Everything together is 244 KB, of which a polish page loads the
`latin` and `latin-ext` half.

Archivo Expanded is not a separate family. Archivo carries a width axis, so the
expanded file is declared under the same `font-family` with
`font-stretch: 125%` and the browser picks it when the `.display` class asks.

`latin-ext` is what carries the polish diacritics (ł ą ę ś ć ż ź ń), `cyrillic`
and `cyrillic-ext` the russian and ukrainian versions of the site.

**Archivo and Public Sans have no cyrillic.** Neither family ships those
glyphs at all, so on `/ru/` and `/uk/` every heading and paragraph falls back to
the system sans. See the CONTRACT GAP in `static/src/css/app.css`.

## Refreshing a face

`@font-face` blocks live in `static/src/css/app.css`. To pull a subset again,
ask the css2 api for the exact weight range with a modern browser user agent,
keep the `unicode-range` that came back with it, and drop the file here under
the same name:

```
https://fonts.googleapis.com/css2?family=Archivo:wght@700..800&display=swap
https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@125,800&display=swap
https://fonts.googleapis.com/css2?family=Public+Sans:wght@400..600&display=swap
https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400..500&display=swap
```
