import errno
import os
import shutil
import sys
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

class StangoRequestHandler(BaseHTTPRequestHandler):
    def start_response(self, code, headers=[]):
        if code == 200:
            self.send_response(200)
            for header in headers:
                keyword, value = header.split(': ')
                self.send_header(keyword, value)
            self.end_headers()
        else:
            self.send_response(code)

    def serve_static_file(self, path):
        if os.path.isfile(os.path.join('static', path)):
            self.start_response(200)
            with open(os.path.join('static', path)) as fobj:
                self.wfile.write(fobj.read())
                return True
        else:
            return False

    def do_GET(self):
        # remove the leading /
        realpath = path = self.path[1:]

        if self.serve_static_file(path):
            return

        if self.server.index_file and (not path or path.endswith('/')):
            realpath = os.path.join(path, self.server.index_file)

        for file in self.server.files:
            if file.realpath == realpath:
                self.start_response(
                    200, ['Content-Type: text/html; charset=UTF-8'])
                self.wfile.write(file.view(**file.kwargs))
                break
        else:
            self.start_response(404)


class StangoHTTPServer(HTTPServer):
    def __init__(self, server_address, files, index_file):
        self.files = files
        self.index_file = index_file
        HTTPServer.__init__(self, server_address, StangoRequestHandler)


def serve(config, host, port):
    if port < 0 or port > 65535:
        print >>sys.stderr, 'Unable to serve on invalid port %r' % port
        return 1

    def do_serve():
        print 'Starting server on on http://%s:%d/' % (host, port)
        httpd = StangoHTTPServer((host, port),
                                 config['files'], config['index_file'])
        httpd.serve_forever()

    from stango.manage import autoreload
    autoreload.main(do_serve)


def render(config, outdir):
    print 'Rendering to %s...' % outdir
    if os.path.exists(outdir):
        if os.path.isdir(outdir):
            shutil.rmtree(outdir)
        else:
            print >>sys.stderr, '%r is not a directory' % outdir
            return 1

    if os.path.isdir('static'):
        shutil.copytree('static', outdir)

    try:
        os.mkdir(outdir)
    except OSError, err:
        if err.errno != errno.EEXIST:
            raise

    for file in config['files']:
        path = os.path.join(outdir, file.realpath)

        if os.path.exists(path):
            print >>sys.stderr, \
                'Warning: %r exists in both static/ and files list' % \
                file.realpath

        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))

        fobj = open(path, 'w')
        try:
            fobj.write(file.view(**file.kwargs))
        finally:
            fobj.close()

    print 'done.'
    return 0
