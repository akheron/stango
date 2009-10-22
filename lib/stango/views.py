def file_from_tar(tar, member):
    return tar.extractfile(member).read()
