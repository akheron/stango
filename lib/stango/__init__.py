import operator
import os
import tarfile
from stango.views import file_from_tar, static_file

class File(object):
    def __init__(self, path, view, kwargs):
        self.path = path
        self.realpath = path
        self.view = view
        self.kwargs = kwargs

    def complete(self, index_file):
        if not self.path or self.path.endswith('/'):
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

            if not isinstance(path, basestring) or path.startswith('/'):
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
