import re


_underscorer1 = re.compile(r'(.)([A-Z][a-z]+)')
_underscorer2 = re.compile('([a-z0-9])([A-Z])')


def camel_to_snake(s):
    # https://gist.github.com/jaytaylor/3660565
    subbed = _underscorer1.sub(r'\1_\2', s)
    return _underscorer2.sub(r'\1_\2', subbed).lower()


def snake_to_camel(s):
    words = s.split('_')
    return "".join(r.title() for r in words)


def save_items(items, db):
    map(lambda x: db.session.add(x), items)
    db.session.commit()
