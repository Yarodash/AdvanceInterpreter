import re
from .useful import *


class TokenType:
    arr = []

    def __init__(self, regex, name, vary=False, priority=None, right_sided=False, is_operation=False):
        self.name, self.regex, self.vary, self.right_sided = name, regex, vary, right_sided
        self.priority, self.is_operation = priority, is_operation or priority is not None
        self.compiled_regex = re.compile('^' + regex)
        TokenType.arr.append(self)

    def search(self, origin):
        if match := self.compiled_regex.search(origin):
            return match.group()

    def __repr__(self):
        return self.name


ADD_TOKEN            = TokenType(r'\+',            'ADD',            priority=9)
SUB_TOKEN            = TokenType(r'-',             'SUB',            priority=9)
POW_TOKEN            = TokenType(r'\*\*',          'POW',            priority=11, right_sided=True)
MUL_TOKEN            = TokenType(r'\*',            'MUL',            priority=10)
INT_DIV_TOKEN        = TokenType(r'\/\/',          'INT_DIV',        priority=10)
DIV_TOKEN            = TokenType(r'\/',            'DIV',            priority=10)
MOD_TOKEN            = TokenType(r'%',             'MOD',            priority=10)
BIT_AND_TOKEN        = TokenType(r'&',             'BIT_AND',        priority=7)
BIT_XOR_TOKEN        = TokenType(r'\^',            'BIT_XOR',        priority=6)
BIT_OR_TOKEN         = TokenType(r'\|',            'BIT_OR',         priority=5)
LEFT_SHIFT_TOKEN     = TokenType(r'<<',            'LEFT_SHIFT',     priority=8)
RIGHT_SHIFT_TOKEN    = TokenType(r'>>',            'RIGHT_SHIFT',    priority=8)
NOT_EQUALS_TOKEN     = TokenType(r'!=',            'NOT_EQUALS',     priority=4)
GREATER_EQUALS_TOKEN = TokenType(r'>=',            'GREATER_EQUALS', priority=4)
LESS_EQUALS_TOKEN    = TokenType(r'<=',            'LESS_EQUALS',    priority=4)
EQUALS_TOKEN         = TokenType(r'==',            'EQUALS',         priority=4)
GREATER_TOKEN        = TokenType(r'>',             'GREATER',        priority=4)
LESS_TOKEN           = TokenType(r'<',             'LESS',           priority=4)
LBAR                 = TokenType(r'\(',            'LBAR')
RBAR                 = TokenType(r'\)',            'RBAR')
NOT_TOKEN            = TokenType(r'not\b',         'NOT',            is_operation=True)
AND_TOKEN            = TokenType(r'and\b',         'AND',            priority=2)
OR_TOKEN             = TokenType(r'or\b',          'OR',             priority=1)
IF_TOKEN             = TokenType(r'if\b',          'IF')
ELSE_TOKEN           = TokenType(r'else\b',        'ELSE')
NUMBER_TOKEN         = TokenType(r'\d+(\.\d+)?\b', 'NUMBER', True)
VARIABLE_TOKEN       = TokenType(r'[a-zA-Z_]\w*',  'VARIABLE', True)
STRING_TOKEN         = TokenType(r"'.*?'",         'STRING', True)
DELIMITER_TOKEN      = TokenType(r',',             'DELIMITER')
SPACE_TOKEN          = TokenType(r'\s+', 'SPACE')


class Token:
    def __init__(self, token_type, content):
        self.token_type, self.content = token_type, content

    def __eq__(self, token_type):
        return self.token_type is token_type

    def __getattr__(self, item):
        return self.token_type.__getattribute__(item)

    def __repr__(self):
        if self.token_type.vary:
            return '{}("{}")'.format(self.token_type, self.content)
        return str(self.token_type)


class Lexer:

    BANNED_WORDS = list(map(lambda word: re.compile(rf'\b{word}\b'),
                            ('for', 'while', 'to', 'downto', 'fn', 'elif', 'with', 'def', 'return',' break')))

    class BannedWordsException(Exception):
        def __init__(self, word):
            self.word = word

        def __repr__(self):
            return 'Expression has banned word: {}'.format(self.word)

    class InvalidTokenException(Exception):
        def __init__(self, origin):
            if len(origin) >= 20:
                origin = origin[:20] + '...'
            self.error_message = f'Impossible to tokenize: {origin}'

        def __str__(self):
            return self.error_message

    def __init__(self, origin):
        self.origin = origin

    def has_banned_words(self, origin):
        for banned_word in self.BANNED_WORDS:
            if match := banned_word.search(origin):
                return match.group()

    def tokenize(self):
        tokens, origin = [], self.origin

        if banned_word := self.has_banned_words(origin):
            raise Lexer.BannedWordsException(banned_word)

        while origin:
            for token_type in TokenType.arr:
                if match := token_type.search(origin):
                    tokens.append(Token(token_type, match))
                    origin = origin[len(match):]
                    break
            else:
                raise Lexer.InvalidTokenException(origin)

        return list(filter(lambda token: token != SPACE_TOKEN, tokens))


