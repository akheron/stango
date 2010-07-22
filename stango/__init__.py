import collections
import operator
import os
import shutil
import tarfile
from functools import reduce
from stango.views import file_from_tar, static_file
from stango.context import Context


class File(object):
    def __init__(self, path, view, kwargs):
        self.path = path
        self.realpath = path
        self.view = view
        self.kwargs = kwargs

    def is_incomplete(self):
        return not self.path or self.path.endswith('/')

    def complete(self, index_file):
        if self.is_incomplete():
            self.realpath = os.path.join(self.path, index_file)


class files(list):
    def _files(self, args):
        for i, arg in enumerate(args):
            if not isinstance(arg, tuple):
                raise ValueError('argument %d is not a tuple' % i)
            if len(arg) < 2 or len(arg) > 3:
                raise ValueError('argument %d is not a 2-tuple or 3-tuple' % i)

            if len(arg) == 2:
                path, view = arg
                kwargs = {}
            else:
                path, view, kwargs = arg

            if not isinstance(path, str) or path.startswith('/'):
                raise ValueError('invalid path %r in arg %d' % (path, i))

            yield File(path, view, kwargs)

    def __init__(self, *args):
        super(files, self).__init__()
        self.extend(list(self._files(args)))

    @staticmethod
    def _served_path(basepath, filename, strip):
        if strip > 0:
            parts = filename.split('/')[strip:]
            if not parts:
                return ''
            served_name = os.path.join(*parts)
        else:
            served_name = filename
        return os.path.join(basepath, served_name)


    @staticmethod
    def from_tar(basepath, tarname, strip=0):
        tar = tarfile.open(tarname, 'r')
        def _gen():
            for member in tar.getmembers():
                if not member.isfile():
                    continue
                filename = files._served_path(basepath, member.name, strip)
                if filename:
                    yield files((
                            filename,
                            file_from_tar,
                            { 'tar': tar, 'member': member.name }))
        return reduce(operator.add, _gen())

    @staticmethod
    def from_dir(basepath, dir_, strip=0):
        def _gen():
            for dirpath, dirnames, filenames in os.walk(dir_):
                for filename in filenames:
                    path = os.path.join(dirpath, filename)
                    yield files((
                            files._served_path(basepath, path, strip),
                            static_file,
                            { 'path': os.path.join(dirpath, filename) }))
        return reduce(operator.add, _gen())

# Alias 'files' to 'files_' so that 'files' can be used as a parameter
# name and local variable name without hiding the class
files_ = files

class Manager(object):
    HOOKS = ['post_view_hook']

    def __init__(self):
        self.index_file = None
        self.files = files()

        # By default, all hooks return the data unmodified
        default_hook = lambda context, data: data
        self.hooks = {hook_name: default_hook for hook_name in self.HOOKS}

    def complete_files(self):
        if self.index_file:
            for filespec in self.files:
                filespec.complete(self.index_file)
        else:
            incomplete = []
            for filespec in self.files:
                if filespec.is_incomplete():
                    incomplete.append(filespec)
            if incomplete:
                raise ValueError('Incomplete files and no index_file: %s' %
                                 ', '.join(incomplete))

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
