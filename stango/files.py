from functools import reduce
from stango.views import file_from_tar, static_file
import collections
import os
import tarfile

FilespecBase = collections.namedtuple('Filespec', 'path view kwargs realpath')

class Filespec(FilespecBase):
    def __new__(cls, path, view, kwargs={}, realpath=None):
        if realpath is None:
            realpath = path

        if not isinstance(path, str):
            raise TypeError('path must be a str, not %r' % path)

        if path.startswith('/'):
            raise ValueError('%r: path must not start with /' % path)

        if not isinstance(view, collections.Callable):
            raise TypeError('%r: view must be callable' % path)

        if not isinstance(kwargs, dict):
            raise TypeError('%r: kwargs must be a dict' % path)

        return super(Filespec, cls).__new__(cls, path, view, kwargs, realpath)

    def isdir(self):
        return not self.realpath or self.realpath.endswith('/')

    def complete(self, index_file):
        assert index_file is not None

        if not self.isdir():
            return self
        else:
            return Filespec(
                self.path,
                self.view,
                self.kwargs,
                os.path.join(self.path, index_file),
            )

class Files(collections.MutableSequence):
    def __init__(self, *args):
        self._data = []

        for arg in args:
            if isinstance(arg, tuple):
                self.append(arg)
            elif isinstance(arg, collections.Iterable):
                for item in arg:
                    self.append(item)
            else:
                self.append(arg)

    def _verify(self, arg):
        if isinstance(arg, Filespec):
            return arg

        elif isinstance(arg, tuple):
            if len(arg) < 2 or len(arg) > 3:
                raise TypeError('expected a tuple of the form (path, view[, kwargs])')

            if len(arg) == 2:
                path, view = arg
                kwargs = {}
            else:
                path, view, kwargs = arg

            return Filespec(path, view, kwargs)

        else:
            raise TypeError('expected a Filespec object or tuple, got %r' % arg)

    def __len__(self):
        return len(self._data)

    def __getitem__(self, index):
        return self._data[index]

    def __setitem__(self, index, value):
        self._data[index] = self._verify(value)

    def __delitem__(self, index):
        del self._data[index]

    def insert(self, index, value):
        self._data.insert(index, self._verify(value))

    def __eq__(self, other):
        if len(self) != len(other):
            return False

        for a, b in zip(self, other):
            if a != b:
                return False

        return True


def _served_path(basepath, filename, strip):
    if strip > 0:
        parts = filename.split('/')[strip:]
        if not parts:
            return ''
        served_name = os.path.join(*parts)
    else:
        served_name = filename
    return os.path.join(basepath, served_name)


def files_from_tar(basepath, tarname, strip=0):
    tar = tarfile.open(tarname, 'r')
    result = Files()
    for member in tar.getmembers():
        if not member.isfile():
            continue
        filename = _served_path(basepath, member.name, strip)
        if filename:
            result.append((
                filename,
                file_from_tar,
                {'tar': tar, 'member': member.name}
            ))
    return result


def files_from_dir(basepath, dir_, strip=0):
    result = Files()
    for dirpath, dirnames, filenames in os.walk(dir_):
        for filename in filenames:
            path = os.path.join(dirpath, filename)
            result.append((
                _served_path(basepath, path, strip),
                static_file,
                {'path': os.path.join(dirpath, filename)}
            ))
    return result
