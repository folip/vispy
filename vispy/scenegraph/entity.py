# -*- coding: utf-8 -*-
# Copyright (c) 2014, Vispy Development Team.
# Distributed under the (new) BSD License. See LICENSE.txt for more info.

from __future__ import division

from ..visuals import transforms
from ..util.event import EmitterGroup, Event
from .events import ScenePaintEvent, SceneMouseEvent

class Entity(object):

    """ Base class to represent a citizen of a scene. Typically an
    Entity is used to visualize something, although this is not strictly
    necessary. It may for instance also be used as a container to apply
    a certain transformation to a group of objects, or an object that
    performs a specific task without being visible.

    Each entity can have zero or more children. Each entity will
    typically have one parent, although multiple parents are allowed.
    It is recommended to use multi-parenting with care.
    """

    def __init__(self, parents=None):
        self.events = EmitterGroup(source=self,
                                   auto_connect=True,
                                   parents_change=Event,
                                   active_parent_change=Event,
                                   children_change=Event,
                                   mouse_press=SceneMouseEvent,
                                   mouse_move=SceneMouseEvent,
                                   mouse_release=SceneMouseEvent,
                                   paint=ScenePaintEvent,
                                   )

        # Entities are organized in a parent-children hierarchy
        self._children = set()
        # TODO: use weakrefs for parents.
        self._parents = set()
        if parents is not None:
            self.parents = parents

        # Components that all entities in vispy have
        self._transform = transforms.AffineTransform()

    @property
    def children(self):
        """ The list of children of this entity.
        """
        return list(self._children)

    @property
    def parents(self):
        """ Get/set the list of parents. Typically the tuple will have
        one element.
        """
        return list(self._parents)

    @parents.setter
    def parents(self, parents):
        # Test input
        if not hasattr(parents, '__iter__'):
            raise ValueError("Entity.parents must be iterable (got %s)" % type(parents))

        # Test that all parents are entities
        for p in parents:
            if not isinstance(p, Entity):
                raise ValueError('A parent of an entity must be an entity too,'
                                 ' not %s.' % p.__class__.__name__)
        
        # convert to set
        prev = self._parents.copy()
        parents = set(parents)
        
        with self.events.parents_change.blocker():
            # Remove from parents
            for parent in prev - parents:
                self.remove_parent(parent)
                
            # Add new
            for parent in parents - prev:
                self.add_parent(parent)

        self.events.parents_change(new=parents, old=prev)

    def add_parent(self, parent):
        if parent in self._parents:
            return
        self._parents.add(parent)
        parent._add_child(self)
        self.events.parents_change(added=parent)
        self.update()
        
    def remove_parent(self, parent):
        if parent not in self._parents:
            raise ValueError("Parent not in set of parents for this entity.")
        self._parents.remove(parent)
        parent._remove_child(self)
        self.events.parents_change(removed=parent)

    def _add_child(self, ent):
        self._children.add(ent)
        self.events.children_change(added=ent)

    def _remove_child(self, ent):
        self._children.remove(ent)
        self.events.children_change(removed=ent)

    def __iter__(self):
        return self._children.__iter__()

    @property
    def transform(self):
        """ The transform for this entity; maps from the local coordinate
        system of the entity to its parent's coordinate system.
        
        By default, this is an AffineTransform instance.
        """
        return self._transform

    @transform.setter
    def transform(self, tr):
        assert isinstance(tr, transforms.Transform)
        self._transform = tr
        self.update()

    def on_paint(self, event):
        """
        Paint this entity, given that we are drawing through 
        the given scene *path*.
        """
        pass
    
    def _process_paint_event(self, event):
        """
        Paint the entire tree of Entities beginnging here.            
        """
        for path in self.walk():
            event._set_path(path)
            entity = path[-1]
            entity.events.paint(event)

    def _process_mouse_event(self, event):
        """
        Propagate a mouse event through the scene tree starting at this Entity.
        """
        # 1. find all entities whose mouse-area includes the point of the click.
        # 2. send the event to each entity one at a time
        #    (we should use a specialized emitter for this, rather than 
        #     rebuild the emitter machinery!)
        
        # TODO: for now we send the event to all entities; need to use
        # picking to decide which entities should receive the event.
        for path in self.walk():
            event._set_path(path)
            entity = path[-1]
            getattr(entity.events, event.type)(event)

    def walk(self, path=None):
        """
        Return an iterator that walks the entire scene graph starting at this
        Entity. Yields a list of Entities for each path in the scenegraph.
        """
        # TODO: need some control over the order..
        #if path is None:
            #path = []
            #yield path, self
        #if len(self.children) > 0:
            #path = path + [self]
            #yield path, self.children
            #for ch in self:
                #for e in ch.walk(path):
                    #yield e
        path = (path or []) + [self]
        yield path
        for ch in self:
            for p in ch.walk(path):
                yield p
        
        

    def update(self):
        """
        Emit an event to inform Canvases that this Entity needs to be redrawn.
        """
        # TODO
        pass


    