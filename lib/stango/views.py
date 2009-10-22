def file_from_tar(tar, member):
    return tar.extractfile(member).read()

def static_file(path):
    fobj = open(path)
    try:
        return fobj.read()
    finally:
        fobj.close()
