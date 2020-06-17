from __future__ import absolute_import

from collections import OrderedDict
from traits.api import HasTraits, HasStrictTraits, Any, Callable, Type, \
    Str, Unicode


class ObjectFactory(HasStrictTraits):
    """ A factory with metadata.
    """
    
    # A unique ID identifying the factory.
    id = Str()
    
    # A short, user-visible name for the object. 
    name = Unicode()
    
    # A longer, user-visible description for the object.
    description = Unicode()
    
    # The type of the object.
    type = Type()
    
    # An Enaml UI for editing the object. The object will be passed to widget
    # via the 'obj' attribute.
    ui = Type('enaml.widgets.widget.Widget')
    
    # A factory for creating new instances of the object.
    # If not specified, objects are created by invoking the type constructor.
    factory = Callable()
    
    def create(self, *args, **kwds):
        """ Create an instance of the object.
        """
        if self.factory:
            return self.factory(*args, **kwds)
        elif self.type:
            return self.type(*args, **kwds)
        else:
            raise RuntimeError('Cannot construct object from factory')


class ObjectRegistry(HasTraits):
    """ A registry of object factories with a variety of lookup mechanisms.
    
    The object registry is a singleton.
    """

    # Private instance variables.
    _registry = Any # Dict(Str, ObjectFactory)
    
    # Private class variable for the singleton registry instance.
    _instance = None
    
    @staticmethod
    def instance():
        return ObjectRegistry._instance
        
    def __new__(cls, *args, **kw):
        if ObjectRegistry._instance:
            raise RuntimeError('Object registry already exists')
        self = super(ObjectRegistry, cls).__new__(cls, *args, **kw)
        ObjectRegistry._instance = self
        return self
    
    def __registry_default(self):
        return OrderedDict()
    
    # dict interface
    
    def __getitem__(self, id):
        return self._registry[id]

    def get(self, id, default=None):
        return self._registry.get(id, default)
    
    # ObjectRegistry interface
    
    def add(self, *args, **kwargs):
        """ Add object factories to the registry.
        """
        for factory in args:
            if not isinstance(factory, ObjectFactory):
                raise ValueError('The object %r is not a factory' % factory)
            
            if factory.id in self._registry and not kwargs.get('force', False):
                msg = 'A factory with ID %r already belong to the registry'
                raise RuntimeError(msg % factory.id)
            else:
                self._registry[factory.id] = factory
        
    def get_by_type(self, klass):
        """ Returns all object factories whose instances are subclasses of a
        given type.
        """
        return [ factory for factory in self._registry.itervalues()
                 if issubclass(factory.type, klass) ]
    
    def get_closest_by_type(self, klass):
        """ Get the object factory whose type is the best match for the given
        type, as determined by the MRO.
        
        Returns an object factory or None. 
        """
        for t in klass.mro():
            for factory in self._registry.itervalues():
                if t == factory.type:
                    return factory
        return None


# Singleton registry instance
object_registry = ObjectRegistry()