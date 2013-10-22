import collections
import errno
import os
import shutil
from stango.context import Context
from stango.files import Files

STANGO_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')


class Stango(object):
    HOOK_NAMES = ['post_render_hook']

    def __init__(self):
        self.index_file = None
        self.files = Files()
        self.template_dirs = [STANGO_TEMPLATE_DIR]

        # By default, all hooks return the data unmodified
        default_hook = lambda context, data: data
        self.hooks = {hook_name: default_hook for hook_name in self.HOOK_NAMES}

    def view(self, filespec, mode):
        assert mode in ('generating', 'serving')

        context = Context(self, mode, filespec)
        view_result = filespec.view(context, **filespec.kwargs)

        if isinstance(view_result, str):
            byte_result = view_result.encode('utf-8')
        elif isinstance(view_result, (bytes, bytearray)):
            byte_result = view_result
        elif (hasattr(view_result, 'read') and
              isinstance(view_result.read, collections.Callable)):
            file_contents = view_result.read()
            if isinstance(file_contents, str):
                byte_result = file_contents.encode('utf-8')
            elif isinstance(file_contents, (bytes, bytearray)):
                byte_result = file_contents
            else:
                raise ValueError('Contents of the file-like object, returned by view %r for path %r, is not a str, bytes or bytearray instance' % (filespec.view.__name__, filespec.path))
        else:
            raise ValueError('The result of view %r for path %r is not a str, bytes or bytearray instance or a file-like object' % (filespec.view.__name__, filespec.path))

        result = self.hooks['post_render_hook'](context, byte_result)
        if not isinstance(result, (bytes, bytearray)):
            raise ValueError('The result of post_render_hook is not a bytes or bytearray instance for %s' % context.realpath)

        return result

    def make_server(self, host, port, verbose=False):
        from stango.http import StangoHTTPServer

        if port < 0 or port > 65535:
            raise ValueError('Invalid port %r' % port)

        httpd = StangoHTTPServer((host, port), self)
        httpd.verbose = verbose

        return httpd

    def generate(self, outdir):
        if os.path.exists(outdir):
            if os.path.isdir(outdir):
                # Delete the contents outdir, not outdir itself
                for entry in os.listdir(outdir):
                    path = os.path.join(outdir, entry)
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
            else:
                raise ValueError('%r is not a directory' % outdir)

        try:
            os.mkdir(outdir)
        except OSError as err:
            if err.errno != errno.EEXIST:
                raise

        for filespec in self.files:
            path = os.path.join(outdir, filespec.realpath(self.index_file))

            if not os.path.exists(os.path.dirname(path)):
                os.makedirs(os.path.dirname(path))

            with open(path, 'wb') as fobj:
                data = self.view(filespec, mode='generating')
                fobj.write(data)

    def add_hook(self, hook_name, hook_func):
        if hook_name not in self.HOOK_NAMES:
            raise ValueError('%s is not a valid hook name' % hook_name)

        if not isinstance(hook_func, collections.Callable):
            raise TypeError('hook_func must be callable')

        self.hooks[hook_name] = hook_func
