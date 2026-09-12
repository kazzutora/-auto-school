"""factory_boy factories, tech.md section 3."""

import random
from io import BytesIO

import factory
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFilter

from apps.core.models import SiteSettings
from apps.gallery.models import Certificate, GalleryImage
from apps.leads.models import Lead


def image_bytes(width: int = 1200, height: int = 800, colour: str = "#5B47A8") -> ContentFile:
    """A real image, so imagekit has something to resize."""
    buffer = BytesIO()
    Image.new("RGB", (width, height), colour).save(buffer, format="PNG")
    return ContentFile(buffer.getvalue(), name="sample.png")


class GalleryImageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = GalleryImage

    section = GalleryImage.Section.SCHOOL
    alt = factory.Sequence(lambda n: f"Zdjęcie ośrodka {n}")
    caption = ""
    order = factory.Sequence(lambda n: n * 10)
    is_published = True
    image = factory.LazyFunction(image_bytes)


class CertificateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Certificate

    title = factory.Sequence(lambda n: f"Certyfikat {n}")
    issuer = "Urząd"
    order = factory.Sequence(lambda n: n * 10)
    is_published = True
    image = factory.LazyFunction(image_bytes)


class LeadFactory(factory.django.DjangoModelFactory):
    """A lead as the form leaves it: consent given, nothing notified yet."""

    class Meta:
        model = Lead

    first_name = "Anna"
    last_name = factory.Sequence(lambda n: f"Kowalska {n}")
    phone = "+48605065795"
    email = factory.Sequence(lambda n: f"anna{n}@example.com")
    preferred_language = "pl"
    message = ""
    consent_rodo = True
    status = Lead.Status.NEW


def notify_site(recipients: str = "biuro@example.com") -> SiteSettings:
    """SiteSettings with somebody to notify, tech.md section 6."""
    site = SiteSettings.get_solo()
    site.short_name = "OSK Ostrycharz"
    site.legal_name = "OSK Ostrycharz — Ośrodek Szkolenia Kierowców"
    site.street = "ul. Asnyka 7"
    site.postal_code = "98-300"
    site.city = "Wieluń"
    site.email = "oskostrycharz@poczta.onet.pl"
    site.phone_primary = "691 570 489"
    site.lead_notify_emails = recipients
    site.save()
    return site


def photo_bytes(width: int = 1600, height: int = 1200) -> ContentFile:
    """An image that compresses like a photograph, not like a flat swatch.

    The weight budget in DEV.md S6.1 is meaningless against a single colour:
    it would shrink to a few hundred bytes and any regression would still fit.
    """
    picture = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(picture)
    for row in range(height):
        draw.line([(0, row), (width, row)], fill=(60 + row // 12, 90 + row // 20, 140 - row // 30))
    shapes = random.Random(20260826)
    for _ in range(400):
        left, top = shapes.randint(0, width), shapes.randint(0, height)
        draw.ellipse(
            [left, top, left + shapes.randint(20, 160), top + shapes.randint(20, 160)],
            fill=(shapes.randint(40, 220), shapes.randint(40, 220), shapes.randint(40, 220)),
        )

    buffer = BytesIO()
    picture.filter(ImageFilter.GaussianBlur(1.5)).save(buffer, format="JPEG", quality=82)
    return ContentFile(buffer.getvalue(), name="photo.jpg")
