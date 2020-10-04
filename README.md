

<h1 style='text-align:center'>Email-Verification for Django</h1>
<p align='center'>
<img src='https://github.com/foo290/Django-Verify-Email/blob/main/readme_imgs/django.png' alt='An image was supposed to be here . . .' height="200">
</p>

Email verification for new signups or new user is a two step verification process and adds a layer for security for valid users.

<b> verify_email </b> is a django app that provides this functionality right of the bat without any complex implimentation or hassle of making user inactive untill they are verified.

## The app takes care of :
* Settings user's is_active status to False by default.
* Providing selected features to inactive users instead of not letting them sign in. (This feature is in testing and hasn't been added yet.)
* Generate hashed token for each user.
* Generate a verification link and sending it to user's email.
* Recieve a request from verification link and verify for its validity.
* Activating the user's account.

## What you have to impliment is :
* Three steps in Quick start below...

<b>Note : </b>The app is designed to be used right of the bat, but further customizations options are also provided in Advance section below.


## Installation

Clone the repo and run the following command where "dist" dir is :<br>
NOTE : Don't forget to activate virtual environment if you have one.

```
python -m pip install dist/Django-Verify-Email-1.0.tar.gz
```


## Quick start
The steps to getting started is very simple. Like any other app, this can be installed easyly by adding "verify_email" in your installed apps like:

<b>Note : </b>This documentation assumes that you already have a mail server configured for your project to send mails. 

if Not, then your first step should be Step 0:

### Step 0 :-
Bypass this step if you already have these things setup for your project.

In your settings.py :
```
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_ID') 
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PW')

DEFAULT_FROM_EMAIL = 'noreply<no_reply@dusk.com>'
```

## Main steps get going...

### Step 1 :-
Add "verify_email" to your INSTALLED_APPS setting like this:
```
    INSTALLED_APPS = [
        ...
        "verify_email",
    ]
```
### Step 2 :-
Include the "verify_email" URLconf in your project urls.py like this:
```

urlpatterns = [
	...
	path('verification/', include('verify_email.urls')),	

]
```


### Step 3 :-
For sending email from a signup form, in your views.py import:

```
...
from verify_email.email_handler import send_verification_link
```
Now in the function where you are validation the form:

```
...

def register_user(request):
    ...
    
    if form.is_valid():

        response = send_verification_link(request, form)
```

<b>Attention : </b>"send_verification_link()" takes two arguments, requests and form in order to set user's active status. 



#### At this point, you are good to go...
 Start the development server and signup with an email and you should be getting an email on the entered email with the default template for account activation. (You can provide your own html template. see)

 <b>Note : </b>The app comes with default email templates which can be overriden. See <a href='#'> Custom Email Templates</a>

## Verifying User's email :
<h3 style='text-align:center'>Nothing...</h3>
That's right ! , you don't have to impliment any other code for validating user with their respective unique tokens and emails. 
<br><br>
The app takes care of everything in background.

* When user click on the verification link, it comes to :
    ```
    path('verification/', include('verify_email')),
    ```
    which you defined in your project's urls.py in step 2 above.
* This pattern is further extended in this app's urls.py where it accepts encoded email and encoded hashed token from the verification link.
* It then checks for user by that email.
* If user exist, it then checks for token if it is valid for that user or not.
* If the token is valid, it activates the user's account by setting is_active attribute to True and last_login to timezone.now().
* If the token is alredy been redeemed or modified, you'll be redirected to a verification failed page.

#### This whole process from generating HMAC hashed token for each user to verifying it for a unique user, is abstracted within the app which reduce hassel by a lot.

# Advance

## Custom Email Templates : 
The app is packed with default html templates to handle the web pages but if you want to provide your own template you can do it by setting an attribute in settings.py :
```
HTML_MESSAGE_TEMPLATE = "path/to/html_template.html"

VERIFICATION_SUCCESS_TEMPLATE = "path/to/success.html"

VERIFICATION_FAILED_TEMPLATE = "path/to/failed.html"
```
```
SUBJECT = 'subject of email'

# default subject is : Email Verification Mail
```

## Successful Verification :
After verification is successful, you might wanna redirect the user to login page. You can do this in two ways :

* 1 Redirect from success webpage.
    ```
    LOGIN_URL = 'name of your login pattern'

    Note: This variable is also used by django.
    ```
* 2 Redirect directly to login page without stopping at success message page.
    ```
    VERIFICATION_SUCCESS_TEMPLATE = None
    ```




