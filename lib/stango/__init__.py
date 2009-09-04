import operator
import os
import tarfile

class File(object):
    def __init__(self, path, view, kwargs):
        self.path = path
        self.realpath = path
        self.view = view
        self.kwargs = kwargs

    def complete(self, index_file):
        if not self.path or self.path.endswith('/'):
            self.realpath = os.path.join(self.path, index_file)


def files(*args):
    import os

    def _files(*args):
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

    return list(_files(*args))


def view_file_from_tar(tar, member):
    return tar.extractfile(member).read()


def files_from_tar(basepath, tarname, strip=0):
    tar = tarfile.open(tarname, 'r')
    def _files():
        for member in tar.getmembers():
            if not member.isfile():
                continue
            if strip > 0:
                parts = member.name.split('/')[strip:]
                if not parts:
                    continue
                served_name = os.path.join(*parts)
            else:
                served_name = member.name
            filename = os.path.join(basepath, served_name)
            yield files((
                    filename,
                    view_file_from_tar,
                    { 'tar': tar, 'member': member.name }))
    return reduce(operator.add, _files())
