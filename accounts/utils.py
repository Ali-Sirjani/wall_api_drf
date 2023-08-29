from functools import wraps

from django.contrib.auth import signals
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib import messages

from axes.handlers.proxy import AxesProxyHandler
from axes.helpers import get_lockout_response

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


def custom_axes_dispatch_with_source(request_from):
    """
    A custom decorator that adds source information to lockout responses.

    Args:
        request_from (str): The source of the request.

    Usage:
        @custom_axes_dispatch_with_source(request_from='web')
        def my_view(request):
            # Your view logic here
    """
    def inner(func):
        @wraps(func)
        def custom_inner(request, *args, **kwargs):
            if AxesProxyHandler.is_allowed(request):
                return func(request, *args, **kwargs)

            return get_lockout_response(request, credentials={'request_from': request_from})

        return custom_inner

    return inner


def custom_lockout_response(request, credentials, *args, **kwargs):
    if credentials.get('request_from') == 'api':
        return JsonResponse({"status": "Locked out due to too many login failures"}, status=403)
    else:
        messages.error(request, 'You are locked for too many requests')
        return redirect('accounts:login')
