from django.contrib.auth import signals

from .models import CustomUser


def signal_failed(request, phone_number):
    """
    Sends a signal indicating a failed user login attempt.

    This function triggers a custom signal `user_login_failed` when a user login attempt fails.

    Args:
        request (HttpRequest): The HTTP request object representing the login attempt.
        phone_number (str): The phone number associated with the login attempt.

    Example:
        signal_failed(request, '1234567890')
    """
    signals.user_login_failed.send(
                    sender=CustomUser,
                    request=request,
                    credentials={
                        'phone_number': phone_number,
                    },
                )
