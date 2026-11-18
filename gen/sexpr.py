"""Minimal S-expression reader/writer for KiCad files (stdlib only).

Nodes are Python lists; atoms are str (bare symbols) or Q (quoted strings).
"""


class Q(str):
    """A quoted string atom."""


def parse(text):
    pos = 0
    n = len(text)
    stack = [[]]
    while pos < n:
        c = text[pos]
        if c == '(':
            stack.append([])
            pos += 1
        elif c == ')':
            node = stack.pop()
            stack[-1].append(node)
            pos += 1
        elif c in ' \t\r\n':
            pos += 1
        elif c == '"':
            pos += 1
            buf = []
            while True:
                ch = text[pos]
                if ch == '\\':
                    buf.append(text[pos + 1])
                    pos += 2
                elif ch == '"':
                    pos += 1
                    break
                else:
                    buf.append(ch)
                    pos += 1
            stack[-1].append(Q(''.join(buf)))
        else:
            start = pos
            while pos < n and text[pos] not in ' \t\r\n()':
                pos += 1
            stack[-1].append(text[start:pos])
    assert len(stack) == 1
    return stack[0]


def _atom(a):
    if isinstance(a, Q):
        return '"' + a.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'
    if isinstance(a, bool):
        return 'yes' if a else 'no'
    if isinstance(a, float):
        s = ('%.4f' % a).rstrip('0').rstrip('.')
        return '0' if s in ('-0', '') else s
    return str(a)


def dump(node, indent=0):
    """Serialize a node list to KiCad-style text (one child list per line)."""
    if not isinstance(node, list):
        return _atom(node)
    simple = all(not isinstance(x, list) for x in node)
    tab = '\t' * indent
    if simple:
        return tab + '(' + ' '.join(_atom(x) for x in node) + ')'
    out = [tab + '(' + ' '.join(_atom(x) for x in node if not isinstance(x, list))]
    # keep atoms that come after lists (rare) in order
    for x in node:
        if isinstance(x, list):
            out.append(dump(x, indent + 1))
    out.append(tab + ')')
    return '\n'.join(out)


def find(node, key):
    for x in node:
        if isinstance(x, list) and x and x[0] == key:
            return x
    return None


def find_all(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]
