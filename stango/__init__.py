import collections
import os
import shutil
from stango.context import Context
from stango.files import Files

class Manager(object):
    HOOKS = ['post_view_hook']

    def __init__(self):
        self.index_file = None
        self.files = Files()

        # By default, all hooks return the data unmodified
        default_hook = lambda context, data: data
        self.hooks = {hook_name: default_hook for hook_name in self.HOOKS}

    def complete_files(self):
        if self.index_file:
            self.files = [x.complete(self.index_file) for x in self.files]
        else:
            incomplete = []
            for filespec in self.files:
                if filespec.isdir():
                    incomplete.append(filespec)
            if incomplete:
                raise ValueError('Incomplete files and no index_file: %s' %
                                 ', '.join(repr(x.path) for x in incomplete))

    def get_context(self, filespec, rendering=False, serving=False):
        context = Context(self, filespec)
        context.rendering = rendering
        context.serving = serving
        return context

    def view(self, filespec, rendering=False, serving=False):
        context = self.get_context(filespec, rendering, serving)
        view_result = filespec.view(context, **filespec.kwargs)

        if isinstance(view_result, str):
            byte_result = view_result.encode('utf-8')
        elif isinstance(view_result, (bytes, bytearray)):
            byte_result = view_result
        else:
            raise ValueError('The result of view %r for file %s is not a str, bytes or bytearray instance' % (view, filespec.realpath))

        result = self.hooks['post_view_hook'](context, byte_result)
        if not isinstance(result, (bytes, bytearray)):
            raise ValueError('The result of %s is not a bytes or bytearray instance for %s' % (hook, filespec.realpath))

        return result

    def serve(self, host, port):
        from stango.http import StangoHTTPServer

        if port < 0 or port > 65535:
            raise ValueError('Invalid port %r' % port)

        self.complete_files()

        httpd = StangoHTTPServer((host, port), self)
        httpd.serve_forever()

    def render(self, outdir):
        self.complete_files()

        if os.path.exists(outdir):
            if os.path.isdir(outdir):
                shutil.rmtree(outdir)
            else:
                raise ValueError('%r is not a directory' % outdir)

        try:
            os.mkdir(outdir)
        except OSError as err:
            if err.errno != errno.EEXIST:
                raise

        for filespec in self.files:
            path = os.path.join(outdir, filespec.realpath)

            if not os.path.exists(os.path.dirname(path)):
                os.makedirs(os.path.dirname(path))

            with open(path, 'wb') as fobj:
                data = self.view(filespec, rendering=True)
                fobj.write(data)

    def add_hook(self, hook_name, hook_func):
        if hook_name not in self.HOOKS:
            raise ValueError('%s is not a valid hook name' % hook_name)

        if not isinstance(hook_func, collections.Callable):
            raise TypeError('hook_func must be callable')

        self.hooks[hook_name] = hook_func
