import logging

from django.http import Http404, HttpResponse
from django.urls import reverse
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.signing import SignatureExpired, BadSignature
from django.views.decorators.http import require_GET, require_POST


from .app_configurations import GetFieldFromSettings
from .confirm import UserActivationProcess
from .email_handler import ActivationMailManager
from .forms import RequestNewVerificationEmail
from .errors import (
    InvalidToken,
    MaxRetriesExceeded,
    UserAlreadyActive,
    UserNotFound,
)

logger = logging.getLogger(__name__)

pkg_configs = GetFieldFromSettings()

login_page = pkg_configs.get("login_page")

success_msg = pkg_configs.get("verification_success_msg")
failed_msg = pkg_configs.get("verification_failed_msg")
debug = pkg_configs.get("debug")

failed_template = pkg_configs.get("verification_failed_template")
success_template = pkg_configs.get("verification_success_template")
link_expired_template = pkg_configs.get("link_expired_template")
request_new_email_template = pkg_configs.get("request_new_email_template")
new_email_sent_template = pkg_configs.get("new_email_sent_template")


@require_GET
def verify_and_activate_user(request, user_email, user_token):
    """
    A view function already implemented for you so you don't have to implement any function for verification
    as this function will be automatically be called when user clicks on verification link.

    verify the user's email and token and redirect'em accordingly.
    """
    try:
        verified_activated_user = UserActivationProcess.activate_user(
            user_email, user_token
        )
        if login_page and not success_template:
            messages.success(request, success_msg)
            return redirect(to=login_page)

        return render(
            request,
            template_name=success_template,
            context={
                "msg": success_msg,
                "status": f"Verification Successful!",
                "link": reverse(login_page),
            },
        )

    except (ValueError, TypeError) as error:
        logger.error(
            f"[ERROR]: Something went wrong while verifying user, exception: {error}"
        )
        return render(
            request,
            status=401,
            template_name=failed_template,
            context={
                "msg": failed_msg,
                "minor_msg": "There is something wrong with this link...",
                "status": "Verification Failed!",
            },
        )
    except SignatureExpired:
        return render(
            request,
            status=401,
            template_name=link_expired_template,
            context={
                "msg": "The link has lived its life :( Request a new one!",
                "status": "Expired!",
                "encoded_email": user_email,
                "encoded_token": user_token,
            },
        )
    except BadSignature:
        return render(
            request,
            status=401,
            template_name=failed_template,
            context={
                "msg": "This link was modified before verification.",
                "minor_msg": "Cannot request another verification link with faulty link.",
                "status": "Faulty Link Detected!",
            },
        )
    except MaxRetriesExceeded:
        return render(
            request,
            status=401,
            template_name=failed_template,
            context={
                "msg": "You have exceeded the maximum verification requests! Contact admin.",
                "status": "Maxed out!",
            },
        )
    except InvalidToken:
        return render(
            request,
            status=401,
            template_name=failed_template,
            context={
                "msg": "This link is invalid or been used already, we cannot verify using this link.",
                "status": "Invalid Link",
            },
        )
    except UserNotFound:
        raise Http404("404 User not found")

    except Exception as err:
        logger.exception(err)
        flash_msg = "Something went wrong during this process!"
        if debug:
            flash_msg = f"""{flash_msg} Developer should look into this.
            Error Details: {err}
            (You are seeing error details because app is running in debug mode)
            """
        return render(
            request,
            status=403,
            template_name=failed_template,
            context={
                "msg": flash_msg,
                "status": "Failed!",
            },
        )



def request_new_link(request, user_email=None, user_token=None):
    try:
        if user_email is None or user_token is None:
            # request came from re-request email page
            if request.method == "POST":
                form = RequestNewVerificationEmail(request.POST)  # do not inflate data
                if form.is_valid():
                    form_data: dict = form.cleaned_data
                    email = form_data["email"]

                    inactive_user = get_user_model().objects.get(email=email)
                    if inactive_user.is_active:
                        raise UserAlreadyActive("User is already active")
                    else:
                        # resend email
                        ActivationMailManager.resend_verification_link(
                            request, email, user=inactive_user, encoded=False
                        )
                        return render(
                            request,
                            template_name=new_email_sent_template,
                            context={
                                "msg": "You have requested another verification email!",
                                "minor_msg": "Your verification link has been sent",
                                "status": "Email Sent!",
                            },
                        )
            else:
                form = RequestNewVerificationEmail()
            return render(
                request,
                template_name=request_new_email_template,
                context={"form": form},
            )
        else:
            # request came from  previously sent link
            status = ActivationMailManager.resend_verification_link(
                request, user_email, token=user_token
            )
            if status:
                return render(
                    request,
                    template_name=new_email_sent_template,
                    context={
                        "msg": "You have requested another verification email!",
                        "minor_msg": "Your verification link has been sent",
                        "status": "Email Sent!",
                    },
                )
            else:
                messages.info(request, "Something went wrong during sending email :(")
                logger.error("something went wrong during sending email")

    except ObjectDoesNotExist as error:
        messages.warning(request, "User not found associated with given email!")
        logger.error(f"[ERROR]: User not found. exception: {error}")
        return HttpResponse(b"User Not Found", status=404)

    except MultipleObjectsReturned as error:
        logger.error(f"[ERROR]: Multiple users found. exception: {error}")
        return HttpResponse(b"Internal server error!", status=500)

    except KeyError as error:
        logger.error(f"[ERROR]: Key error for email in your form: {error}")
        return HttpResponse(b"Internal server error!", status=500)

    except MaxRetriesExceeded as error:
        logger.error(
            f"[ERROR]: Maximum retries for link has been reached. exception: {error}"
        )
        return render(
            request,
            status=403,
            template_name=failed_template,
            context={
                "msg": "You have exceeded the maximum verification requests! Contact admin.",
                "status": "Maxed out!",
            },
        )
    except InvalidToken:
        return render(
            request,
            template_name=failed_template,
            context={
                "msg": "This link is invalid or been used already, we cannot verify using this link.",
                "status": "Invalid Link",
            },
        )
    except UserAlreadyActive:
        return render(
            request,
            status=403,
            template_name=failed_template,
            context={
                "msg": "This user's account is already active",
                "status": "Already Verified!",
            },
        )
    except Exception as err:
        logger.exception(err)
        flash_msg = "Something went wrong during this process!"
        if debug:
            flash_msg = f"""{flash_msg} Developer should look into this.
            Error Details: {err}
            (You are seeing error details because app is running in debug mode)
            """
        return render(
            request,
            status=403,
            template_name=failed_template,
            context={
                "msg": flash_msg,
                "status": "Failed!",
            },
        )
