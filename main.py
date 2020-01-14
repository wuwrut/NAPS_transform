import simdjson as sj
from walker import walk_uast
import pickle


class EmbeddingTable:
    def __init__(self):
        self.lut = {'!=': 44, 'continue': 28, 'len': 36, 'clear': 96, 'array_insert': 93, '&': 74, '>': 39, 'pow': 50, '|': 95, 'floor': 92, 'func6': 102, 'str': 29, 'min': 41, 'string_split': 33, 'map_keys': 72, 'sort': 62, 'log': 68, '+': 24, 'globals': 49, 'contains': 55, 'string_find_last': 85, 'array_find': 98, '__main__': 94, 'substring': 59, 'set_remove': 79, '<=': 26, '||': 47, 'round': 66, 'set_push': 60, '<': 37, 'upper': 89, '&&': 56, 'lower': 88, 'array_remove_value': 103, 'func5': 81, 'func7': 90, '_ctor': 21, '^': 84, 'map_has_key': 69, 'map_put': 71, 'func0': 35, '>>': 83, 'copy_range': 91, 'fill': 43, 'break': 61, 'string_insert': 99, 'array_pop': 87, 'func2': 67, 'string_replace_all': 77, 'substring_end': 46, 'func1': 52, 'max': 40, '==': 53, 'array_remove_idx': 58, 'map_values': 86, 'cos': 101, '%': 51, '/': 45, 'map_get': 70, 'func3': 80, 'string': 25, 'concat': 30, 'string_find': 78, 'numer_float': 64, 'array_concat': 34, 'string_trim': 42, '=': 22, 'sqrt': 63, 'sin': 100, 'abs': 75, 'array_push': 32, 'map_remove_key': 97, 'ceil': 65, 'func4': 57, '*': 31, 'reverse': 82, '!': 48, 'number': 23, 'array_initializer': 76, '>=': 54, '<<': 73, '-': 38, 'array_index': 27}
        self.type_lut = {
            'void': 0,
            'bool': 1,
            'char': 2,
            'int': 3,
            'real': 4,
            'any': 5
        }

        self.var_lut = {
            'var0': 0,
            'var1': 1,
            'var2': 2,
            'var3': 3,
            'var4': 4,
            'var5': 5,
            'var6': 6,
            'var7': 7,
            'var8': 8,
            'var9': 9,
            'var10': 10,
            'var11': 11,
            'var12': 12,
            'var13': 13,
            'var14': 14,
            'var15': 15,
            'var16': 16,
            'var17': 17,
            'var18': 18,
            'var19': 19
        }

        self.counter = 104
        self.type_counter = 6

    def get_entry_id(self, entry):
        if entry not in self.lut:
            self.lut[entry] = self.counter
            self.counter += 1

        return self.lut[entry]

    def get_type_id(self, entry):
        if entry not in self.type_lut:
            self.type_lut[entry] = self.type_counter
            self.type_counter += 1

        return self.type_lut[entry]

    def get_var_id(self, var_name):
        return self.var_lut[var_name]

    def __str__(self):
        return str(self.type_lut)


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


def parse_ast(ast, embed_lut):
    main = find_main_func(ast['funcs'])

    args = main[3]
    vars = main[4]
    var_types = {}

    for v in args:
        var_types[v[2]] = v[1]

    for v in vars:
        var_types[v[2]] = v[1]

    preparsed = walk_uast(ast, on_tree=on_tree_cb, on_expression=on_expression_cb, on_statement=on_statement, on_block=on_block, on_func=on_func)

    # if list:
    # - first element string => function call first(*rest)
    # - else iterate over it, it is block
    # if tuple:
    # - single var name => return var
    # - 2 tuples => assign right to left


    A = []  # adjacency list
    X = {}  # node embedding number list
    Y = {}  # which nodes has labels
    walk(preparsed[-1], 0, 1, A, X, Y, embed_lut, var_types)

    return A, X, Y


def walk(node, my_num, num, A, X, Y, embed_lut, var_types):
    start = num
    op = None

    # if list, and first arg is string, eval as func
    if isinstance(node, list) and isinstance(node[0], str):
        op = node[0]
        node = node[1:]

    # __globals__
    elif len(node) == 1 and isinstance(node, tuple) and isinstance(node[0], tuple):
        X[my_num] = embed_lut.get_entry_id('globals')
        Y[my_num] = embed_lut.get_type_id('any')
        return num

    # it is number, string or variable
    if len(node) == 1 and not (isinstance(node[0], tuple) or isinstance(node[0], list)):
        if isinstance(node[0], int):
            Y[my_num] = embed_lut.get_type_id('int')
            X[my_num] = embed_lut.get_entry_id('number')

        elif isinstance(node[0], float):
            Y[my_num] = embed_lut.get_type_id('real')
            X[my_num] = embed_lut.get_entry_id('numer_float')

        else:  # string or var
            if node[0].startswith('var'):
                Y[my_num] = embed_lut.get_type_id(var_types[node[0]])
                X[my_num] = embed_lut.get_var_id(node[0])

            else:
                Y[my_num] = embed_lut.get_type_id('char*')
                X[my_num] = embed_lut.get_entry_id('string')

        return num

    # break, continue etc
    if not (isinstance(node, list) or isinstance(node, tuple)):
        X[my_num] = embed_lut.get_entry_id(node)
        return num

    # go into childs, it is some function or operator
    for i in range(len(node)):
        if len(node[i]) == 0:
            continue

        A.append([my_num, num])
        A.append([num, my_num])
        num += 1

    for i, n in enumerate(node):
        if len(n) == 0:
            continue

        num = walk(n, start + i, num, A, X, Y, embed_lut, var_types)

    X[my_num] = embed_lut.get_entry_id('=' if op is None else op)
    return num


def find_main_func(funcs):
    for f in funcs:
        if f[2] == "__main__":
            return f

    raise Exception('No main func!')


def parse_line(line, embed_lut):
    parsed = sj.ParsedJson(line.encode('utf-8'))
    ast = parsed.items('.code_tree')
    A, X, Y = parse_ast(ast, embed_lut)

    X = [X[v] for v in sorted(X)]
    return A, X, Y


def validate(a, x):
    max_node_count = len(x)
    actual_max = max(map(max, a))

    return actual_max + 1 == max_node_count

with open('naps.test.1.0.jsonl') as f:
    embed_lut = EmbeddingTable()

    As, Xs, Ys = [],[],[]

    for line in f:
        try:
            A, X, Y = parse_line(line, embed_lut)

            if validate(A, X):
                As.append(A)
                Xs.append(X)
                Ys.append(Y)

        except Exception as e:
            print("IGNORE: exception caught: {}".format(e))

    with open('dataset.pckl', 'wb') as f:
        pickle.dump((As, Xs, Ys, embed_lut.lut, embed_lut.type_lut, embed_lut.var_lut), f)

    print("done")