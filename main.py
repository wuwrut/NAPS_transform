import simdjson as sj
from walker import walk_uast

KEYWORDS = {
    'if': 0,
    'foreach': 1,
    'while': 2,
    'break': 3,
    'continue': 4,
    'return': 5,
    'noop': 6,
    'assign': 7,
    'field': 8,
    'val': 9,
    'invoke': 10,
    '?:': 11,
    'cast': 12,
    'var': 13
}


def on_tree_cb(tree, structs, funcs):
    return funcs


def on_expression_cb(expression, is_lhs, res):

    return res


def on_statement(statement, res):
    return res


def on_block(block, res):
    return res


def on_func(kind, return_type, func_name, args, variables, body, res):
    return res


def parse_ast(ast):
    main = find_main_func(ast['funcs'])

    args = main[3]
    vars = main[4]
    y = []

    for v in args:
        y.append(v[1])

    for v in vars:
        y.append(v[1])

    preparsed = walk_uast(ast, on_tree=on_tree_cb, on_expression=on_expression_cb, on_statement=on_statement, on_block=on_block, on_func=on_func)

    # if list:
    # - first element string => function call first(*rest)
    # - else iterate over it, it is block
    # if tuple:
    # - single var name => return var
    # - 2 tuples => assign right to left
    X = []
    walk(preparsed[0], 0, 1, X)

    return X

def walk(node, my_num, num, X):
    start = num

    #if list, and first arg is string, eval as func

    if len(node) == 1 and not (isinstance(node[0], tuple) or isinstance(node[0], list)):
        return num

    if isinstance(node, list) and isinstance(node[0], str):
        node = node[1:]

    if not (isinstance(node, list) or isinstance(node, tuple)):
        return num

    for _ in range(len(node)):
        X.append([my_num, num])
        X.append([num, my_num])
        num += 1

    for i, n in enumerate(node):
        if len(n) == 0:
            continue

        num = walk(n, start+i, num, X)

    return num


def find_main_func(funcs):
    for f in funcs:
        if f[2] == "__main__":
            return f

    raise Exception('No main func!')


def parse_line(line):
    parsed = sj.ParsedJson(line.encode('utf-8'))
    ast = parsed.items('.code_tree')
    return parse_ast(ast)


with open('naps.test.1.0.jsonl') as f:
    for line in f:
        print(parse_line(line))

    print("done")