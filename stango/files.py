from functools import reduce
from stango.views import file_from_tar, static_file
import os
import tarfile

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


class Files(list):
    def _files(self, args):
        for i, arg in enumerate(args):
            if isinstance(arg, Files):
                for filespec in arg:
                    yield filespec

            elif not isinstance(arg, tuple):
                raise ValueError('argument %d is not a tuple or Files object' %
                                 i)
            elif len(arg) < 2 or len(arg) > 3:
                raise ValueError('argument %d is not a 2-tuple or 3-tuple' % i)

            else:
                if len(arg) == 2:
                    path, view = arg
                    kwargs = {}
                else:
                    path, view, kwargs = arg

                if not isinstance(path, str) or path.startswith('/'):
                    raise ValueError('invalid path %r in arg %d' % (path, i))

                yield File(path, view, kwargs)

    def __init__(self, *args):
        super(Files, self).__init__()
        self.extend(list(self._files(args)))


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
            result.append(File(
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
            result.append(File(
                _served_path(basepath, path, strip),
                static_file,
                {'path': os.path.join(dirpath, filename)}
            ))
    return result
