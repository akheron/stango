from datetime import datetime
import os
import shutil
import sys
import unittest

class StangoTestCase(unittest.TestCase):
    def setup(self):
        pass

    def teardown(self):
        pass

    def eq(self, a, b):
        return self.assertEqual(a, b)

    def assert_raises(self, exc_class, func, *args, **kwargs):
        '''Like assertRaises() but returns the exception'''
        try:
            func(*args, **kwargs)
        except exc_class as exc:
            return exc
        else:
            raise AssertionError('%s was not raised' % exc_class.__name__)

    def tempdir(self):
        path = os.path.join('tmp', self.id())
        if os.path.exists(path):
            shutil.rmtree(path)
        os.makedirs(path)
        return path


    # Don't override these in test code

    def setUp(self):
        dirpath = os.path.dirname(__file__)
        self.template_path = os.path.join(dirpath, 'templates')
        self.data_path = os.path.relpath(os.path.join(dirpath, 'data'))
        self.setup()

    def tearDown(self):
        self.teardown()


def view_value(value):
    '''Construct a view that returns the given value when called'''
    def value_returner(context):
        return value
    return value_returner


def view_template(template_name):
    '''Construct a view that renders the given template when called'''
    def template_renderer(context, **kwargs):
        return context.render_template(template_name, **kwargs)
    return template_renderer


def make_suite(cls):
    '''Makes a suite from all test functions in a TestCase class'''
    return unittest.TestLoader().loadTestsFromTestCase(cls)


def suite():
    from . import \
        test_files, test_generate, test_main, test_manager, test_server, \
        test_views
    suite = unittest.TestSuite()
    suite.addTest(test_files.suite())
    suite.addTest(test_generate.suite())
    suite.addTest(test_main.suite())
    suite.addTest(test_manager.suite())
    suite.addTest(test_server.suite())
    suite.addTest(test_views.suite())
    return suite


def run(verbose=False):
    return unittest.TextTestRunner(verbosity=(2 if verbose else 1)).run(suite())
