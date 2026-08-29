"""The enrolment form, DEV.md S3.1.

The old site had no form at all — this is the main breakage the rebuild fixes,
so the form is deliberately short. Everything the school actually needs to call
someone back is name, phone and which course; the rest is optional.
"""

from typing import Any, cast

from django import forms
from django.utils.translation import gettext_lazy as _

from apps.courses.models import Course, CourseIntake
from apps.leads.models import Lead
from apps.leads.services import normalize_phone

# A field no human sees and every naive bot fills in, DEV.md S3.1.
HONEYPOT = "website"

# The field box from FRONTEND.md A.5, the same one <c-input> draws: 48px, a
# line.soft hairline, and a second pixel of ink on focus that arrives as an
# inset shadow so the layout does not shift.
#
# It is repeated here because <c-field> hands rendering to django, and a django
# widget knows nothing about the design system unless the form tells it. The
# alternative — styling bare inputs in the base layer — would reach into the
# shared stylesheet from a feature slice.
FIELD_CLASS = (
    "h-12 w-full rounded border border-line-soft bg-paper px-4 text-ink transition "
    "focus:border-ink focus:shadow-field"
)
TEXTAREA_CLASS = (
    "w-full rounded border border-line-soft bg-paper px-4 py-3 text-ink transition "
    "focus:border-ink focus:shadow-field"
)
ERROR_CLASS = "border-state-err"


class LeadForm(forms.ModelForm):
    """Name, phone, course, consent. Everything else is optional.

    The honeypot is a real form field rather than a hand written input, so it
    is validated and cleaned like any other and the view only has to ask
    whether it came back filled.
    """

    website = forms.CharField(
        required=False,
        label=_("Zostaw to pole puste"),
        widget=forms.TextInput(
            attrs={
                # Hidden from people without hiding it from a bot: type=hidden
                # is the first thing a scraper skips.
                "class": "sr-only",
                "tabindex": "-1",
                "autocomplete": "off",
                "aria-hidden": "true",
            }
        ),
    )

    class Meta:
        model = Lead
        fields = (
            "first_name",
            "last_name",
            "phone",
            "email",
            "course",
            "intake",
            "message",
            "consent_rodo",
            "consent_marketing",
        )
        labels = {
            "first_name": _("Imię"),
            "last_name": _("Nazwisko"),
            "phone": _("Telefon"),
            "email": _("E-mail"),
            "course": _("Kurs"),
            "message": _("Wiadomość"),
        }
        help_texts = {
            "email": _("Nieobowiązkowo. Wyślemy na niego potwierdzenie."),
            "phone": _("Oddzwonimy pod ten numer."),
        }
        widgets = {
            "message": forms.Textarea(attrs={"rows": 4}),
            # Carried, never chosen: it arrives from the term the visitor
            # clicked and the form has no business asking about it again.
            "intake": forms.HiddenInput(),
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        # Only courses somebody could actually enrol on. The queryset is set
        # here rather than on the model field so an inactive course disappears
        # from the form the moment the owner unticks it.
        course = cast(forms.ModelChoiceField, self.fields["course"])
        course.queryset = Course.objects.filter(is_active=True).order_by("kind", "order", "id")
        course.required = False
        course.empty_label = _("Jeszcze nie wiem")

        intake = cast(forms.ModelChoiceField, self.fields["intake"])
        intake.queryset = CourseIntake.objects.all()
        intake.required = False

        self.fields["first_name"].required = True
        self.fields["phone"].required = True

        # Consent is the one box that has to be ticked, DEV.md S3.1. Django
        # makes a BooleanField optional by default, which would let a lead
        # through without it.
        self.fields["consent_rodo"].required = True
        self.fields["consent_rodo"].error_messages["required"] = _(
            "Bez tej zgody nie możemy się z Tobą skontaktować."
        )
        self.fields["consent_marketing"].required = False

        # Last, and it matters: _dress_widgets reads self.errors to mark the
        # fields that failed, and touching errors on a bound form runs the
        # validation there and then. Called any earlier it would validate
        # against a form whose required flags are not all set yet, and consent
        # would stop being mandatory.
        self._dress_widgets()

    def _dress_widgets(self) -> None:
        """Give every rendered widget the box A.5 describes.

        The honeypot keeps its own sr-only class: it is the one field that must
        not look like a field. Checkboxes are drawn by <c-checkbox> in the
        template and never reach here either.
        """
        for name, field in self.fields.items():
            if name == HONEYPOT or isinstance(field.widget, forms.CheckboxInput):
                continue
            if isinstance(field.widget, forms.HiddenInput):
                continue

            classes = TEXTAREA_CLASS if isinstance(field.widget, forms.Textarea) else FIELD_CLASS
            if self.is_bound and self.errors.get(name):
                classes = f"{classes} {ERROR_CLASS}"
            field.widget.attrs["class"] = classes

    def clean_phone(self) -> str:
        """One canonical +48XXXXXXXXX, however the visitor typed it.

        Rejected rather than stored raw: a number the school cannot dial is a
        lead they cannot answer, and finding that out at call time is worse
        than saying so here.
        """
        normalized = normalize_phone(self.cleaned_data.get("phone"))
        if not normalized:
            raise forms.ValidationError(_("Podaj polski numer telefonu, np. 605 065 795."))
        return normalized

    @property
    def looks_automated(self) -> bool:
        """True when the honeypot came back filled.

        Read after is_valid(): the field is not required, so a filled honeypot
        never makes the form invalid. DEV.md S3.1 wants the sender to see the
        same success page either way.
        """
        return bool(self.cleaned_data.get(HONEYPOT))


def initial_from_query(params: Any) -> dict[str, Any]:
    """Prefill the course from ?course= or ?intake=, DEV.md S3.1.

    Both are ids handed over by a link the visitor clicked, so an unknown or
    malformed one is not an error — it just means nothing is preselected.
    """
    initial: dict[str, Any] = {}

    intake_id = params.get("intake")
    if intake_id:
        intake = CourseIntake.objects.filter(pk=_as_int(intake_id)).select_related("course").first()
        if intake:
            initial["course"] = intake.course_id
            initial["intake"] = intake.pk
            return initial

    course_id = params.get("course")
    if course_id:
        course = Course.objects.filter(pk=_as_int(course_id), is_active=True).first()
        if course:
            initial["course"] = course.pk

    return initial


def _as_int(value: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
