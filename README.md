

<h1 style='text-align:center'>DJANGO-REST-API</h1>

<img src='' alt='An image was supposed to be here . . .' height="200" style='display:block; margin-left:auto; margin-right:auto;'>

Django-REST-API is an app which lets you make get request to the database using Django's inbuilt ORMs and returns data in JSON

## Installation
clone the repo and run the following command where "dist" dir is :<br>
NOTE : Don't forget to activate virtual environment if you have one.

```
python -m pip install dist/Django-REST-API-1.0.tar.gz
```


## Quick start
The steps to getting started is very simple. Like any other app, this can be installed easyly by adding "api_response" in your installed apps like:

### Step 1 :-
Add "api_response" to your INSTALLED_APPS setting like this:
```
    INSTALLED_APPS = [
        ...
        "api_response",
    ]
```
### Step 2 :-
Include the "api_response" URLconf in your project urls.py like this:
```
import api_response

urlpatterns = [
	...
	path('api.response/', include('api_response.urls')),	

]
```

```
Note : change the url pattern ('api.response/') to anything you like...
```

### Step 4 :-
Specify the apps on which you want to enable the api in <b>settings.py</b> as :

```
API_ENABLED_APPS = {
    'App name': 'Model name'
}

A dict that contains your 'App name' as key and 'Model name' as its values.
```
### Important : If you have more than one model in you app, you can simply pass them in a list or tuple as :

```
API_ENABLED_APPS = {
    'App name': ['Model 1 name', 'model 2 name', ... ]
}

A dict that contains your 'App name' as key and list of 'Model name' as its values.
```
Note 'Model name' is the class name you make in your App.models file by inheriting models.Model and App name is simply the name of your app.

#### At this point, your api is ready to use
 Start the development server and visit http://127.0.0.1:8000/api.yourDomain/

 you will see a welcome message at api endpoint as :
```
{
    "WELCOME": "This is the api endpoint.",
    "suggested": "Start making request on API_URLS that you've specified",
}
```
### Note : Your URLs are namespaced by your 'App Name' so if you have an app named 'products', the url will be:
```
http://127.0.0.1:8000/api.response/products/
```
These API urls can be customized and you can specify your own (multiple) url pattern for your app as described in Advance section below.

Note : At the App's endpoints like ```http://127.0.0.1:8000/api.response/products/``` , only 10 results are shown by default to prevent server from overloading by unwanted computation. This behaviour can be overridden by specifying a variable named ```ENDPOINT_RESPONSE_LENGTH``` in <b>settings.py</b> . Set this variable to desired number of results you want or set it to "all" to get the full results by default.

# Advance

## Customize your api URL patterns
By default the urls are namespaced by "app_name/model_name/" but you can specify your own url pattern and get more control over passing arguments in URLs by configuring <b>settings.py</b> as :

```
API_URLS = {
    'Model name 1': [
		'pattern 1',
		'pattern 2',
		...
	],
	'Model name 2': [
		'pattern 1',
		...
	]
}

A dict containing 'Model name' as key and 'url patterns' (may be multiple) as values.
For Ex. :-

API_URLS = {
    'product': [
        'products/<int:id>/',
		'products/<str:name>/'
		...
    ]
}
```

### ATTENTION : The arguments names passed in url pattern must be same as fields specified in model.
for ex :- <br>
models.py :
```
from django.db import models

class Product(models.Model):
    name = models.CharField(max_length = 100)
    price = models.FloatField()
	
	...
```
In the example above, if I want to make a url pattern which gets the products for a specific price or name, the pattern's argument names will be 'name' and 'price'. Ex :
```
API_URLS = {
    'product': [
        'products/<str:name>/',	--> 'name' as argument
		'products/<int:price>/'	--> 'price' as argument
		...
    ]
}
```
<b>Note:</b> If you specify URL for an app in API_URLS, you are fully responsible for the pattern specified.

On every start of dev server, the url patterns will be printed on console to confirm it is made as specified like :

```
python manage.py runserver


Performing system checks...

API_URL_patterns --> [<URLPattern 'products/'>, <URLPattern 'blog/'>, <URLPattern 'users/<slug:userid>/'>, <URLPattern ''>, <URLPattern 'users/'>]

Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

## Block default api URL:
As urls for api are made by default as soon as the apps is added in API_ENABLED_APPS, you can block urls for apps by typing "block" inplace of pattern and default urls will be removed for that model.

### This does not block your url to access the page.

For ex:
```
API_URLS = {
    'product': [
        'block'
    ]
}
```
You can see if the URL is blocked or not when you run dev server as :

```
python manage.py runserver

...
Performing system checks...

API URL blocked for  --> "product", by URL_PATTERN_BLOCKER : "block"

Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

## Getting User data :
User model may have relations with other models in apps in your projects (like users have profile or posts of blogs) either by ForeignKey or One-to-One fields. To get these included in user api response, simple specify USER_RELATED_MODELS with model names you want to include in <b>settings.py</b> as

```
USER_RELATED_MODELS = [
    'profile',
	'post', 
]

A list containing model names which have some relations with User by ForeignKey or One-to-one relation.
```

## Accessing user's api URL
You can get user details either by user id or username as they are unique identifiers by visiting.

```
http://127.0.0.1:8000/api.response/users/id/
			OR
http://127.0.0.1:8000/api.response/users/username/
```
# Output

```
$ curl http://127.0.0.1:8000/api.domain/users/1/
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100  1329  100  1329    0     0  41531      0 --:--:-- --:--:-- --:--:-- 42870{
    "status": 200,
    "id": "1",
    "details": {
        "last_login": "2020-09-19T08:09:18.895Z",
        "username": "ns290",
        "first_name": "Nitin",
        "last_name": "Sharma",
        "email": "ns@gmail.com",
        "is_active": true,
        "date_joined": "2020-09-13T05:57:07Z",
        "groups": [],
        "user_permissions": [],
	}
}
```

## Output after adding profile and post models to USER_RELATED_MODEL

```
$ curl http://127.0.0.1:8000/api.domain/users/1/
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100  1329  100  1329    0     0  41531      0 --:--:-- --:--:-- --:--:-- 42870{
    "status": "Success",
    "id": "1",
    "details": {
        "last_login": "2020-09-19T08:09:18.895Z",
        "username": "ns290",
        "first_name": "",
        "last_name": "",
        "email": "ns@gmail.com",
        "is_active": true,
        "is_staff": true,
        "date_joined": "2020-09-13T05:57:07Z",
        "groups": [],
        "user_permissions": [],
        "profile": {
            "user": 1,
            "img": "default_pfp.jpg",
            "bio": 'Keep it logically awesome! 😃',
            "city": null,
            "country": 'India',
            "company": null,
            "github": 'https://github.com/foo290',
            "twitter": 'https://twitter.com/_foo290',
            "instagram": "https://instagram.com/_iamnitinsharma",
            "website": 'https://foo290.github.io.com'
        },
        "post": [
            {
                "id": 1,
                "title": "post 1",
                "author": 1
            },
            {
                "id": 2,
                "title": "post 2",
                "author": 1
            },
            {
                "id": 3,
                "title": "post 3",
                "author": 1
            }
        ]
    }
}

```

#### To uninstall, run the following command:
```
python -m pip uninstall Django-REST-API
```




