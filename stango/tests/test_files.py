from stango.files import Filespec, Files, files_from_dir, files_from_tar
from stango.views import file_from_tar, static_file
from stango.tests import StangoTestCase, make_suite

import operator
import os

def dummy_view(context):
    return ''

class FilesTestCase(StangoTestCase):
    def test_Files_init(self):
        files = Files(
            ('', dummy_view),
            ('file1', dummy_view),
            ('file2', dummy_view, {'foo': 'bar'}),
            ('dir/', dummy_view),
            ('path/to/file', dummy_view),
            ('path/to/dir/', dummy_view),
        )
        self.eq(
            list(files),
            [
                Filespec('', dummy_view),
                Filespec('file1', dummy_view),
                Filespec('file2', dummy_view, {'foo': 'bar'}),
                Filespec('dir/', dummy_view),
                Filespec('path/to/file', dummy_view),
                Filespec('path/to/dir/', dummy_view),
            ]
        )

    def test_nested_Files(self):
        files1 = Files(
            ('file1', dummy_view),
            ('file2', dummy_view, {'foo': 'bar'}),
        )

        files2 = Files(
            ('file3', dummy_view),
            ('file4', dummy_view),
        )

        combined_files = Files(
            ('file0', dummy_view),
            files1,
            files2,
            ('file5', dummy_view),
        )

        self.eq(
            list(combined_files),
            [
                Filespec('file0', dummy_view),
                Filespec('file1', dummy_view),
                Filespec('file2', dummy_view, {'foo': 'bar'}),
                Filespec('file3', dummy_view),
                Filespec('file4', dummy_view),
                Filespec('file5', dummy_view),
            ]
        )

    def test_Files_init_None_as_filespec(self):
        exc = self.assert_raises(TypeError, Files, None)
        self.eq(str(exc), 'expected a Filespec object or tuple, got None')

    def test_Files_init_empty_tuple_as_filespec(self):
        exc = self.assert_raises(TypeError, Files, ())
        self.eq(str(exc), 'expected a tuple of the form (path, view[, kwargs])')

    def test_Files_init_nonstring_as_path(self):
        exc = self.assert_raises(TypeError, Files, (1, dummy_view))
        self.eq(str(exc), 'path must be a str, not 1')

    def test_Files_init_path_starts_with_slash(self):
        exc = self.assert_raises(ValueError, Files, ('/foo', dummy_view))
        self.eq(str(exc), "'/foo': path must not start with /")

    def test_Files_init_view_is_not_callable(self):
        exc = self.assert_raises(TypeError, Files, ('foo', 1))
        self.eq(str(exc), "'foo': view must be callable")

    def test_Files_init_kwargs_is_not_dict(self):
        exc = self.assert_raises(TypeError, Files, ('foo', dummy_view, 1))
        self.eq(str(exc), "'foo': kwargs must be a dict")

    def test_Files_ops(self):
        files = Files()

        files.append(Filespec('a', dummy_view))
        files.append(('b', dummy_view, {'foo': 'bar'}))

        files += Files()
        files += Files(('c', dummy_view))
        files += [
            ('d', dummy_view),
            ('e', dummy_view),
        ]

        files.insert(0, ('0', dummy_view))
        files.insert(len(files), Filespec('999', dummy_view))

        del files[1]

        self.eq(
            list(files),
            [
                Filespec('0', dummy_view),
                Filespec('b', dummy_view, {'foo': 'bar'}),
                Filespec('c', dummy_view),
                Filespec('d', dummy_view),
                Filespec('e', dummy_view),
                Filespec('999', dummy_view),
            ]
        )

        assert [] == Files()
        assert [None] != Files()
        assert Files(('a', dummy_view)) != [None]

    def test_Files_ops_type_checking(self):
        files = Files()

        # append
        exc = self.assert_raises(TypeError, files.append, None)
        self.eq(str(exc), 'expected a Filespec object or tuple, got None')

        # +=
        exc = self.assert_raises(TypeError, operator.iadd, files, [None])
        self.eq(str(exc), 'expected a Filespec object or tuple, got None')

        # insert
        exc = self.assert_raises(TypeError, files.insert, 0, None)
        self.eq(str(exc), 'expected a Filespec object or tuple, got None')

        # __setitem__
        exc = self.assert_raises(TypeError, operator.setitem, files, 0, None)
        self.eq(str(exc), 'expected a Filespec object or tuple, got None')

    def test_files_from_dir(self):
        path = os.path.join(self.data_path, 'static')
        files = files_from_dir('foo', path)
        self.eq(
            sorted((x.path, x.view, x.kwargs) for x in files),
            [
                (
                    os.path.join('foo', self.data_path, 'static/file.txt'),
                    static_file,
                    {'path': os.path.join(self.data_path, 'static/file.txt')},
                ),
                (
                    os.path.join('foo', self.data_path, 'static/other.txt'),
                    static_file,
                    {'path': os.path.join(self.data_path, 'static/other.txt')},
                ),
            ],
        )

    def test_files_from_dir_empty_basepath(self):
        path = os.path.join(self.data_path, 'static')
        files = files_from_dir('', path)
        self.eq(
            sorted((x.path, x.view, x.kwargs) for x in files),
            [
                (
                    os.path.join(self.data_path, 'static/file.txt'),
                    static_file,
                    {'path': os.path.join(self.data_path, 'static/file.txt')},
                ),
                (
                    os.path.join(self.data_path, 'static/other.txt'),
                    static_file,
                    {'path': os.path.join(self.data_path, 'static/other.txt')},
                ),
            ],
        )

    def test_files_from_dir_strip(self):
        strip = self.data_path.count('/') + 2
        path = os.path.join(self.data_path, 'static')

        files = files_from_dir('foo', path, strip=strip)
        self.eq(
            sorted((x.path, x.view, x.kwargs) for x in files),
            [
                (
                    'foo/file.txt',
                    static_file,
                    {'path': os.path.join(self.data_path, 'static/file.txt')},
                ),
                (
                    'foo/other.txt',
                    static_file,
                    {'path': os.path.join(self.data_path, 'static/other.txt')},
                ),
            ],
        )

    def test_files_from_tar(self):
        tar = os.path.join(self.data_path, 'test.tar')
        files = files_from_tar('foo', tar)
        self.eq(
            sorted((x.path, x.view, x.kwargs['member']) for x in files),
            [
                ('foo/static/file.txt', file_from_tar, 'static/file.txt'),
                ('foo/static/other.txt', file_from_tar, 'static/other.txt'),
            ],
        )

    def test_files_from_tar_empty_basepath(self):
        tar = os.path.join(self.data_path, 'test.tar')
        files = files_from_tar('', tar)
        self.eq(
            sorted((x.path, x.view, x.kwargs['member']) for x in files),
            [
                ('static/file.txt', file_from_tar, 'static/file.txt'),
                ('static/other.txt', file_from_tar, 'static/other.txt'),
            ],
        )

    def test_files_from_tar_strip(self):
        tar = os.path.join(self.data_path, 'test.tar')
        files = files_from_tar('foo', tar, strip=1)
        self.eq(
            sorted((x.path, x.view, x.kwargs['member']) for x in files),
            [
                ('foo/file.txt', file_from_tar, 'static/file.txt'),
                ('foo/other.txt', file_from_tar, 'static/other.txt'),
            ],
        )


def suite():
    return make_suite(FilesTestCase)
