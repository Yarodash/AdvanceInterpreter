class AST:

    class InvalidAstOperationException(Exception):
        def __init__(self, operation):
            self.operation = operation

        def __repr__(self):
            return 'Invalid operation in ast: {}'.format(self.operation)

    binary_operations = {'ADD':            lambda x, y: x + y,
                         'SUB':            lambda x, y: x - y,
                         'MUL':            lambda x, y: x * y,
                         'INT_DIV':        lambda x, y: x // y,
                         'DIV':            lambda x, y: x / y,
                         'MOD':            lambda x, y: x % y,
                         'POW':            lambda x, y: x ** y,
                         'LEFT_SHIFT':     lambda x, y: x << y,
                         'RIGHT_SHIFT':    lambda x, y: x >> y,
                         'BIT_AND':        lambda x, y: x & y,
                         'BIT_XOR':        lambda x, y: x ^ y,
                         'BIT_OR':         lambda x, y: x | y,
                         'EQUALS':         lambda x, y: int(x == y),
                         'NOT_EQUALS':     lambda x, y: int(x != y),
                         'LESS':           lambda x, y: int(x < y),
                         'LESS_EQUALS':    lambda x, y: int(x <= y),
                         'GREATER':        lambda x, y: int(x > y),
                         'GREATER_EQUALS': lambda x, y: int(x >= y)}

    unary_operations = {'UNARY_PLUS':      lambda x: x,
                        'UNARY_MINUS':     lambda x: -x,
                        'NOT':             lambda x: not x}

    def __init__(self, ast):
        self.ast = ast

    @staticmethod
    def recursive(ast, variables):
        if ast['op'] == 'NUMBER':
            if '.' in ast['content']:
                return float(ast['content'])
            return int(ast['content'])

        if ast['op'] == 'VARIABLE':
            return variables.get(ast['content'])

        if ast['op'] == 'STRING':
            return ast['content']

        if ast['op'] == 'IF':
            if AST.recursive(ast['condition'], variables):
                return AST.recursive(ast['true'], variables)
            return AST.recursive(ast['false'], variables)

        if ast['op'] == 'CALL_FUNCTION':
            function = ast['function']['content']
            arguments = [AST.recursive(sub_ast, variables) for sub_ast in ast['arguments']]
            return variables.get(function).execute(arguments, variables)
        
        left = AST.recursive(ast['left'], variables)

        if ast['op'] == 'AND':
            if left:
                return AST.recursive(ast['right'], variables)
            return left

        if ast['op'] == 'OR':
            if left:
                return left
            return AST.recursive(ast['right'], variables)

        if ast['op'] in AST.unary_operations:
            return AST.unary_operations[ast['op']](left)

        if ast['op'] in AST.binary_operations:
            right = AST.recursive(ast['right'], variables)
            return AST.binary_operations[ast['op']](left, right)

        raise AST.InvalidAstOperationException(ast['op'])

    def execute(self, variables):
        return self.recursive(self.ast, variables)
