from __future__ import absolute_import

import jsonpickle
from traits.api import HasTraits, Event, on_trait_change


###############################################################################
# Serialization functions
###############################################################################

def json_to_obj(json):
    """ Re-constructs an object from its JSON-encodable form.
    """
    unpickler = jsonpickle.unpickler.Unpickler()
    return unpickler.restore(json)

def obj_to_json(obj):
    """ Converts an object to a JSON-encodable format.
    """
    pickler = jsonpickle.pickler.Pickler()
    return pickler.flatten(obj)

# Monkey-patch JSON pickle. The existing implementations of these methods check
# whether the obj is strictly of the specified type, e.g. whether ``type(obj) is
# dict``. Naturally, this breaks TraitDict, TraitList, etc.
from traits.api import TraitDictObject, TraitListObject, TraitSetObject

jsonpickle.util.is_dictionary = lambda obj: type(obj) in (dict, TraitDictObject)
jsonpickle.util.is_list = lambda obj: type(obj) in (list, TraitListObject)
jsonpickle.util.is_set = lambda obj: type(obj) in (set, TraitSetObject)


###############################################################################
# Dirty state tracking
###############################################################################

class DirtyMixin(HasTraits):
    """ A mixin class for automatically setting "dirty" events.
    
    Traits which have 'transient = True' metadata are ignored. Cf. the
    pickling protocol in `HasTraits.__getstate__`.
    
    TODO: Recursive 'dirtied' propagation.
    Note that the obvious approach of using `on_trait_change('+.dirtied?')`
    does not work due to primitive (non-HasTraits) types.
    """
    
    # Event fired when the object is dirtied by a change.
    dirtied = Event()
    
    @on_trait_change('anytrait')
    def _transient_trait_change(self, obj, name, old, new):
        if not obj.trait(name).transient:
            self.dirtied = True
