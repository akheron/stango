def file_from_tar(context, tar, member):
    return tar.extractfile(member).read()

def static_file(context, path):
    with open(path, 'rb') as fobj:
        return fobj.read()
