# Legacy url table

The site this one replaces is `oskostrycharz.pl` — a single page with anchor
navigation. There is no page export to import, because there were no pages:
everything lived in one document, and its content is transcribed in
`OSTRYCHARZ.md` part A instead.

What is left here is `redirects.csv`, the old url space mapped onto the new one.

It has two halves and `apps/core/redirects.py` splits them:

- rows without a `#` are real request paths. `load_redirects()` writes them into
  `django.contrib.redirects` and the middleware answers them 301.
- rows with a `#` are the anchors of the old one-page site. A browser never
  sends a fragment, so no server can redirect one. `fragment_map()` hands them
  to the home page and `static/js/app.js` performs the jump on arrival.

Both halves come out of the same file so the table cannot drift in two places.

Run the loader with:

    docker compose exec web python manage.py load_redirects
