from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import translation


def send_welcome_email(user):
    language = user.preferred_language

    with translation.override(language):
        subject = render_to_string(
            "users/emails/welcome_subject.txt",
            {"user": user},
        ).strip()

        body = render_to_string(
            "users/emails/welcome_body.txt",
            {"user": user},
        )

        send_mail(subject=subject,
                  message=body,
                  from_email=settings.DEFAULT_FROM_EMAIL,
                  recipient_list=[user.email],
                  fail_silently=False)
