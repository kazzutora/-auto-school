"""factory_boy factories, tech.md section 3."""

from io import BytesIO

import factory
from django.core.files.base import ContentFile
from PIL import Image

from apps.gallery.models import Certificate, GalleryImage


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
