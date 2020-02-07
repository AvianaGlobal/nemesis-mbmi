from __future__ import absolute_import

import json
from textwrap import dedent

from traits.api import Bool, Instance, List, Range, Str, Unicode, \
    on_trait_change

from .r import ast, ast_macros
from .r.traits import RNameTrait
from .serialize import DirtyMixin, json_to_obj, obj_to_json


class Model(DirtyMixin):
    """ The specification for an outlier detection model.
    """
    
    # The data attributes containing the entity and group IDs.
    entity_name = RNameTrait()
    group_name = RNameTrait()
    
    # The controls and metrics associated with the model.
    controls = List(Instance('Control'))
    metrics = List(Instance('Metric'))
    
    # The algorithms that combine the metric scores into a composite score.
    composite_scores = List(Instance('CompositeScore'))
    
    # Custom, user-defined code associated with the model.
    user_code = Unicode()
    
    # Whether to cap entity-level z scores.
    cap_entity_score = Bool(True)
    max_entity_score = Range(low=0.0, value=3.0)
    
    # Whether to discard small groups.
    limit_group_size = Bool(False)
    min_group_size = Range(low=1, value=50)

    # Whether to store the input data as an additional table in the output DB.
    # FIXME: This doesn't really belong here because it's a property of the
    # model run process, not the model itself. If we ever develop the notion
    # of a "project", it should be moved there.
    store_input = Bool(True)
    
    def ast(self):
        """ Generate an AST that defines the model.
        """
        nodes = []
        
        if self.user_code:
            nodes += [
                ast.Comment('User-defined code'),
                ast.Raw(self.user_code),
            ]
        
        nodes += [
            ast.Comment('Configure model'),
            ast.Call(ast.Name('def_parameters'), self._ast_parameters(),
                     print_hint='long'),
        ]

        if self.controls:
            nodes += [ ast.Comment('Control variables') ]
            nodes += [ control.ast() for control in self.controls ]

        if self.metrics:
            nodes += [ ast.Comment('Metrics') ]
            nodes += [ metric.ast() for metric in self.metrics ]
        
        if self.composite_scores:
            nodes += [ ast.Comment('Composite scores') ]
            nodes += [ score.ast() for score in self.composite_scores ]

        return ast.Block(nodes, print_hint='long', libraries=['EliteOutliers'])
    
    def _ast_parameters(self):
        params = [
            (ast.Name('entity_name'), ast.Constant(self.entity_name)),
            (ast.Name('group_name'), ast.Constant(self.group_name)),
        ]
        if self.cap_entity_score:
            params += [ (ast.Name('cap_entity_score'),
                         ast.Constant(self.max_entity_score)) ]
        if self.limit_group_size:
            params += [ (ast.Name('min_group_size'), 
                         ast.Constant(self.min_group_size)) ]
        return params
        
    @classmethod
    def load(cls, f):
        """ Load a model from a file-like object.
        """
        content = json.load(f)
        version = content.get('version', 0)
        
        if version == 0:
            model = json_to_obj(content)
        elif version == 1:
            model = json_to_obj(content['model'])
        elif version > 1:
            message = dedent('''\
                The model you are trying to load was created by a newer
                version of this software.
                
                Please upgrade your installation.
            ''')
            raise IOError(message)
            
        assert isinstance(model, cls)
        return model
    
    def save(self, f):
        """ Save the model to a file-like object.
        """
        # When the model format changes in a backwards-compatibility breaking
        # way, the version number below should be incremented.
        content = dict(
            model = obj_to_json(self),
            version = 1,
        )
        json.dump(content, f, indent=2)
    
    def validate(self):
        """ Validate the model.
        
        This method performs consistency checks on the model definition.
        It cannot detect programming errors, but it can detect common mistakes
        like forgetting to define the entity/group names or duplicating a 
        metric/control.
        
        Returns None if successful; raises a ModelError otherwise.
        """
        # Check that entity and group name are defined.
        if not self.entity_name:
            raise ModelError('Entity column is not defined')
        elif not self.group_name:
            raise ModelError('Group column is not defined')
        
        # Verify uniqueness of names.
        model_objects = self.controls + self.metrics + self.composite_scores
        model_object_names = set(obj.name for obj in model_objects)
        if len(model_objects) != len(model_object_names):
            msg = 'Duplicate name among metrics, controls, and scores'
            raise ModelError(msg)
        
        # Perform validation on sub-objects.
        for obj in model_objects:
            obj.validate()
    
    @on_trait_change('controls.dirtied, metrics.dirtied, composite_scores.dirtied')
    def _set_dirtied(self):
        self.dirtied = True


class ModelObject(DirtyMixin):
    """ The base class for objects in an outlier model.
    """
    
    # The name of the object, which must be a valid R identifier.
    name = RNameTrait()
    
    # A human-readable description of the object. Set by the user.
    description = Unicode()
    
    def validate(self):
        """ Validate the model object.
        """
        pass


class ModelError(Exception):
    """ An exception type for invalid model specifications.
    """
    pass


class Control(ModelObject):
    """ Represents a control variable in a model.
    """

    def ast(self):
        args = [ (ast.Name(self.name), self._ast_impl()) ]
        return ast.Call(ast.Name('def_control'), args, print_hint='long')

    def _ast_impl(self):
        raise NotImplementedError


class Metric(ModelObject):
    """ Represents a single metric in a model.
    """

    # The variables to control (adjust) for.
    control_for = List(Instance('Control'))

    def ast(self):
        args = [ (ast.Name(self.name), self._ast_impl()) ]
        if self.control_for:
            args += [ (ast.Name('control_for'),
                       ast_macros.seq_to_vector(
                           [ c.name for c in self.control_for ])) ]
        return ast.Call(ast.Name('def_metric'), args, print_hint='long')

    def _ast_impl(self):
        raise NotImplementedError


class CompositeScore(ModelObject):
    """ Combines group-level metric scores into a single composite score.
    """
    
    def ast(self):
        if self._ast_nonstandard_eval():
            return ast.Call(ast.Name('def_composite_score'),
                            (ast.Name(self.name), self._ast_impl()),
                            print_hint = 'long')
        else:
            return ast.Call(ast.Name('def_composite_score_q'),
                            ast.Constant(self.name),
                            *self._ast_impl())
        
    def _ast_impl(self):
        raise NotImplementedError
    
    def _ast_nonstandard_eval(self):
        return True
