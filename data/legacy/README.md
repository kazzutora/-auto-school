# Legacy export

tech.md section 15 describes an export of the old `naukajazdywielun.pl` site:
one markdown file per page, plus `redirects.csv` and `links.csv`.

**These course pages are a reconstruction, not that export.** The real one was
never added to the repository. Every file carries `source: reconstructed` in its
header, and `scripts/import_legacy.py` prints a warning for each one it reads.

What is faithful to tech.md and must stay that way when the real export lands:

- the fifteen slugs match the url map in section 5 and the redirect table in 4.8;
- all five source typos from the section 15 table appear verbatim, so the
  importer's correction is tested against real input rather than against itself;
- the two fragments section 15 reports as unreadable are marked, in the places
  it names: the first entitlement of `kat-a2` and the category D age range in
  `kwalifikacja-wstepna-przyspieszona`.

The prose itself is written for this repository and is not the school's copy.
Replace these files with the real export, keep the header block, and rerun
`python -m scripts.import_legacy`. Nothing in the importer needs to change.

`redirects.csv` and `links.csv` are still missing. The redirect table is frozen
in tech.md section 4.8, so the data migration that fills
`django.contrib.redirects` can be written from there.
