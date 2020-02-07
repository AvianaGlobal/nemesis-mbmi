from __future__ import absolute_import

from atom.api import Atom, Float


class PlotLimits(Atom):
    """ An object that keeps track of a high and low value for the limits
    of a plot axis.
    """
    low = Float(0.0)

    high = Float(1.0)

    def as_tuple(self):
        """ Return the object as a (low, high) tuple.
        """
        return self.low, self.high

    @classmethod
    def from_tuple(cls, tup):
        """ Create a PlotLimits object from a (low, high) tuple.
        """
        self = cls()
        self.low, self.high = tup
        return self
