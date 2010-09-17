from http.server import HTTPServer, BaseHTTPRequestHandler
import mimetypes
import os

class StangoRequestHandler(BaseHTTPRequestHandler):
    def start_response(self, code, headers={}):
        if code == 200:
            self.send_response(200)
            for header, value in headers.items():
                self.send_header(header, value)
            self.end_headers()
        else:
            self.send_response(code)

    def do_GET(self):
        manager = self.server.manager

        # remove the leading /
        realpath = path = self.path[1:]

        if manager.index_file and (not path or path.endswith('/')):
            realpath = os.path.join(path, manager.index_file)

        headers = {}
        content_type, content_encoding = mimetypes.guess_type(realpath)
        if content_type:
            headers['Content-Type'] = content_type
        if content_encoding:
            headers['Content-Encoding'] = content_encoding

        for filespec in manager.files:
            if filespec.realpath(manager.index_file) == realpath:
                self.start_response(200, headers)
                self.wfile.write(manager.view(filespec, mode='serving'))
                break
        else:
            self.start_response(404)

    def log_message(self, *args, **kwargs):
        if self.server.verbose:
            super(StangoRequestHandler, self).log_message(*args, **kwargs)


class StangoHTTPServer(HTTPServer):
    def __init__(self, server_address, manager):
        self.manager = manager
        HTTPServer.__init__(self, server_address, StangoRequestHandler)
