from stango import Stango
from stango.files import files_from_dir, files_from_tar

import os

from . import StangoTestCase, make_suite

def filelist(path):
    result = []
    for dirpath, dirnames, filenames in os.walk(path):
        rel = os.path.relpath(dirpath, path)
        for filename in filenames:
            result.append(os.path.join(rel, filename))
    return sorted(result)

class ViewsTestCase(StangoTestCase):
    def setup(self):
        self.tmp = self.tempdir()
        self.manager = Stango()

    def test_static_file(self):
        # stango.files.files_from_dir uses the stango.views.static_file view
        strip = self.data_path.count('/') + 2
        path = os.path.join(self.data_path, 'static')
        self.manager.files += files_from_dir('foo', path, strip=strip)
        self.manager.generate(self.tmp)
        self.eq(
            filelist(self.tmp),
            [
                'foo/file.txt',
                'foo/other.txt',
            ]
        )
        with open(os.path.join(self.tmp, 'foo/file.txt')) as fobj:
            self.eq(fobj.read(), 'This is a test file\n')
        with open(os.path.join(self.tmp, 'foo/other.txt')) as fobj:
            self.eq(fobj.read(), 'This is also a test file\n')

    def test_file_from_tar(self):
        # stango.files.files_from_dir uses the stango.views.file_from_tar view
        tar = os.path.join(self.data_path, 'test.tar')
        self.manager.files += files_from_tar('foo', tar)
        self.manager.generate(self.tmp)
        self.eq(
            filelist(self.tmp),
            [
                'foo/static/file.txt',
                'foo/static/other.txt',
            ]
        )
        with open(os.path.join(self.tmp, 'foo/static/file.txt')) as fobj:
            self.eq(fobj.read(), 'This is a test file\n')
        with open(os.path.join(self.tmp, 'foo/static/other.txt')) as fobj:
            self.eq(fobj.read(), 'This is also a test file\n')

def suite():
    return make_suite(ViewsTestCase)
