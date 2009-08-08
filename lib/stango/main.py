import os
import sys
import stango.manage

def quickstart():
    conf_code = '''\
import stango
import views

index_file = 'index.html'

files = stango.files(
    ('', views.hello, { 'message': 'Hello, World!', 'link': 'greeting.html' }),
    ('greeting.html', views.hello, { 'message': 'Greetings, World!', 'link': 'index.html' }),
)
'''

    views_code = '''\
from stango.shortcuts import render_template

def hello(message, link):
    return render_template('hello.html', message=message, link=link)
'''

    hello_template = '''\
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
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
        ('__init__.py', '', 0644),
        ('conf.py', conf_code, 0644),
        ('views.py', views_code, 0644),
        ('static/hello.css', hello_css, 0644),
        ('templates/hello.html', hello_template, 0644),
    ]

    for filename, contents, mode in init_files:
        print 'Creating %s' % filename
        dirname = os.path.dirname(filename)
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname)
        fobj = open(filename, 'w')
        fobj.write(contents)
        fobj.close()
        os.chmod(filename, mode)

    print 'Now run "stango serve" or "stango render"'
    return 0


def print_help():
        print '''\
usage: %s COMMAND [ARGS...]

Available commands:

    render [OUTDIR]

        Render the pages as flat files to directory OUTDIR
        (default: out). If OUTDIR doesn't exist, it is
        created, and if it already exists, it is cleared
        first.

    serve [[HOST:]PORT]

        Serve the pages on http://HOST:PORT/ (default:
        127.0.0.1:8000).

    quickstart

        Initialize a boilerplate example project in the
        current directory.
''' % sys.argv[0]
        sys.exit(2)


CONFIG_DEFAULTS = {
    'index_file': None,
}

def run():
    if (len(sys.argv) < 2 or
        sys.argv[1] not in ['serve', 'render', 'quickstart']):
        print_help()

    if sys.argv[1] == 'quickstart':
        if len(sys.argv) != 2:
            print_help()
        sys.exit(quickstart())

    if not os.path.exists('conf.py'):
        print >>sys.stderr, 'conf.py not found'
        sys.exit(1)

    try:
        backup = sys.path
        sys.path = [''] + sys.path
        config = {}
        execfile('conf.py', config)
    finally:
        sys.path = backup

    for k, v in CONFIG_DEFAULTS.items():
        config.setdefault(k, v)

    if not 'files' in config:
        print >>sys.stderr, "'files.py' doesn't define the 'files' variable"
        sys.exit(1)

    if config['index_file']:
        for file in config['files']:
            file.complete(config['index_file'])

    if sys.argv[1] == 'serve':
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

        sys.exit(stango.manage.serve(config, host, port))

    elif sys.argv[1] == 'render':
        if len(sys.argv) == 2:
            outdir = 'out'
        elif len(sys.argv) == 3:
            outdir = sys.argv[2]
        else:
            print_help()

        sys.exit(stango.manage.render(config, outdir))

    else:
        print_usage()
