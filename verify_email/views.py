from .app_configurations import GetFieldFromSettings
from .confirm import _verify_user
from django.contrib import messages
from django.urls import reverse
from django.shortcuts import render, redirect


success_redirect = GetFieldFromSettings().get('verification_success_redirect')

success_msg = GetFieldFromSettings().get('verification_success_msg')
failed_msg = GetFieldFromSettings().get('verification_failed_msg')

failed_template = GetFieldFromSettings().get('verification_failed_template')
success_template = GetFieldFromSettings().get('verification_success_template')


def verify_user_and_activate(request, useremail, usertoken):
    """
    A view function already implemented for you so you don't have to implement any function for verification
    as this function will be automatically be called when user clicks on verification link.

    verify the user's email and token and redirect'em accordingly.
    """

    if _verify_user(useremail, usertoken):
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
    else:
        return render(
            request,
            template_name=failed_template,
            context={
                'msg': failed_msg,
                'status': 'Verification Failed!',
            }
        )


