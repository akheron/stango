from io import StringIO
import os
import sys

import stango.autoreload
import stango.main
from stango import Manager

from . import StangoTestCase, make_suite

# A fake HTTP server class whose serve_forever returns right away
class FakeHTTPServer(object):
    def serve_forever(self):
        return

class MainTestCase(StangoTestCase):
    def setup(self):
        self.monkey_patches = []
        self.saved_argv = None
        self.saved_stdout = sys.stdout
        self.saved_stderr = sys.stderr
        self.saved_cwd = os.getcwd()

        self.temp = self.tempdir()
        sys.stdout = StringIO()
        sys.stderr = StringIO()
        os.chdir(self.temp)

    def teardown(self):
        os.chdir(self.saved_cwd)
        sys.stderr = self.saved_stderr
        if self.saved_argv:
            sys.argv = self.saved_argv
        sys.stdout = self.saved_stdout
        sys.stderr = self.saved_stderr
        for cls, attr, orig_value in self.monkey_patches:
            setattr(cls, attr, orig_value)

    def set_argv(self, *argv):
        if not self.saved_argv:
            # Save the original sys.argv only once
            self.saved_argv = sys.argv
        sys.argv = list(argv)

    def write_config(self, text):
        with open('conf.py', 'w') as fobj:
            fobj.write(text)

    def monkey_patch(self, cls, attr, value):
        self.monkey_patches.append((cls, attr, getattr(cls, attr)))
        setattr(cls, attr, value)

    # Tests start from here

    def test_empty_args(self):
        self.set_argv('stango')
        exc = self.assert_raises(SystemExit, stango.main.run)
        self.eq(exc.args[0], 2)

    def test_no_conf_py(self):
        self.set_argv('stango', 'generate')
        exc = self.assert_raises(SystemExit, stango.main.run)
        self.eq(exc.args[0], 1)
        self.eq(sys.stderr.getvalue(), 'conf.py not found\n')

    def test_no_files_in_config(self):
        self.write_config('')
        self.set_argv('stango', 'generate', 'out')
        exc = self.assert_raises(SystemExit, stango.main.run)
        self.eq(exc.args[0], 1)
        self.eq(sys.stdout.getvalue(), '')
        self.eq(sys.stderr.getvalue(), "conf.py doesn't define the 'files' variable\n")

    def test_defaults(self):
        self.write_config('''\
from stango import Files
files = Files()
''')
        self.set_argv('stango', 'generate')

        def fake_generate(mgr, outdir):
            self.eq(outdir, 'out')
            return mgr
        self.monkey_patch(Manager, 'generate', fake_generate)

        exc = self.assert_raises(SystemExit, stango.main.run)
        manager = exc.args[0]

        self.eq(manager.files, [])
        self.eq(manager.index_file, None)

    def test_generate_config_values(self):
        self.write_config('''\
from stango import Files
index_file = 'index.html'
def post_render_hook(context, data):
    return data + 'bar'
files = Files(('', lambda x: 'foo'))
''')
        self.set_argv('stango', 'generate', 'quux')

        def fake_generate(mgr, outdir):
            self.eq(outdir, 'quux')
            return mgr
        self.monkey_patch(Manager, 'generate', fake_generate)

        exc = self.assert_raises(SystemExit, stango.main.run)
        manager = exc.args[0]

        self.eq(manager.files[0].view(None), 'foo')
        self.eq(manager.index_file, 'index.html')
        self.eq(manager.hooks['post_render_hook'](None, 'foo'), 'foobar')

    def test_quickstart(self):
        self.set_argv('stango', 'quickstart')
        self.assert_raises(SystemExit, stango.main.run)
        self.eq(
            sorted(os.listdir('.')),
            ['__init__.py', 'conf.py', 'static', 'templates', 'views.py']
        )

        self.set_argv('stango', 'generate', 'out')
        self.assert_raises(SystemExit, stango.main.run)

        self.eq(sorted(os.listdir('out')), ['greeting.html', 'index.html'])

    def test_runserver(self):
        self.set_argv('stango', 'runserver')
        self.write_config('''\
from stango import Files
index_file = 'index.html'
files = Files(('', lambda x: 'foo'))
''')

        def fake_autoreload(func, patterns):
            func()
        self.monkey_patch(stango.autoreload, 'main', fake_autoreload)

        def fake_make_server(mgr, host, port):
            self.eq(host, '127.0.0.1')
            self.eq(port, 8000)
            return FakeHTTPServer()
        self.monkey_patch(Manager, 'make_server', fake_make_server)

        stango.main.run()

    def test_runserver_explicit_port(self):
        self.set_argv('stango', 'runserver', '9876')
        self.write_config('''\
from stango import Files
index_file = 'index.html'
files = Files(('', lambda x: 'foo'))
''')

        def fake_autoreload(func, patterns):
            func()
        self.monkey_patch(stango.autoreload, 'main', fake_autoreload)

        def fake_make_server(mgr, host, port):
            self.eq(host, '127.0.0.1')
            self.eq(port, 9876)
            return FakeHTTPServer()
        self.monkey_patch(Manager, 'make_server', fake_make_server)

        stango.main.run()

    def test_runserver_explicit_host_and_port(self):
        self.set_argv('stango', 'runserver', '4.3.2.1:9876')
        self.write_config('''\
from stango import Files
index_file = 'index.html'
files = Files(('', lambda x: 'foo'))
''')

        def fake_autoreload(func, patterns):
            func()
        self.monkey_patch(stango.autoreload, 'main', fake_autoreload)

        def fake_make_server(mgr, host, port):
            self.eq(host, '4.3.2.1')
            self.eq(port, 9876)
            return FakeHTTPServer()
        self.monkey_patch(Manager, 'make_server', fake_make_server)

        stango.main.run()

def suite():
    return make_suite(MainTestCase)