class Parser:
    class InvalidBracketsException(Exception):
        pass

    class InvalidExpression(Exception):
        pass

    class IfStatementAbsenceException(Exception):
        pass

    class ElseStatementAbsenceException(Exception):
        pass

    class InvalidUnaryOperationException(Exception):
        pass

    def __init__(self, tokens):
        self.tokens = tokens

    def is_valid_brackets(self):
        depth = 0
        for token in self.tokens:
            depth += (token == LBAR) - (token == RBAR)
            if depth < 0:
                return False
        return depth == 0

    @staticmethod
    def build_depth_map(tokens):
        result, depth = [], 0
        for token in tokens:
            depth += (token == LBAR) - (token == RBAR)
            result.append(depth + (token == RBAR))
        return result

    @staticmethod
    def find_close_bracket(tokens, index):
        depth = 0
        for i in range(index, len(tokens)):
            depth += (tokens[i] == LBAR) - (tokens[i] == RBAR)
            if depth == 0:
                return i

    @staticmethod
    def recursive_build_ast(tokens):
        if not tokens:
            raise Parser.InvalidExpression

        if len(tokens) == 1:
            if isinstance(tokens[0], dict):
                return tokens[0]
            raise Parser.InvalidExpression

        depth_map = Parser.build_depth_map(tokens)
        combined_tokens = list(zip(range(len(tokens)), tokens, depth_map))

        # ( ... )
        if tokens[0] == LBAR and tokens[-1] == RBAR and \
                not any(depth_map[i] - (tokens[i] == RBAR) == 0 for i in range(1, len(tokens) - 1)):
            return Parser.recursive_build_ast(tokens[1:-1])

        # ... if ... else ...
        for if_index, token, depth in combined_tokens:
            if token == IF_TOKEN and depth == 0:
                for else_index, _token, _depth in combined_tokens[if_index + 1:]:
                    if _token == ELSE_TOKEN and depth == 0:
                        true_expr = Parser.recursive_build_ast(tokens[:if_index])
                        condition = Parser.recursive_build_ast(tokens[if_index + 1: else_index])
                        false_expr = Parser.recursive_build_ast(tokens[else_index + 1:])

                        return {'op': 'IF', 'condition': condition, 'true': true_expr, 'false': false_expr}

                raise Parser.ElseStatementAbsenceException

            if token == ELSE_TOKEN and depth == 0:
                raise Parser.IfStatementAbsenceException

        # not ...
        end_of_not = len(tokens)
        for i, token, depth in combined_tokens[::-1]:
            if token in (OR_TOKEN, AND_TOKEN) and depth == 0:
                end_of_not = i

            if token == NOT_TOKEN and depth == 0:
                tokens[i] = {'op': 'NOT', 'left': Parser.recursive_build_ast(tokens[i + 1: end_of_not])}
                del tokens[i + 1: end_of_not]
                del combined_tokens[i + 1: end_of_not]
                del depth_map[i + 1: end_of_not]
                return Parser.recursive_build_ast(tokens)

        # var(...)
        i = 0
        while i < len(tokens):
            if depth_map[i] == 0 and is_variable(tokens[i]) and i < len(tokens) - 1 and tokens[i + 1] == LBAR:
                close_bracket = Parser.find_close_bracket(tokens, i + 1)

                if close_bracket == i + 2:
                    arguments = []
                else:
                    arguments = map(lambda arr: list(map(lambda x: x[1], arr)),
                                    split_arr(combined_tokens[i + 2: close_bracket], (Any(), DELIMITER_TOKEN, 1)))

                del tokens[i + 1:close_bracket + 1]
                del depth_map[i + 1: close_bracket + 1]
                del combined_tokens[i + 1: close_bracket + 1]
                tokens[i] = {'op': 'CALL_FUNCTION', 'function': tokens[i],
                             'arguments': list(map(Parser.recursive_build_ast, arguments))}
            i += 1

        # calculating brackets
        i = 0
        while i < len(tokens):
            if tokens[i] == LBAR:
                close_bracket = Parser.find_close_bracket(tokens, i)
                tokens[i] = Parser.recursive_build_ast(tokens[i + 1:close_bracket])
                del tokens[i + 1:close_bracket + 1]
                del depth_map[i + 1:close_bracket + 1]
                del combined_tokens[i + 1:close_bracket + 1]
            i += 1

        # unary operations: +x, -x
        for i in range(len(tokens)-2, -1, -1):
            if tokens[i] in (ADD_TOKEN, SUB_TOKEN):
                if i == 0 or is_operation(tokens[i-1]):
                    tokens[i] = {'op': 'UNARY_PLUS' if tokens[i] == ADD_TOKEN else 'UNARY_MINUS', 'left': tokens[i+1]}
                    del tokens[i+1]
                    del depth_map[i+1]
                    del combined_tokens[i+1]

        # calculating expression without brackets
        stack, operands = [], []

        def process_op():
            operation = stack.pop()
            try:
                right = operands.pop()
                left = operands.pop()
            except IndexError:
                raise Parser.InvalidExpression
            operands.append({'op': operation.name, 'left': left, 'right': right})

        for token in tokens:
            if isinstance(token, Token):
                while stack and stack[-1].priority >= token.priority + token.right_sided:
                    process_op()

                stack.append(token)
            else:
                operands.append(token)

        while stack:
            process_op()

        if len(operands) != 1 or stack:
            raise Parser.InvalidExpression
        return operands[0]

    def build(self):
        if not self.is_valid_brackets():
            raise Parser.InvalidBracketsException

        return self.recursive_build_ast(self.tokens)


def build_ast(expression):
    def prepare_token(token):
        if token == NUMBER_TOKEN:
            return {'op': 'NUMBER', 'content': token.content}
        if token == VARIABLE_TOKEN:
            return {'op': 'VARIABLE', 'content': token.content}
        if token == STRING_TOKEN:
            return {'op': 'STRING', 'content': token.content[1:-1]}
        return token

    prepared_tokens = list(map(prepare_token, Lexer(expression).tokenize()))

    return Parser(prepared_tokens).build()
