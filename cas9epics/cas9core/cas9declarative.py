"""
"""
from __future__ import division, print_function, unicode_literals

import declarative
from declarative import bunch


class ShadowBunchN(bunch.ShadowBunch):
    _names = {
        'current'  :  0,
        'names'    :  1,
        'epics'    :  2,
        'config'   :  3,
    }

class ShadowBunchNPull(ShadowBunchN):
    """
    ShadownBunch for ctree that also stores every access to determine what was stored. For diffs and config pruning
    """
    _pull_full = True


dproperty = declarative.dproperty
mproperty = declarative.mproperty
__NOARG = declarative.utilities.unique_generator()
NOARG = declarative.NOARG


def dproperty_ctree(func = None, default = __NOARG, name = None):
    """
    automatically grabs the value from the ctree to pass along. The function being wrapped should do the string conversion and validation.
    The doctstring is inserted into the ctree about field. A default may be passed as well. If the default is a function, then it is assumed to
    take "self" as an argument. This allows defaults computed from other attributes. Typically these will be small lambda functions but they don't
    need to be.

    decorator conventions:

    @dproperty_ctree
    def attrib(self, val):
        ...

    @dproperty_ctree(default = 1234)
    def attrib(self, val):
        ...

    @dproperty_ctree(default = lambda self : self.attrib2 + 1)
    def attrib(self, val):
        ...

    """
    def deferred(func):
        if name is None:
            usename = func.__name__
        else:
            usename = name
        if default is __NOARG:
            def superfunc(self, val):
                val = self.ctree.setdefault(
                    usename, val,
                    about = func.__doc__,
                )
                return func(self, val)
        elif not callable(default):
            def superfunc(self, val = default):
                val = self.ctree.setdefault(
                    usename, val,
                    about = func.__doc__,
                )
                return func(self, val)
        else:
            def superfunc(self, val = __NOARG):
                if val is __NOARG:
                    val = default(self)
                val = self.ctree.setdefault(
                    usename, val,
                    about = func.__doc__,
                )
                return func(self, val)
        superfunc.__name__ = func.__name__
        superfunc.__doc__  = func.__doc__
        return declarative.dproperty(superfunc)
    if func is None:
        return deferred
    else:
        return deferred(func)

