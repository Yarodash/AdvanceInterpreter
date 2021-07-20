def split_arr(arr, sep):
    parts, left = [], 0
    while True:
        try:
            right = arr.index(sep, left)
        except ValueError:
            return parts + [arr[left:]]
        parts.append(arr[left: right])
        left = right + 1


class Any:
    def __eq__(self, other):
        return True


class ASTtoString:

    class InvalidAstException(Exception):
        pass

    operations = {'ADD': '+', 'SUB': '-', 'MUL': '*', 'DIV': '/', 'MOD': '%', 'POW': '**',
                  'BIT_AND': '&', 'BIT_XOR': '^', 'BIT_OR': '|', 'LEFT_SHIFT': '<<', 'RIGHT_SHIFT': '>>',
                  'EQUALS': '==', 'NOT_EQUALS': '!=', 'GREATER': '>', 'LESS': '<', 'GREATER_EQUALS': '>=',
                  'LESS_EQUALS': '<=', 'AND': 'and', 'OR': 'or', 'ASSIGN': ':='}

    def __init__(self, ast):
        self.ast = ast

    def convert(self, ast=None):
        if ast is None:
            ast = self.ast

        if ast['op'] == 'CALL_FUNCTION':
            return '{}({})'.format(ast['function']['content'],
                                   ', '.join(self.convert(sub_ast) for sub_ast in ast['arguments']))

        if ast['op'] in ('NUMBER', 'VARIABLE'):
            return ast['content']

        if ast['op'] in self.operations:
            return '({} {} {})'.format(self.convert(ast['left']), self.operations[ast['op']], self.convert(ast['right']))

        if ast['op'] == 'NOT':
            return '(not {})'.format(self.convert(ast['left']))

        if ast['op'] == 'IF':
            return '({} if {} else {})'.format(*list(map(self.convert, (ast['true'], ast['condition'], ast['false']))))

        raise ASTtoString.InvalidAstException


def is_variable(token):
    return isinstance(token, dict) and token['op'] == 'VARIABLE'


def is_number(token):
    return isinstance(token, dict) and token['op'] == 'NUMBER'


def is_operation(token):
    return not isinstance(token, dict)
