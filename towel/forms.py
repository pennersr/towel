import pickle

from django import forms as django_forms
from django.db import models as django_models
from django.forms import * # Pose as the forms module
from django.utils.translation import ugettext_lazy as _


class BatchForm(Form):
    ids = []
    process = False

    def __init__(self, request, *args, **kwargs):
        kwargs.setdefault('prefix', 'batch')

        self.request = request

        if request.method == 'POST' and 'batchform' in request.POST:
            self.process = True
            super(BatchForm, self).__init__(request.POST, *args, **kwargs)
        else:
            super(BatchForm, self).__init__(*args, **kwargs)

    def context(self, queryset):
        ctx = {
            'batch_form': self,
            }

        if self.process and self.is_valid():
            ctx.update(self._context(
                self.selected_items(self.request.POST, queryset)))

        return ctx

    def _context(self, batch_queryset):
        raise NotImplementedError

    def selected_items(self, post_data, queryset):
        self.ids = queryset.values_list('id', flat=True)
        self.ids = [pk for pk in self.ids if post_data.get('entry%s' % pk)]
        return queryset.filter(id__in=self.ids)


class SearchForm(Form):
    always_exclude = ('s', 'query')

    # search form active?
    s = CharField(required=False)
    query = CharField(required=False, label=_('Query'))

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request')
        super(SearchForm, self).__init__(*args, **kwargs)
        self.persist(request)

    def persist(self, request):
        session_key = 'sf_%s' % self.__class__.__name__.lower()

        if 'clear' in request.GET or 'n' in request.GET:
            if session_key in request.session:
                del request.session[session_key]

        if request.method == 'GET' and 's' not in request.GET:
            # try to get saved search from session
            if session_key in request.session:
                self.data = pickle.loads(request.session[session_key])
                self.persistency = True
        else:
            request.session[session_key] = pickle.dumps(self.data)

    def searching(self):
        if self.cleaned_data['s'] or hasattr(self, 'persistency'):
            return 'searching'
        return ''

    @property
    def safe_cleaned_data(self):
        self.is_valid()
        try:
            return self.cleaned_data.copy()
        except AttributeError:
            return {}

    def fields_iterator(self):
        skip = ('query', 's')

        for field in self:
            if field.name not in skip:
                yield field

    def apply_filters(self, queryset, data, exclude=()):
        exclude = list(exclude) + list(self.always_exclude)

        for field in self.fields.keys():
            if field in exclude:
                continue

            value = data.get(field)
            if value is not None:
                if hasattr(value, '__iter__'):
                    queryset = queryset.filter(**{'%s__in' % field: value})
                else:
                    queryset = queryset.filter(**{field: value})

        return queryset


class StrippedTextInput(TextInput):
    def value_from_datadict(self, data, files, name):
        value = data.get(name, None)
        if isinstance(value, (str, unicode)):
            return value.strip()
        return value

    def render(self, *args, **kwargs):
        return super(StrippedTextInput, self).render(*args, **kwargs)


class StrippedTextarea(Textarea):
    def value_from_datadict(self, data, files, name):
        value = data.get(name, None)
        if isinstance(value, (str, unicode)):
            return value.strip()
        return value

    def render(self, *args, **kwargs):
        return super(StrippedTextarea, self).render(*args, **kwargs)


def stripped_formfield_callback(field, **kwargs):
    if isinstance(field, django_models.CharField) and not field.choices:
        kwargs['widget'] = StrippedTextInput()
    elif isinstance(field, django_models.TextField):
        kwargs['widget'] = StrippedTextarea()
    return field.formfield(**kwargs)