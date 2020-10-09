import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="Django-Verify-Email",
    version="0.0.1",
    author="Nitin",
    author_email="ns290670@gamil.com",
    description="A Django app for email verification.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/foo290/Django-Verify-Email/",
    packages=setuptools.find_packages(),
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Django CMS :: 3.8",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
