from django.utils.translation import gettext_lazy as _


def zarin_errors(payment_code):
    error_messages = ''

    if payment_code == -9:
        error_messages = _('Validation error')

    if payment_code == -10:
        error_messages = _('Terminal is not valid, please check merchant_id or ip address.')

    if payment_code == -11:
        error_messages = _('Terminal is not active, please contact our support team.')

    if payment_code == -12:
        error_messages = _('To many attempts, please try again later.')

    if payment_code == -15:
        error_messages = _('Terminal user is suspend : (please contact our support team).')

    if payment_code == -16:
        error_messages = _('Terminal user level is not valid : ( please contact our support team).')

    if payment_code == -17:
        error_messages = _('Terminal user level is not valid : ( please contact our support team).')

    if payment_code == -30:
        error_messages = _('Terminal do not allow to accept floating wages.')

    if payment_code == -31:
        error_messages = _('Terminal do not allow to accept wages, please add default bank account in panel.')

    if payment_code == -32:
        error_messages = _('Wages is not valid, Total wages(floating) has been overload max amount.')

    if payment_code == -33:
        error_messages = _('Wages floating is not valid.')

    if payment_code == -34:
        error_messages = _('Wages is not valid, Total wages(fixed) has been overload max amount.')

    if payment_code == -35:
        error_messages = _('Wages is not valid, Total wages(floating) has been reached the limit in max parts.')

    if payment_code == -40:
        error_messages = _('Invalid extra params, expire_in is not valid.')

    if payment_code == -50:
        error_messages = _('Session is not valid, amounts values is not the same.')

    if payment_code == -51:
        error_messages = _('Session is not valid, session is not active paid try.')

    if payment_code == -52:
        error_messages = _('Oops!!, please contact our support team')

    if payment_code == -53:
        error_messages = _('Session is not this merchant_id session')

    if payment_code == -54:
        error_messages = _('Invalid authority.')

    if payment_code == 101:
        error_messages = _('Verified')

    return error_messages
