"""
Serialize data to/from JSON
"""

from django.core.serializers.json import Serializer as DjangoJSONSerializer


class Serializer(DjangoJSONSerializer):
    """
    Convert a queryset to JSON.
    """
    DEFAULT_JSON_SEPARATORS = (',',  ':')

    def _init_options(self):
        super(Serializer, self)._init_options()
        # Prevent trailing spaces
        self.json_kwargs['separators'] = self.DEFAULT_JSON_SEPARATORS


    def start_serialization(self):
        self.objects = []
        super(Serializer, self).start_serialization()


    def start_object(self, obj):
        super(Serializer, self).start_object(obj)
        self.deferred_fields = obj.get_deferred_fields()


    def handle_field(self, obj, field):
        if field.name not in self.deferred_fields:
             super(Serializer, self).handle_field(obj, field)


    def handle_fk_field(self, obj, field):

        fname = field.name
        if fname in self.relations:
            related = getattr(obj, fname)
            if related is not None:

                # perform full serialization of FK
                serializer = Serializer()

                options = {
                     'use_natural_primary_keys': False,
                     'use_natural_foreign_keys': False,
                     'skip_json_dump': True
                }
                if isinstance(self.relations, dict):
                    if isinstance(self.relations[fname], dict):
                        options['relations'] = self.relations[fname]
                serializer.serialize([related], **options)
                self._current[fname] = serializer.objects[0]
                return
            else:
                return super(Serializer, self).handle_fk_field(obj, field)
        return super(Serializer, self).handle_fk_field(obj, field)


    def serialize(self, queryset, *args, **options):

        self.excludes = options.pop("excludes", [])
        self.relations = options.pop("relations", [])
        self.extras = options.pop("extras", [])
        self.skip_json_dump = options.pop("skip_json_dump", False)

        options['use_natural_primary_keys'] = False

        return super(Serializer, self).serialize(queryset, *args, **options)


    def end_object(self, obj):
        concrete_model = obj._meta.proxy_for_model or obj.__class__

        if self.use_natural_primary_keys:
            pk = concrete_model._meta.pk
            pk_parent = pk if pk.remote_field and pk.remote_field.parent_link else None
        else:
            pk_parent = None

        local_fields = concrete_model._meta.local_fields

        # Serialize fields of the base models
        for field in concrete_model._meta.fields:
            if field in local_fields:
                # Field is already serialized by standard impl (django.core.serializers.base.serialize)
                continue
            if field.primary_key is True:
                 self.handle_field(obj, field)
            if field.serialize or field is pk_parent:
                if field.remote_field is None:
                    if self.selected_fields is None or field.attname in self.selected_fields:
                        self.handle_field(obj, field)
                else:
                    if self.selected_fields is None or field.attname[:-3] in self.selected_fields:
                        self.handle_fk_field(obj, field)

        if self.skip_json_dump is True:
            self.objects.append(self.get_dump_object(obj))
        else:
            super(Serializer, self).end_object(obj)
