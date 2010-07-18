import os

_env = None
def render_template(template_name, **kwargs):
    from jinja2 import Environment, FileSystemLoader
    global _env

    if _env is None:
        _env = Environment(loader=FileSystemLoader('templates'))

    tmpl = _env.get_template(template_name)
    return tmpl.render(**kwargs)
