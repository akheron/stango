from stango import Manager
from stango.files import Files

import functools
from threading import Thread
from urllib.request import urlopen
from urllib.error import HTTPError

from . import StangoTestCase, make_suite, view_value, view_template

class ServeTestCase(StangoTestCase):
    def setup(self):
        self.manager = Manager()
        self.manager.index_file = 'index.html'

    def serve(func):
        @functools.wraps(func)
        def wrapper(self):
            gen = func(self)

            httpd = next(gen)
            httpd.allow_reuse_address = True

            server_thread = Thread(target=httpd.serve_forever)
            server_thread.start()

            try:
                self.assert_raises(StopIteration, gen.send, None)

            finally:
                httpd.shutdown()
                server_thread.join()
                httpd.socket.close()

        return wrapper


    @serve
    def test_simple(self):
        self.manager.files = Files(
            ('', view_value('foobar')),
        )
        yield self.manager.make_server('127.0.0.1', 8080)

        data = urlopen('http://127.0.0.1:8080/')
        self.eq(data.read(), b'foobar')

    @serve
    def test_real_path(self):
        self.manager.files = Files(
            ('', view_value('bazbuzz')),
        )
        yield self.manager.make_server('127.0.0.1', 8080)

        data = urlopen('http://127.0.0.1:8080/index.html')
        self.eq(data.read(), b'bazbuzz')

    @serve
    def test_404(self):
        self.manager.files = Files(
            ('', view_value('foobar')),
        )
        yield self.manager.make_server('127.0.0.1', 8080)

        url = 'http://127.0.0.1:8080/nonexistent'
        exc = self.assert_raises(HTTPError, urlopen, url)
        self.eq(exc.code, 404)


def suite():
    return make_suite(ServeTestCase)
