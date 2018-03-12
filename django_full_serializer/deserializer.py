"""
Serialize data to/from JSON
"""
import json
from collections import OrderedDict

from django.apps import apps
from django.core.serializers import base
from django.db import DEFAULT_DB_ALIAS, models
from django.utils.encoding import is_protected_type
from django.core.serializers.base import DeserializationError


def _read_objects(object_list, *, using=DEFAULT_DB_ALIAS, ignorenonexistent=False, **options):
    """
    Deserialize simple Python objects back into Django ORM instances.
    It's expected that you pass the Python objects themselves (instead of a
    stream or a string) to the constructor
    """
    field_names_cache = {}  # Model: <list of field_names>

    for d in object_list:
        # Look up the model and starting build a dict of data for it.
        try:
            Model = _get_model(d["model"])
        except base.DeserializationError:
            if ignorenonexistent:
                continue
            else:
                raise
        data = {}
        if 'pk' in d:
            try:
                data[Model._meta.pk.attname] = Model._meta.pk.to_python(d.get('pk'))
            except Exception as e:
                raise base.DeserializationError.WithData(e, d['model'], d.get('pk'), None)
        m2m_data = {}

        if Model not in field_names_cache:
            field_names_cache[Model] = {f.name for f in Model._meta.get_fields()}
        field_names = field_names_cache[Model]

        # Handle each field
        for (field_name, field_value) in d["fields"].items():

            if ignorenonexistent and field_name not in field_names:
                # skip fields no longer on model
                continue

            field = Model._meta.get_field(field_name)

            # Handle M2M relations
            if field.remote_field and isinstance(field.remote_field, models.ManyToManyRel):
                model = field.remote_field.model
                if hasattr(model._default_manager, 'get_by_natural_key'):
                    def m2m_convert(value):
                        if hasattr(value, '__iter__') and not isinstance(value, str):
                            return model._default_manager.db_manager(using).get_by_natural_key(*value).pk
                        else:
                            return model._meta.pk.to_python(value)
                else:
                    def m2m_convert(v):
                        return model._meta.pk.to_python(v)

                try:
                    m2m_data[field.name] = []
                    for pk in field_value:
                        m2m_data[field.name].append(m2m_convert(pk))
                except Exception as e:
                    raise base.DeserializationError.WithData(e, d['model'], d.get('pk'), pk)

            # Handle FK fields
            elif field.remote_field and isinstance(field.remote_field, models.ManyToOneRel):
                model = field.remote_field.model
                if field_value is not None:
                    try:
                        default_manager = model._default_manager
                        field_name = field.remote_field.field_name
                        if isinstance(field_value, dict):
                            data[field.name] = list(_read_objects([field_value], **options))[0].object
                        if hasattr(default_manager, 'get_by_natural_key'):
                            if hasattr(field_value, '__iter__') and not isinstance(field_value, str):
                                obj = default_manager.db_manager(using).get_by_natural_key(*field_value)
                                value = getattr(obj, field.remote_field.field_name)
                                # If this is a natural foreign key to an object that
                                # has a FK/O2O as the foreign key, use the FK value
                                if model._meta.pk.remote_field:
                                    value = value.pk
                            else:
                                value = model._meta.get_field(field_name).to_python(field_value)
                            data[field.attname] = value
                        else:
                            data[field.attname] = model._meta.get_field(field_name).to_python(field_value)
                    except Exception as e:
                        raise base.DeserializationError.WithData(e, d['model'], d.get('pk'), field_value)
                else:
                    data[field.attname] = None

            # Handle all other fields
            else:
                try:
                    data[field.name] = field.to_python(field_value)
                except Exception as e:
                    raise base.DeserializationError.WithData(e, d['model'], d.get('pk'), field_value)

        obj = base.build_instance(Model, data, using)
        yield base.DeserializedObject(obj, m2m_data)


def _get_model(model_identifier):
    """Look up a model from an "app_label.model_name" string."""
    try:
        return apps.get_model(model_identifier)
    except (LookupError, TypeError):
        raise base.DeserializationError("Invalid model identifier: '%s'" % model_identifier)


def Deserializer(stream_or_string, **options):
    """Deserialize a stream or string of JSON data."""
    if not isinstance(stream_or_string, (bytes, str)):
        stream_or_string = stream_or_string.read()
    if isinstance(stream_or_string, bytes):
        stream_or_string = stream_or_string.decode()
    try:
        objects = json.loads(stream_or_string)
        yield from _read_objects(objects, **options)
    except (GeneratorExit, DeserializationError):
        raise
    except Exception as exc:
        raise DeserializationError() from exc
