"""Bla."""

from rope.base.project import Project
import ast


def find_change_context(old, new):
    """Finds the smallest context of a change.

    'g(f(a, h()))', 'g(f(b, h()))' ~>
    'f(a, h())', 'f(b, h())'
    """
    if old.__class__ != new.__class__:
        return old, new

    old_children = list(ast.iter_child_nodes(old))
    new_children = list(ast.iter_child_nodes(new))

    for field in old._fields:
        old_val = getattr(old, field)
        new_val = getattr(new, field)
        if (not isinstance(old_val, (ast.AST, list)) and
            old_val != new_val):
            return old, new

    if len(old_children) != len(new_children):
        return old, new

    changed_pairs = filter(None, [
        find_change_context(old_child, new_child)
        for old_child, new_child in zip(old_children, new_children)
    ])
    if len(changed_pairs) == 0:
        return None
    elif len(changed_pairs) == 1:
        ctx = changed_pairs[0]
        # prefer Call contexts
        if isinstance(old, ast.Call) and not isinstance(ctx[0], ast.Call):
            ctx = old, new
        return ctx
    else:
        return old, new

def main():
    proj = Project('test/')
    def get_ast(mod):
        return proj.pycore.get_module(mod).get_ast()

    old, new = find_change_context(get_ast('a'), get_ast('b'))
    print(ast.dump(old))
    print(ast.dump(new))

main()
