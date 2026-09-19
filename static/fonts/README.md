# Fonts

Self hosted. `tech.md` §2 bans third party font hosts on public pages, so
nothing here may be replaced by a link to Google Fonts. The three families and
the weights are frozen in `ROSE.md` B.4.

| Family | Role | Weights | Subsets | Licence |
|---|---|---|---|---|
| Rubik | display: `h1`, `h2`, `PRAWO JAZDY`, the figures, the wordmark | 800 italic | latin, latin-ext, cyrillic, cyrillic-ext | SIL OFL 1.1 |
| Nunito | text: paragraphs, buttons, fields, the menu, `h3`, prices | 400–800 | latin, latin-ext, cyrillic, cyrillic-ext | SIL OFL 1.1 |
| Caveat | handwriting: margin notes, eyebrows, photo captions, the slogan | 600–700 | latin, latin-ext, cyrillic, cyrillic-ext | SIL OFL 1.1 |

All three are variable woff2 sliced to the weight range in use. The slice is
what keeps them small, and asking the api for a range rather than a list of
weights is what makes one file cover 400 through 800 instead of five.

`latin-ext` carries the Polish diacritics (ł ą ę ś ć ż ź ń), `cyrillic` and
`cyrillic-ext` the Russian and Ukrainian versions of the site.

## All three carry cyrillic, and that is the point

The site is in three languages, and the fault this table closes has been back
twice. Public Sans, the text face before core v25, had no cyrillic at all, so
every paragraph on `/ru/` and `/uk/` fell back to the system sans. Archivo, the
display face until core v29, had none either, so the headings kept doing it
after the paragraphs stopped.

`scripts/check_fonts.py` runs in CI and fails the build if a linked face stops
covering `ąćęłńóśźż ĄĆĘŁŃÓŚŹŻ` or the Russian and Ukrainian alphabets.

## Refreshing them

```
python -m scripts.brand.fetch_fonts          download the woff2 files
python -m scripts.brand.fetch_fonts --css    print the @font-face blocks
```

The script asks the css2 api with a modern browser user agent, keeps the four
subsets in use, and writes the files under the names `app.css` links.

**The order of the `@font-face` blocks is load bearing.** Where two subsets
claim the same character, the face declared *last* wins, and only one of the
two files carries the glyph: `cyrillic-ext` claims `U+0460-052F`, which
swallows the Ukrainian `ґ` at `U+0490`, while only `cyrillic` has it. So the
blocks go rarest first — cyrillic-ext, cyrillic, latin-ext, latin — and the
common subset wins every overlap. Tidying that list into alphabetical order
drops `ґ` into the system sans on every Ukrainian page.

## Weight

Roughly 205 KB reaches a Polish visitor (latin plus latin-ext across the three
families), and the Russian and Ukrainian pages swap latin-ext for cyrillic.
Caveat is the heavy one: a script face carries far more outline per glyph than
a sans. It is worth it — the handwriting is the owner's own voice on the page,
`ROSE.md` B.4 — but it is the first thing to look at if the budget tightens.
