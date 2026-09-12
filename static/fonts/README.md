# Fonts

Self hosted. tech.md section 2 bans third party font hosts on public pages, so
nothing here may be replaced by a link to Google Fonts. The three families and
the weights are frozen in `REDESIGN.md` B.3.

| Family | Role | Weights | Subsets | Licence |
|---|---|---|---|---|
| Archivo | display: h1, h2, group names | 700, 800 | latin, latin-ext | SIL OFL 1.1 |
| Archivo Expanded | the `display` step of the scale | 800 | latin, latin-ext | SIL OFL 1.1 |
| Manrope | text: paragraphs, lists, fields, buttons, h3 | 400, 500, 700 | latin, latin-ext, cyrillic, cyrillic-ext | SIL OFL 1.1 |
| Roboto Mono | data: prices, phones, dates, hours, labels | 400, 500 | latin, latin-ext, cyrillic, cyrillic-ext | Apache 2.0 |

All are variable woff2 sliced to the weight range in use. The slice is what
keeps them small: the full two axis Archivo is 86 KB for one subset, against
31 KB once it is cut to 700–800.

Archivo Expanded is not a separate family. Archivo carries a width axis, so the
expanded file is declared under the same `font-family` with
`font-stretch: 125%` and the browser picks it when `.display`, `h1` or `h2`
asks for it.

`latin-ext` is what carries the polish diacritics (ł ą ę ś ć ż ź ń), `cyrillic`
and `cyrillic-ext` the russian and ukrainian versions of the site.

## Manrope replaced Public Sans at core v25

`REDESIGN.md` B.3 changed the text face, and the swap closed most of a
CONTRACT GAP on the way out. Public Sans ships no cyrillic glyphs at all, so on
`/ru/` and `/uk/` every paragraph on the site fell back to the system sans.
Manrope carries both cyrillic subsets, so the body text on those two languages
is now the same face as on the polish one.

**What is still open: Archivo has no cyrillic either.** Headings on `/ru/` and
`/uk/` fall back to the system sans. That is one face on two languages rather
than the whole page, and closing it properly means either a fourth family for
cyrillic headings or swapping the display face — which would take the school's
own wordmark with it, because the lockup in `static/brand/` is set in Archivo.
Owner's call.

## Refreshing a face

`@font-face` blocks live in `static/src/css/app.css`. To pull a subset again,
ask the css2 api for the exact weight range with a modern browser user agent,
keep the `unicode-range` that came back with it, and drop the file here under
the same name:

```
https://fonts.googleapis.com/css2?family=Archivo:wght@700..800&display=swap
https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@125,800&display=swap
https://fonts.googleapis.com/css2?family=Manrope:wght@400..700&display=swap
https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400..500&display=swap
```
