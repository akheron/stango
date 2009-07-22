import os
import manage
import views

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
