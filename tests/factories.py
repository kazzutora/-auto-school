"""factory_boy factories, tech.md section 3."""

from io import BytesIO

import factory
from django.core.files.base import ContentFile
from PIL import Image

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
    site.short_name = "OSK Nawrocki"
    site.legal_name = "OKiDZ Adam Nawrocki, Mariola Nawrocka S.C."
    site.street = "ul. Zielona 45"
    site.postal_code = "98-300"
    site.city = "Wieluń"
    site.email = "osk.adam.nawrocki@wp.pl"
    site.phone_primary = "43 843 29 11"
    site.lead_notify_emails = recipients
    site.save()
    return site
