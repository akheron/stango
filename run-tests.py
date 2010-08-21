import sys
from optparse import OptionParser

try:
    from coverage import coverage
except ImportError:
    coverage = None

parser = OptionParser()
parser.add_option('-v', '--verbose', action='store_true',
                  help='Be more verbose')
if coverage:
    parser.add_option('-c', '--coverage', action='store_true',
                      help='Measure code coverage')

options, args = parser.parse_args()
if args:
    parser.print_help()
    sys.exit(2)

if coverage and options.coverage:
    cov = coverage()
    cov.start()

# Import the Stango code down here to make coverage count the importing, too
import tests
result = tests.run(options.verbose)

if result.wasSuccessful() and options.coverage:
    exclude = [
        'stango.tests',
        'stango.autoreload',
    ]

    def include_module(name):
        # exclude test code and stango.autoreload which is not testable
        for prefix in ['stango.tests', 'stango.autoreload']:
            if name.startswith(prefix):
                return False
        return name.startswith('stango')

    cov.stop()
    modules = [
        module for name, module in sys.modules.items()
        if include_module(name)
    ]
    cov.report(modules, file=sys.stdout)
    cov.erase()
