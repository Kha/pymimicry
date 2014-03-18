"""Bla."""

import collections

from rope.base.project import Project
import ast

def all_equal(values):
    return len(set(values)) == 1

def union(sets):
    return {value
            for set_ in sets
            for value in set_}

def transpose(lists):
    """
    >>> transpose([[1, 2], [3, 4]])
    [(1, 3), (2, 4)]
    """
    return zip(*lists)

def windows(values, n=2):
    """
    >>> list(windows([1, 2, 3, 4]))
    [[1, 2], [2, 3], [3, 4]]
    """
    window = values[:n]
    values = values[n:]
    yield window
    while values:
        window = window[1:] + [values[0]]
        values = values[1:]
        yield window

def wrap(value):
    if isinstance(value, ast.AST) and not isinstance(value, ASTWrapper):
        return ASTWrapper(value)
    elif isinstance(value, list):
        return map(wrap, value)
    else:
        return value

class ASTWrapper(ast.AST):
    """ast.AST wrapper for more Pythonicity."""
    def __init__(self, node):
        object.__setattr__(self, '_node', node)
        self._fields = self._node._fields

    def __getattr__(self, name):
        value = getattr(self._node, name)
        setattr(self, name, value)
        return getattr(self, name)

    def __setattr__(self, name, value):
        object.__setattr__(self, name, wrap(value))

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return equal_node_structure([self, other]) and \
                all(n1 == n2 for n1, n2 in
                    zip(self.child_nodes, other.child_nodes))

    def __repr__(self):
        # shamelessly copied from ast.dump
        def _format(node):
            if isinstance(node, AST):
                fields = [(a, _format(b)) for a, b in ast.iter_fields(node)]
                return '%s(%s)' % (node.type.__name__, ', '.join(
                    ('%s=%s' % field for field in fields)
                ))
            elif isinstance(node, list):
                return '[%s]' % ', '.join(_format(x) for x in node)
            return repr(node)
        return _format(self)

    @property
    def child_nodes(self):
        return list(ast.iter_child_nodes(self))

    @property
    def type(self):
        return type(self._node)

    def of_class(self, class_):
        return self.type == class_

AST = ASTWrapper

def parse(source):
    return ASTWrapper(ast.parse(source))

def parse_expr(source):
    return parse(source).body[0].value

def parse_exprs(*sources):
    return [parse_expr(source) for source in sources]

def equal_node_structure(nodes):
    """Returns True iff all given nodes have the same structure.
    The structure of a node is its type, the values of its non-node attributes
    and the lengths of its node-list attributes, i.e. node equality minus
    equality of child nodes.

    >>> equal_node_structure(parse_exprs('f(a)', 'g(b)'))
    True
    >>> equal_node_structure(parse_exprs('f(a)', 'g(b, c)'))
    False
    """
    def equal(n1, n2):
        if n1.type != n2.type:
            return False

        for field in n1._fields:
            n1_val = getattr(n1, field)
            n2_val = getattr(n2, field)
            if isinstance(n1_val, list):
                if len(n1_val) != len(n2_val):
                    return False
            elif not isinstance(n1_val, AST):
                if n1_val != n2_val:
                    return False

        return True

    nodes = list(nodes)
    return len(nodes) < 2 or all(equal(nodes[0], n) for n in nodes[1:])

def find_change_context(old, new):
    """Finds the smallest context of a change.

    'g(f(a, h()))', 'g(f(b, h()))' ~>
    'f(a, h())', 'f(b, h())'
    """
    if not equal_node_structure([old, new]):
        return old, new

    changed_pairs = filter(None, [
        find_change_context(old_child, new_child)
        for old_child, new_child in zip(old.child_nodes, new.child_nodes)
    ])
    if len(changed_pairs) == 0:
        return None
    elif len(changed_pairs) == 1:
        ctx = changed_pairs[0]
        # prefer Call contexts
        if old.of_class(ast.Call) and not ctx[0].of_class(ast.Call):
            ctx = old, new
        return ctx
    else:
        return old, new

class Template(collections.namedtuple('Template', ['node', 'holes'])):
    """A node where specific sub-nodes, the 'holes', are marked as
    substituteable.
    >>> n = parse_expr('f(a, g())')
    >>> Template(n, [n.args[1]])
    Call(func=Name(id='f', ctx=Load()), args=[Name(id='a', ctx=Load()), Name(id='$0', ctx=None)], keywords=[], starargs=None, kwargs=None)
    """
    def __repr__(self):
        return repr(self.instantiate({
            hole: ast.Name('$%d' % i, None) for i, hole in enumerate(self.holes)
        }))

    def instantiate(self, replacement):
        """Replaces the template's holes with values in the given dict."""
        assert len(replacement) == len(self.holes)
        holes = self.holes

        class Transformer(ast.NodeTransformer):
            def visit(self, node):
                if node in holes:
                    return wrap(replacement[node])
                else:
                    return self.generic_visit(node)

        return Transformer().visit(self.node)

def get_most_specific_template(nodes):
    """Gets the most specific template instantiable to all given nodes.

    A template t1 is more specific than a template t2 iff t2 can be
    instantiated to t1 (plus the right set of holes).

    >>> get_most_specific_template(parse_exprs('f(a, b+1)', 'f(a, g())'))
    Call(func=Name(id='f', ctx=Load()), args=[Name(id='a', ctx=Load()), Name(id='$0', ctx=None)], keywords=[], starargs=None, kwargs=None)
    """
    assert len(nodes) > 1

    def get_holes(nodes):
        node = nodes[0]

        if not equal_node_structure(nodes):
            return {node}

        return union(map(get_holes, transpose([n.child_nodes for n in nodes])))

    return Template(nodes[0], get_holes(nodes))

def main():
    proj = Project('test/')
    def get_ast(mod):
        return wrap(proj.pycore.get_module(mod).get_ast())

    edit_steps = ['a', 'b', 'c']
    contexts = [find_change_context(*win) for win in windows(map(get_ast, edit_steps))]
    old_template, new_template = map(get_most_specific_template, transpose(contexts))
    print(old_template)
    print(new_template)


if __name__ == '__main__':
    main()
