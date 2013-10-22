def dict_merge(*args):
    result = {}
    for d in args:
        result.update(d)
    return result


class Context(object):
    def __init__(self, manager, mode, filespec):
        self.manager = manager
        self.mode = mode
        self.path = filespec.path
        self.realpath = filespec.realpath(manager.index_file)
        self.jinja_env = manager.jinja_env

    def render_template(self, template_name, **kwargs):
        builtin_template_args = {
            'generating': self.mode == 'generating',
            'serving': self.mode == 'serving',
            'path': self.path,
            'realpath': self.realpath,
        }

        template = self.jinja_env.get_template(template_name)
        return template.render(dict_merge(builtin_template_args, kwargs))
