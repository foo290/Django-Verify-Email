from .app_configurations import GetFieldFromSettings
from .confirm import _verify_user
from django.contrib import messages
from django.urls import reverse
from django.shortcuts import render, redirect

from .token_manager import error_type
from .email_handler import resend_verification_email

success_redirect = GetFieldFromSettings().get('verification_success_redirect')

success_msg = GetFieldFromSettings().get('verification_success_msg')
failed_msg = GetFieldFromSettings().get('verification_failed_msg')

failed_template = GetFieldFromSettings().get('verification_failed_template')
success_template = GetFieldFromSettings().get('verification_success_template')
link_expired_template = GetFieldFromSettings().get('link_expired_template')


def verify_user_and_activate(request, useremail, usertoken):
    """
    A view function already implemented for you so you don't have to implement any function for verification
    as this function will be automatically be called when user clicks on verification link.

    verify the user's email and token and redirect'em accordingly.
    """

    verified = _verify_user(useremail, usertoken)
    if verified is True:
        if success_redirect and not success_template:
            messages.success(request, success_msg)
            return redirect(to=success_redirect)
        return render(
            request,
            template_name=success_template,
            context={
                'msg': success_msg,
                'status': 'Verification Successful!',
                'link': reverse(success_redirect)
            }
        )
    elif verified == error_type.expired:
        return render(
            request,
            template_name=link_expired_template,
            context={
                'msg': 'The link has lived its life :( Request a new one!',
                'status': 'Expired!',
                'encoded_email': useremail,
                'encoded_token': usertoken
            }
        )
    elif verified == error_type.tempered:
        return render(
            request,
            template_name=failed_template,
            context={
                'msg': 'This link was modified before verification.',
                'minor_msg': 'Cannot request another verification link with faulty link.',
                'status': 'Faulty Link Detected!',
            }
        )
    elif verified == error_type.mre:
        return render(
            request,
            template_name=failed_template,
            context={
                'msg': 'You have exceeded the maximum verification requests! Contact admin.',
                'status': 'Maxed out!',
            }
        )
    else:
        return render(
            request,
            template_name=failed_template,
            context={
                'msg': failed_msg,
                'minor_msg': 'There is something wrong with this link...',
                'status': 'Verification Failed!',
            }
        )


def request_new_link(request, useremail, usertoken):
    status = resend_verification_email(request, useremail, usertoken)
    if status:
        return render(
            request,
            template_name='verify_email/display_message.html',
            context={
                'msg': "You have requested another verification email!",
                'minor_msg': 'Your verification link has been sent',
                'status': 'Email Sent!',
            }
        )
    elif status == error_type.mre:
        return render(
            request,
            template_name=failed_template,
            context={
                'msg': 'You have exceeded the maximum verification requests! Contact admin.',
                'status': 'Maxed out!',
            }
        )
    else:
        return render(
            request,
            template_name=failed_template,
            context={
                'msg': failed_msg,
                'minor_msg': 'Cannot send verification link to you! contact admin.',
                'status': 'Verification Failed!',
            }
        )
