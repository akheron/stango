import os
import sys

from stango import Stango


def quickstart():
    conf_code = '''\
from stango.files import Files
import views

index_file = 'index.html'

files = Files(
    ('', views.hello, { 'message': 'Hello, World!', 'link': 'greeting.html' }),
    ('greeting.html', views.hello, { 'message': 'Greetings, World!', 'link': 'index.html' }),
)
'''

    views_code = '''\
def hello(context, message, link):
    return context.render_template('hello.html', message=message, link=link)
'''

    hello_template = '''\
<!DOCTYPE html>
<html>
  <head>
    <title>{{ message }}</title>
    <link rel="stylesheet" type="text/css" href="hello.css">
  </head>
  <body>
    <h1>{{ message }}</h1>
    Another greeting <a href="{{ link }}">here</a>.
  </body>
</html>
'''

    hello_css = '''\
h1 { color: #0c0; }
'''

    init_files = [
        ('__init__.py', '', 0o644),
        ('conf.py', conf_code, 0o644),
        ('views.py', views_code, 0o644),
        ('static/hello.css', hello_css, 0o644),
        ('templates/hello.html', hello_template, 0o644),
    ]

    for filename, contents, mode in init_files:
        print('Creating %s' % filename)
        dirname = os.path.dirname(filename)
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname)
        fobj = open(filename, 'w')
        fobj.write(contents)
        fobj.close()
        os.chmod(filename, mode)

    print('Now run "stango runserver" or "stango generate"')
    return 0


def print_help():
        print('''\
usage: %s COMMAND [ARGS...]

Available commands:

    generate [OUTDIR]

        Generate the pages as flat files to directory OUTDIR
        (default: out). If OUTDIR doesn't exist, it is
        created, and if it already exists, it is cleared
        first.

    runserver [[HOST:]PORT]

        Start the development server on http://HOST:PORT/
        (default: http://127.0.0.1:8000/).

    quickstart

        Initialize a boilerplate example project in the
        current directory.
''' % sys.argv[0])
        sys.exit(2)


CONFIG_DEFAULTS = {
    'autoreload': [],
    'index_file': None,
    'post_render_hook': None,
}


def run():
    if len(sys.argv) < 2:
        print_help()
    if sys.argv[1] not in ['runserver', 'generate', 'quickstart']:
        print_help()

    if sys.argv[1] == 'quickstart':
        if len(sys.argv) != 2:
            print_help()
        sys.exit(quickstart())

    if not os.path.exists('conf.py'):
        print('conf.py not found', file=sys.stderr)
        sys.exit(1)

    try:
        backup = sys.path
        sys.path = [''] + sys.path
        config = {}
        exec(open('conf.py').read(), config)
    finally:
        sys.path = backup

    for k, v in list(CONFIG_DEFAULTS.items()):
        config.setdefault(k, v)

    if 'files' not in config:
        print("conf.py doesn't define the 'files' variable", file=sys.stderr)
        sys.exit(1)

    manager = Stango()
    manager.files = config['files']
    manager.index_file = config['index_file']
    manager.template_dirs.insert(0, 'templates')

    if config['post_render_hook']:
        manager.add_hook('post_render_hook', config['post_render_hook'])

    if sys.argv[1] == 'runserver':
        host = '127.0.0.1'
        port = 8000
        if len(sys.argv) == 3:
            if ':' in sys.argv[2]:
                host, port = sys.argv[2].split(':')
            else:
                port = sys.argv[2]
            try:
                port = int(port)
            except ValueError:
                print_help()
        elif len(sys.argv) > 3:
            print_help()

        def do_serve():
            print('Starting server at http://%s:%d/' % (host, port))
            httpd = manager.make_server(host, port, verbose=True)
            httpd.serve_forever()

        import stango.autoreload
        stango.autoreload.main(do_serve, config['autoreload'])

    elif sys.argv[1] == 'generate':
        if len(sys.argv) == 2:
            outdir = 'out'
        elif len(sys.argv) == 3:
            outdir = sys.argv[2]
        else:
            print_help()

        print('Generating to %s...' % outdir)
        sys.exit(manager.generate(outdir) or 0)

    else:
        print_help()
