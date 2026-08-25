"""The app layout is frozen in tech.md section 3, one vertical slice per app."""

from django.apps import apps as django_apps

TECH_MD_SLICES = {
    "core",
    "courses",
    "leads",
    "people",
    "gallery",
    "links",
    "reviews",
}


def test_every_slice_from_tech_md_is_installed() -> None:
    installed = {config.label for config in django_apps.get_app_configs()}
    missing = TECH_MD_SLICES - installed
    assert not missing, f"slices missing from INSTALLED_APPS: {sorted(missing)}"


def test_every_slice_lives_under_the_apps_package() -> None:
    for label in TECH_MD_SLICES:
        assert django_apps.get_app_config(label).name == f"apps.{label}"
