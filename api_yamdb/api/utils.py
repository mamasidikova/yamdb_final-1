import uuid

from django.core.mail import EmailMessage


def send_email(username, email, code):
    email_body = (f'Привет {username}, твой код '
                  f'подтверждения: {code}!')
    email = EmailMessage(
        subject='Код подтверждения',
        body=email_body,
        to=[email]
    )
    email.send()


def code_gen():
    return str(uuid.uuid4()).split('-')[0]
