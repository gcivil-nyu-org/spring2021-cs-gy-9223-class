from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes
from django.core.mail import EmailMultiAlternatives, send_mail
from django import template
from django.conf import settings

import logging

logger = logging.getLogger(__name__)


def send_reset_password_email(request, email):
    user = get_user_model().objects.get(email=email)
    host_name = request.get_host()
    base_url = host_name + "/user/reset_password/"
    if str(host_name).startswith("127.0.0.1"):
        base_url = "http://" + base_url
    else:
        base_url = "https://" + base_url
    c = {
        "base_url": base_url,
        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
        "token": PasswordResetTokenGenerator().make_token(user),
    }
    htmltemp = template.loader.get_template("reset_password_template.html")
    html_content = htmltemp.render(c)
    email_subject = "Reset Your DineLine Password!"
    logger.info("Send email to: %s", user.email)
    email = EmailMultiAlternatives(email_subject, to=[user.email])
    email.attach_alternative(html_content, "text/html")
    return email.send()


def send_verification_email(request, email):
    user = get_user_model().objects.get(email=email)
    host_name = request.get_host()
    base_url = host_name + "/user/verification/"
    if str(host_name).startswith("127.0.0.1"):
        base_url = "http://" + base_url
    else:
        base_url = "https://" + base_url

    logger.info(base_url)
    c = {
        "base_url": base_url,
        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
        "token": PasswordResetTokenGenerator().make_token(user),
    }
    htmltemp = template.loader.get_template("verify_user_template.html")
    html_content = htmltemp.render(c)
    email_subject = "Verify your account!"
    logger.info("Send email to: %s", user.email)
    email = EmailMultiAlternatives(email_subject, to=[user.email])
    email.attach_alternative(html_content, "text/html")
    return email.send()


def send_feedback_email(request, email, subject, message):
    try:
        email_subject = "DineLine Feedback: " + subject
        email_message = "From: " + email + "\n" + message
        send_mail(
            email_subject,
            email_message,
            settings.EMAIL_HOST_USER,
            [settings.EMAIL_HOST_USER],
        )
        return True
    except Exception:
        return False


def send_verification_secondary_email(request, email):
    host_name = request.get_host()
    base_url = host_name + "/user/email/verification/"
    if str(host_name).startswith("127.0.0.1"):
        base_url = "http://" + base_url
    else:
        base_url = "https://" + base_url

    c = {
        "base_url": base_url,
        "uid": urlsafe_base64_encode(force_bytes(request.user.pk)),
        "encoded_email": urlsafe_base64_encode(force_bytes(email)),
        "token": PasswordResetTokenGenerator().make_token(request.user),
    }
    htmltemp = template.loader.get_template("verify_email_template.html")
    html_content = htmltemp.render(c)
    email_subject = "Verify your email!"
    email = EmailMultiAlternatives(email_subject, to=[email])
    email.attach_alternative(html_content, "text/html")
    return email.send()
