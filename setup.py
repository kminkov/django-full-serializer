#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup


setup(
    name="django-full-serializer",
    classifiers=[
        'Topic :: Utilities',
        'Development Status :: 4 - Beta',
        "Framework :: Django",
        'Environment :: Web Environment',
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Operating System :: POSIX",
        "Programming Language :: Python",
    ],
    description="Django Models (QuerySet) Serializer/Deserializer (JSON format) including related (foreign) models",
    license="MIT",
    long_description='',
    url="https://github.com/tru-software/django-full-serializer",
    project_urls={
        "Documentation": "https://github.com/tru-software/django-full-serializer",
        "Source Code": "https://github.com/tru-software/django-full-serializer",
    },

    author="TRU SOFTWARE",
    author_email="at@tru.pl",

    setup_requires=["setuptools_scm"],
    use_scm_version=True,

    install_requires=["django"],
    packages=["django_full_serializer"]
)
