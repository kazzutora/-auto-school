"""The supported markdown subset, tech.md section 4."""

from apps.core.markdown import render_markdown


def test_paragraphs_are_split_on_blank_lines() -> None:
    assert render_markdown("one\n\ntwo") == "<p>one</p><p>two</p>"


def test_wrapped_lines_join_into_one_paragraph() -> None:
    assert render_markdown("one\ntwo") == "<p>one two</p>"


def test_headings_start_at_h2() -> None:
    assert render_markdown("# Tytuł") == "<h2>Tytuł</h2>"
    assert render_markdown("## Podtytuł") == "<h3>Podtytuł</h3>"
    assert render_markdown("### Głębiej") == "<h4>Głębiej</h4>"
    assert render_markdown("##### Bardzo głęboko") == "<h4>Bardzo głęboko</h4>"


def test_unordered_list() -> None:
    rendered = render_markdown("- kat. B\n- kat. C")
    assert rendered == "<ul><li>kat. B</li><li>kat. C</li></ul>"


def test_ordered_list() -> None:
    rendered = render_markdown("1. PKK\n2. Kurs")
    assert rendered == "<ol><li>PKK</li><li>Kurs</li></ol>"


def test_lists_do_not_bleed_into_each_other() -> None:
    rendered = render_markdown("- a\n1. b")
    assert rendered == "<ul><li>a</li></ul><ol><li>b</li></ol>"


def test_inline_marks() -> None:
    expected = "<p><strong>mocno</strong> i <em>lekko</em></p>"
    assert render_markdown("**mocno** i *lekko*") == expected
    assert render_markdown("`kod`") == "<p><code>kod</code></p>"


def test_link_keeps_label_and_href() -> None:
    rendered = render_markdown("[info-car](https://info-car.pl/)")
    assert rendered == '<p><a href="https://info-car.pl/">info-car</a></p>'


def test_ampersand_in_a_url_survives_escaping() -> None:
    rendered = render_markdown("[x](https://example.com/?a=1&b=2)")
    assert 'href="https://example.com/?a=1&amp;b=2"' in rendered


def test_empty_source_renders_nothing() -> None:
    assert render_markdown("") == ""
    assert render_markdown("   \n\n  ") == ""
