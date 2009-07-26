import os
import shutil
import sys
import traceback
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
        path = self.path[1:]

        if self.serve_static_file(path):
            return

        if not path or path.endswith('/'):
            realpath = os.path.join(path, self.server.index_file)
        else:
            realpath = path

        for file in self.server.files:
            if file.realpath == realpath:
                self.start_response(
                    200, ['Content-Type: text/html; charset=UTF-8'])
                self.wfile.write(file.view(**file.kwargs))
                break
        else:
            self.start_response(404)
            self.wfile.write('Not found: %s' % self.path)


class StangoHTTPServer(HTTPServer):
    def __init__(self, server_address, files, index_file):
        self.files = files
        self.index_file = index_file
        HTTPServer.__init__(self, server_address, StangoRequestHandler)


def serve(files, index_file, port):
    if port < 0 or port > 65535:
        print >>sys.stderr, 'Unable to serve on invalid port %r' % port
        return 1

    addr = '127.0.0.1'

    print 'Starting server on on http://%s:%d/' % (addr, port)
    httpd = StangoHTTPServer((addr, port), files, index_file)
    httpd.serve_forever()


def render(files, outdir):
    if os.path.exists(outdir):
        if os.path.isdir(outdir):
            shutil.rmtree(outdir)
        else:
            print >>sys.stderr, '%r is not a directory' % outdir
            return 1

    if os.path.isdir('static'):
        shutil.copytree('static', 'out')

    for file in files:
        path = os.path.join(outdir, file.realpath)

        if os.path.exists(path):
            print >>sys.stderr, '%r exists in both static/ and files.py' % \
                file.realpath

        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))

        fobj = open(path, 'w')
        try:
            fobj.write(file.view(**file.kwargs))
        finally:
            fobj.close()


def print_help():
        print '''\
usage: %s subcmd [args...]

subcommands:
    serve [port]

        Serve the pages on http://localhost:<port>/. <port> defaults
        to 8080.

    render [outdir]

        Render the pages as flat files to directory <outdir>, which
        defaults to 'out'.
''' % sys.argv[0]
        sys.exit(2)


def run(files_module):
    if not hasattr(files_module, 'files'):
        print >>sys.stderr, "'files.py' doesn't define the 'files' variable"
        sys.exit(1)
    files = files_module.files

    if hasattr(files_module, 'index_file'):
        index_file = files_module.index_file
        for file in files:
            file.complete(index_file)
    else:
        index_file = None

    if len(sys.argv) < 2 or sys.argv[1] not in ['serve', 'render']:
        print_help()

    if sys.argv[1] == 'serve':
        if len(sys.argv) == 2:
            port = 8080
        elif len(sys.argv) == 3:
            try:
                port = int(sys.argv[2])
            except ValueError:
                print_help()
        else:
            print_help()

        sys.exit(serve(files, index_file, port) or 0)

    elif sys.argv[1] == 'render':
        if len(sys.argv) == 2:
            outdir = 'out'
        elif len(sys.argv) == 3:
            outdir = sys.argv[2]
        else:
            print_help()

        sys.exit(render(files, outdir) or 0)

    else:
        print_usage()
