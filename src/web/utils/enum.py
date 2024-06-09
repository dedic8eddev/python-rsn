# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _


class EnumMetaclass(type):
    """Metaclass for enumerations.
    You must define the values using UPPERCASE names.

    Generates:
    cls.names - reverse dictionary mapping value to name
    cls.pairs - sorted list of (id, name) pairs suitable for model choices
    cls.values - list of values defined by the enumeration

    Example:
    class X(object):
        __metaclass__ = EnumMetaclass
        A = 1
        B = 2
        C = 3

    >>> X.names
    {1: 'A', 2: 'B', 3: 'C'}

    >>> X.values
    [1, 2, 3]

    >>> X.pairs
    [(1, 'A'), (2, 'B'), (3, 'C')]

    >>> X.trans_names
    {1: _('KlassEnum.A'), 2: _('KlassEnum.B'), 3: _('KlassEnum.C')}

    >>> X.trans_pairs
    >>> X.sorted_trans_pairs - OrderedDict sorted by translated name
    >>> X.ordered_trans_pairs - OrderedDict sorted by id
    [(1, _('KlassEnum.A')), (2. _('KlassEnum.B')), (3, _('KlassEnum.C'))]
    """

    def __new__(cls, name, bases, d):
        names = dict()
        pairs = []
        values = []
        trans_names = dict()
        trans_pairs = []
        for x in d:
            if x.isupper() and (
                isinstance(d[x], int) or isinstance(d[x], long)
            ):
                names[d[x]] = x
                pairs.append((d[x], x))
                trans_pairs.append((d[x], _(name + u"." + x)))
                values.append(d[x])
                trans_names[d[x]] = _(name + u"." + x)
        pairs.sort()
        trans_pairs.sort()
        d['names'] = names
        d['names_human'] = {}
        for key, name in names.items():
            d['names_human'][name.replace('_', ' ')] = key
        d['reverse_names'] = {v: k for k, v in names.items()}
        d['pairs'] = pairs
        d['values'] = values
        d['trans_names'] = trans_names
        d['trans_pairs'] = trans_pairs
        d['sorted_trans_pairs'] = sorted(trans_pairs, key=lambda x: x[1])
        d['ordered_trans_pairs'] = sorted(trans_pairs, key=lambda x: x[0])
        return type.__new__(cls, name, bases, d)
