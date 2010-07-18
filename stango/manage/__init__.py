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

    def do_GET(self):
        # remove the leading /
        realpath = path = self.path[1:]

        if self.server.index_file and (not path or path.endswith('/')):
            realpath = os.path.join(path, self.server.index_file)

        for file in self.server.files:
            if file.realpath == realpath:
                headers = []
                self.start_response(200)
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
        print 'Starting server on http://%s:%d/' % (host, port)
        httpd = StangoHTTPServer((host, port),
                                 config['files'], config['index_file'])
        httpd.serve_forever()

    from stango.manage import autoreload
    autoreload.main(do_serve, config['autoreload'])


def render(config, outdir):
    print 'Rendering to %s...' % outdir
    if os.path.exists(outdir):
        if os.path.isdir(outdir):
            shutil.rmtree(outdir)
        else:
            print >>sys.stderr, '%r is not a directory' % outdir
            return 1

    try:
        os.mkdir(outdir)
    except OSError, err:
        if err.errno != errno.EEXIST:
            raise

    post_render_hook = config['post_render_hook']
    if post_render_hook and not callable(post_render_hook):
        print >>sys.stderr, 'Error: post_render_hook must be callable'
        return 1

    for file in config['files']:
        path = os.path.join(outdir, file.realpath)

        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))

        fobj = open(path, 'w')
        try:
            data = file.view(**file.kwargs)
            if post_render_hook:
                data = post_render_hook(file.realpath, data)
                if not isinstance(data, basestring):
                    print >>sys.stderr, 'Warning: post_render_hook returned a non-string for %s, writing an empty file' % file.realpath
                    data = ''
            fobj.write(data)
        finally:
            fobj.close()

    print 'done.'
    return 0
