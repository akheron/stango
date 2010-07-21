import errno
import os
import shutil
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import collections

def view_and_encode(file):
    data = file.view(**file.kwargs)

    if not isinstance(data, (str, bytes, bytearray)):
        print('Warning: The result of the view %r is not a str, bytes or bytearray instance, writing an empty file' % (view, file.realpath), file=sys.stderr)
        data = b''

    if isinstance(data, str):
        data = data.encode('utf-8')

    return data

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
                self.wfile.write(view_and_encode(file))
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
        print('Unable to serve on invalid port %r' % port, file=sys.stderr)
        return 1

    def do_serve():
        print('Starting server on http://%s:%d/' % (host, port))
        httpd = StangoHTTPServer((host, port),
                                 config['files'], config['index_file'])
        httpd.serve_forever()

    from stango.manage import autoreload
    autoreload.main(do_serve, config['autoreload'])


def render(config, outdir):
    print('Rendering to %s...' % outdir)
    if os.path.exists(outdir):
        if os.path.isdir(outdir):
            shutil.rmtree(outdir)
        else:
            print('%r is not a directory' % outdir, file=sys.stderr)
            return 1

    try:
        os.mkdir(outdir)
    except OSError as err:
        if err.errno != errno.EEXIST:
            raise

    post_render_hook = config['post_render_hook']
    if post_render_hook and not isinstance(post_render_hook, collections.Callable):
        print('Error: post_render_hook must be callable', file=sys.stderr)
        return 1

    for file in config['files']:
        path = os.path.join(outdir, file.realpath)

        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))

        fobj = open(path, 'wb')
        try:
            data = view_and_encode(file)
            if post_render_hook:
                data = post_render_hook(file.realpath, data)
            fobj.write(data)
        finally:
            fobj.close()

    print('done.')
    return 0
