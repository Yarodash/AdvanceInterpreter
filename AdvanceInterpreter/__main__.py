from expression_builder import build_ast
import re
from VariableScopeClass import VariableScope
from ASTwithCalculation import AST
from Commands import *
import argparse


class Compiled:
    def __init__(self, compiled_commands, variable_scope):
        self.compiled_commands = compiled_commands
        self.variable_scope = variable_scope

    def run(self):
        self.variable_scope.clear()
        for cmd in self.compiled_commands:
            cmd.execute()


class Compiler:

    class InvalidLineException(Exception):
        pass

    class InvalidElifException(Exception):
        pass

    def __init__(self, text):
        self.lines = list(filter(lambda x: x[1], map(self.prepare_line, text.split('\n'))))

    @staticmethod
    def replace_tabulation(line):
        return line.replace('\t', '    ')

    @staticmethod
    def remove_comment(line):
        if '#' in line:
            return line[:line.index('#')]
        return line

    @staticmethod
    def add_level(line):
        spaces = re.search(r'^(    )*', line).group()
        return len(spaces)//4, line.strip()

    def prepare_line(self, line):
        return self.add_level(self.replace_tabulation(self.remove_comment(line)))

    @staticmethod
    def find_block_end(lines, i):
        try:
            return next(j for j in range(i+1, len(lines)) if lines[j][0] <= lines[i][0])
        except StopIteration:
            return len(lines)

    def compile(self, lines=None, variable_scope=None, in_commands=False):
        variable_scope = variable_scope or VariableScope()
        lines = self.lines if lines is None else lines
        commands = []

        i = 0
        while i < len(lines):
            priority, line = lines[i]
            if match := re.match(r'^([a-zA-Z_]\w*)\s*=(.*)$', line):
                var_name, ast = match.group(1), AST(build_ast(match.group(2)))
                commands.append(SetVariableCommand(variable_scope, var_name, ast))
                i += 1

            elif match := re.match(r'^fn\s+([a-zA-Z_]\w*)\s*\((([a-zA-Z_]\w*(\s*,\s*[a-zA-Z_]\w*)*)?)\)\s*=>(.*)$', line):
                (func_name, arguments), ast = match.group(1, 2), AST(build_ast(match.group(5)))
                args = re.findall(r'[a-zA-Z_]\w*', arguments)
                commands.append(CreateFunctionCommand(variable_scope, func_name, args, ast))
                i += 1

            elif match := re.match(r'^def\s+([a-zA-Z_]\w*)\s*\(([a-zA-Z_]\w*(\s*,\s*[a-zA-Z_]\w*)*)?\)'
                                   r'\s*(\s+with\s+([a-zA-Z_]\w*(\s*,\s*[a-zA-Z_]\w*)*))?:$', line):
                func_name, arguments, with_vars = match.group(1, 2, 5)

                args = re.findall(r'[a-zA-Z_]\w*', arguments or '')
                with_vars = re.findall(r'[a-zA-Z_]\w*', with_vars or '')

                end_of_block = self.find_block_end(lines, i)
                block = self.compile(lines[i+1:end_of_block], variable_scope, True)
                commands.append(CreateAdvanceFunctionCommand(func_name, args, with_vars, variable_scope, block))
                i = end_of_block

            elif match := re.match(r'^return\s+(.*)$', line):
                ast = AST(build_ast(match.group(1)))
                commands.append(ReturnCommand(variable_scope, ast))
                i += 1

            elif match := re.match(r'^if\b(.*):$', line):
                ast = AST(build_ast(match.group(1)))
                end_of_block = self.find_block_end(lines, i)
                block = self.compile(lines[i+1:end_of_block], variable_scope, True)
                commands.append(IfCommand(variable_scope, ast, block))
                i = end_of_block

            elif match := re.match(r'^elif\b(.*):$', line):
                ast = AST(build_ast(match.group(1)))
                end_of_block = self.find_block_end(lines, i)
                block = self.compile(lines[i+1:end_of_block], variable_scope, True)
                cmd = IfCommand(variable_scope, ast, block)

                if len(commands) > 0 and isinstance(commands[-1], IfCommand):
                    commands[-1].end().hook_up(cmd)
                else:
                    raise Compiler.InvalidElifException

                i = end_of_block

            elif re.match(r'^else\s*:$', line):
                ast = AST(build_ast('1'))
                end_of_block = self.find_block_end(lines, i)
                block = self.compile(lines[i+1:end_of_block], variable_scope, True)
                cmd = IfCommand(variable_scope, ast, block)

                if len(commands) > 0 and isinstance(commands[-1], IfCommand):
                    commands[-1].end().hook_up(cmd)
                else:
                    raise Compiler.InvalidElifException

                i = end_of_block

            elif match := re.match(r'^while\b(.*):$', line):
                ast = AST(build_ast(match.group(1)))
                end_of_block = self.find_block_end(lines, i)
                block = self.compile(lines[i+1:end_of_block], variable_scope, True)
                commands.append(WhileCommand(variable_scope, ast, block))
                i = end_of_block

            elif match := re.match(r'^for\s+([a-zA-Z_]\w*)\s*=(.*)\s+(to|downto)\s+(.*):$', line):
                var_name, from_expr, direction, to_expr = match.group(1, 2, 3, 4)
                from_ast, to_ast = AST(build_ast(from_expr)), AST(build_ast(to_expr))
                direction = ForCommand.UP if direction == 'to' else ForCommand.DOWN

                end_of_block = self.find_block_end(lines, i)
                block = self.compile(lines[i+1:end_of_block], variable_scope, True)
                commands.append(ForCommand(variable_scope, var_name, from_ast, to_ast, block, direction))
                i = end_of_block

            elif re.match(r'break', line):
                commands.append(BreakCommand())
                i += 1

            elif re.match(r'continue', line):
                commands.append(ContinueCommand())
                i += 1

            else:
                commands.append(ExpressionCommand(variable_scope, AST(build_ast(line))))
                i += 1

        if in_commands:
            return commands
        return Compiled(commands, variable_scope)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--src', type=str, help='file with code to execute location', required=True)
    args = parser.parse_args()
    return args.src


def main(code_src):
    try:
        with open(code_src, 'r') as f:
            source_code = f.read()
    except FileNotFoundError:
        pass

    try:
        compiled = Compiler(source_code).compile()
        compiled.run()
    except Exception as e:
        if hasattr(e, '__repr__'):
            print(e.__repr__())
        else:
            print(e)


if __name__ == '__main__':
    main(parse_args())
