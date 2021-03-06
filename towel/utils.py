import re

from django import template
from django.db.models.deletion import Collector


def related_classes(instance):
    """
    Return all classes which would be deleted if the passed instance
    were deleted too by employing the cascade machinery of Django
    itself. Does **not** return instances, only classes.
    """
    collector = Collector(using=instance._state.db)
    collector.collect([instance])

    # Save collected objects for later referencing (well yes, it does return
    # instances but we don't have to tell anybody :-)
    instance._collected_objects = collector.data

    return collector.data.keys()


def safe_queryset_and(qs1, qs2):
    """
    Safe AND-ing of two querysets. If one of both queries has its
    DISTINCT flag set, sets distinct on both querysets. Also takes extra
    care to preserve the result of the following queryset methods:

    * ``reverse()``
    * ``transform()``
    * ``select_related()``
    """

    if qs1.query.distinct or qs2.query.distinct:
        res = qs1.distinct() & qs2.distinct()
    else:
        res = qs1 & qs2

    res._transform_fns = list(set(
        getattr(qs1, '_transform_fns', [])
        + getattr(qs2, '_transform_fns', [])))

    if not (qs1.query.standard_ordering and qs2.query.standard_ordering):
        res.query.standard_ordering = False

    select_related = [qs1.query.select_related, qs2.query.select_related]
    if False in select_related:
        select_related.remove(False) # We are not interested in the default value

    if len(select_related) == 1:
        res.query.select_related = select_related[0]
    elif len(select_related) == 2:
        if True in select_related:
            select_related.remove(True) # prefer explicit select_related to generic select_related()

        if len(select_related) > 0:
            # If we have two explicit select_related calls, take any of them
            res.query.select_related = select_related[0]
        else:
            res = res.select_related()

    return res


kwarg_re = re.compile("(?:(\w+)=)?(.+)")

def parse_args_and_kwargs(parser, bits):
    """
    Parses template tag arguments and keyword arguments

    Returns a tuple ``args, kwargs``.

    Usage::

        @register.tag
        def custom(parser, token):
            return CustomNode(*parse_args_and_kwargs(parser, token.split_contents()[1:]))

        class CustomNode(template.Node):
            def __init__(self, args, kwargs):
                self.args = args
                self.kwargs = kwargs

            def render(self, context):
                args, kwargs = resolve_args_and_kwargs(context, self.args, self.kwargs)
                return self._render(context, *args, **kwargs):

            def _render(self, context, ...):
                # The real workhorse
    """
    args = []
    kwargs = {}

    for bit in bits:
        match = kwarg_re.match(bit)
        key, value = match.groups()
        value = parser.compile_filter(value)
        if key:
            kwargs[key] = value
        else:
            args.append(value)

    return args, kwargs


def resolve_args_and_kwargs(context, args, kwargs):
    """
    Resolves arguments and keyword arguments parsed by ``parse_args_and_kwargs`` using
    the passed context instance

    See ``parse_args_and_kwargs`` for usage instructions.
    """
    return [v.resolve(context) for v in args], dict((k, v.resolve(context))
        for k, v in kwargs.items())
