import os
import unittest

from stango import Manager
from stango.files import Files
from stango.tests import StangoTestCase, make_suite

class ManagerTestCase(StangoTestCase):
    def setup(self):
        self.manager = Manager()

    def test_manager_defaults(self):
        self.eq(self.manager.files, Files())
        self.eq(self.manager.index_file, None)

    def test_add_hook(self):
        def hook(context, data):
            pass

        self.manager.add_hook('post_render_hook', hook)
        self.eq(self.manager.hooks, {'post_render_hook': hook})

    def test_add_hook_invalid_name(self):
        def hook(context, data):
            pass

        exc = self.assert_raises(ValueError, self.manager.add_hook,
                                 'nonexistent_hook', hook)
        self.eq(str(exc), 'nonexistent_hook is not a valid hook name')

    def test_add_noncallable_hook(self):
        exc = self.assert_raises(TypeError, self.manager.add_hook,
                                 'post_render_hook', 5)
        self.eq(str(exc), 'hook_func must be callable')


def suite():
    return make_suite(ManagerTestCase)
