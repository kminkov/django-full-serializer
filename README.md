# django-full-serializer
Django Models (QuerySet) Serializer/Deserializer (JSON format) including related (foreign) models.

Works well with **Django 2.0** and **Python 3**.

The interface is based on Wad of Stuff (see https://wadofstuff.blogspot.com/2009/02/django-full-serializers-part-i.html).

Mainly the serializer inherits an original Django serializer and overrides some funtions to extend features.
For the deserializer, overrides wasn't possible and the code is copied from the origin: https://github.com/django/django/tree/master/django/core/serializers

# Installation

Install the package from pip:

```
pip install -e "git+https://github.com/tru-software/django-full-serializer#egg=django_full_serializer"
```

Make sure to add `jsonfull` to your `SERIALIZATION_MODULES` (`settings.py`):

```python
SERIALIZATION_MODULES = {
	'jsonfull': 'django_full_serializer'
}
```

# Basic Usage

## Models
```python
class Country(models.Model):
    name = models.CharField(max_length=100)

class Author(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    lines = models.IntegerField()
    pages = models.IntegerField()
    price = models.IntegerField()
```

## Serialization
```python
from django.core import serializers

print(serializers.serialize('jsonfull', Book.objects.all()))

print(serializers.serialize('jsonfull', Book.objects.all(), excludes=('pages',)))

print(serializers.serialize('jsonfull', Book.objects.all(), relations={'author': True}))

print(serializers.serialize('jsonfull', Book.objects.all(), relations={'author': {'country': True}}))

data = serializers.serialize('jsonfull', Book.objects.all())
objects = [i.object for i in serializers.deserialize('jsonfull', data)]
```
