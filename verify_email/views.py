from django.shortcuts import render, redirect, HttpResponse
from . email_handler import varify_user
from .app_configurations import GetFieldFromSettings
from django.contrib import messages

# Create your views here.

success_redirect = GetFieldFromSettings().get('verification_success_redirect')
failed_redirect = GetFieldFromSettings().get('verification_failed_redirect')

success_msg = GetFieldFromSettings().get('verification_success_msg')
failed_msg = GetFieldFromSettings().get('verification_failed_msg')

failed_template = GetFieldFromSettings().get('verification_failed_template')
success_template = GetFieldFromSettings().get('verification_success_template')


def verify_user_and_activate(request, useremail, usertoken):
    """
    verify the user's email and token and redirect'em accordingly.
    """
    
    if varify_user(useremail, usertoken):
        if success_redirect and not success_template:
            messages.SUCCESS(request, 'Successfully Verified!')
            return redirect(to=success_redirect)
        return render(
            request,
            template_name=success_template,
            context={
                'msg': success_msg,
                'status':'Verification Successfull!',
                'link': success_redirect
            }
        )
    else:
        return render(
            request,
            template_name=failed_template, 
            context={
                'msg': failed_msg,
                'status':'Verification Failed!',
            }
        )


