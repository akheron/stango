import os

def render_template(template_name, **kwargs):
    from jinja2 import Environment, FileSystemLoader

    env = Environment(loader=FileSystemLoader('templates'))
    tmpl = env.get_template(template_name)

    return tmpl.render(**kwargs)
