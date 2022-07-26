from .events import TreesManager
from .mixins import BaseNestedSets

# __mixins__ = [MPTTMixin]
# __all__ = ['MPTTMixin', 'mptt_sessionmaker']

tree_manager = TreesManager(BaseNestedSets)
tree_manager.register_events()
mptt_sessionmaker = tree_manager.register_factory
