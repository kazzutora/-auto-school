"""seo_meta and jsonld tags, tech.md section 8."""

import json

from django.template import Context, Template
from django.test import RequestFactory

from apps.core.seo import Seo


def render(template: str, context: dict) -> str:
    return Template("{% load seo %}" + template).render(Context(context))


def make_seo(**overrides: object) -> Seo:
    base = {
        "title": "Kat. B — OSK Ostrycharz Wieluń",
        "description": "Kurs prawa jazdy kategorii B w Wieluniu.",
        "canonical": "https://oskostrycharz.pl/kursy/kat-b/",
    }
    return Seo(**{**base, **overrides})  # type: ignore[arg-type]


def test_jsonld_renders_each_block() -> None:
    seo = make_seo(jsonld=[{"@type": "DrivingSchool"}, {"@type": "Course"}])
    out = render("{% jsonld %}", {"seo": seo})

    assert out.count('<script type="application/ld+json">') == 2
    assert '"DrivingSchool"' in out


def test_jsonld_payload_cannot_close_the_script_element() -> None:
    """A value carrying </script> must not break out of the block."""
    seo = make_seo(jsonld=[{"name": "</script><script>alert(1)</script>"}])
    out = render("{% jsonld %}", {"seo": seo})

    assert out.count("<script") == 1
    assert "</script><script>" not in out
    assert out.count("</script>") == 1  # only the real closing tag


def test_jsonld_stays_valid_json_after_escaping() -> None:
    seo = make_seo(jsonld=[{"name": "A & B <c>"}])
    out = render("{% jsonld %}", {"seo": seo})

    payload = out.split(">", 1)[1].rsplit("</script>", 1)[0]
    assert json.loads(payload) == {"name": "A & B <c>"}


def test_jsonld_is_empty_without_data() -> None:
    assert render("{% jsonld %}", {"seo": make_seo()}) == ""
    assert render("{% jsonld %}", {}) == ""


def test_seo_meta_emits_the_contract_fields() -> None:
    request = RequestFactory().get("/kursy/kat-b/")
    out = render("{% seo_meta %}", {"seo": make_seo(), "request": request})

    assert "<title>Kat. B — OSK Ostrycharz Wieluń</title>" in out
    assert 'name="description"' in out
    assert 'rel="canonical"' in out
    assert 'name="robots" content="index,follow"' in out


def test_seo_meta_emits_hreflang_for_every_language_and_x_default() -> None:
    request = RequestFactory().get("/kursy/kat-b/")
    out = render("{% seo_meta %}", {"seo": make_seo(), "request": request})

    for code in ("pl", "ru", "uk", "x-default"):
        assert f'hreflang="{code}"' in out


def test_seo_meta_survives_a_missing_request() -> None:
    out = render("{% seo_meta %}", {"seo": make_seo()})
    assert "hreflang" not in out
    assert "<title>" in out
