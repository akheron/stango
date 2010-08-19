def view_value(value):
    '''Construct a view that returns the given value when called'''
    def value_returner(context):
        return value
    return value_returner

def view_template(template_name):
    '''Construct a view that renders the given template when called'''
    def template_renderer(context, **kwargs):
        return context.render_template(template_name, **kwargs)
    return template_renderer
