from VariableScopeClass import VariableScopeLocalAdvance


class Function:

    class FunctionInvalidArgumentsException:
        pass

    def __init__(self, argument_names, ast, variable_scope):
        self.argument_names, self.ast = argument_names, ast
        self.variable_scope = variable_scope

    def execute(self, arguments_values, variable_scope):
        variable_scope = self.variable_scope
        local_variables = VariableScopeLocalAdvance(variable_scope, [])

        if len(arguments_values) != len(self.argument_names):
            raise Function.FunctionInvalidArgumentsException

        for key, value in zip(self.argument_names, arguments_values):
            local_variables.admin_set_variable(key, value)

        return self.ast.execute(local_variables)


class ReturnException(Exception):
    def __init__(self, data):
        self.data = data


class FunctionAdvance:

    class NullReturnException(Exception):
        pass

    def __init__(self, argument_names, with_vars, commands, variable_scope):
        self.argument_names, self.with_vars, self.commands = argument_names, with_vars, commands
        self.variable_scope = variable_scope

    def execute(self, arguments_values, variable_scope):
        variable_scope = self.variable_scope
        local_variables = VariableScopeLocalAdvance(variable_scope, self.with_vars)

        if len(arguments_values) != len(self.argument_names):
            raise Function.FunctionInvalidArgumentsException

        for key, value in zip(self.argument_names, arguments_values):
            local_variables.admin_set_variable(key, value)

        for command in self.commands:
            command.set_scope(local_variables)

        try:
            for command in self.commands:
                command.execute()
        except ReturnException as return_value:
            return return_value.data

        #raise self.NullReturnException
        return None


class Command:
    def __init__(self, variable_scope):
        self.variable_scope = variable_scope

    def set_scope(self, new_variable_scope):
        self.variable_scope = new_variable_scope

    def execute(self):
        pass


class SetVariableCommand(Command):
    def __init__(self, variable_scope, var_name, ast):
        super().__init__(variable_scope)
        self.var_name, self.ast = var_name, ast

    def execute(self):
        self.variable_scope.set(self.var_name, self.ast.execute(self.variable_scope))


class CreateFunctionCommand(Command):
    def __init__(self, variable_scope, func_name, args, ast):
        super().__init__(variable_scope)
        self.func_name, self.args, self.ast = func_name, args, ast

    def execute(self):
        self.variable_scope.set(self.func_name,
                                Function(self.args, self.ast, self.variable_scope))


class BlockCommand(Command):
    def __init__(self, variable_scope, commands):
        super().__init__(variable_scope)
        self.commands = commands

    def set_scope(self, new_variable_scope):
        super().set_scope(new_variable_scope)
        for command in self.commands:
            command.set_scope(new_variable_scope)

    def execute_inner(self):
        for command in self.commands:
            command.execute()


class CreateAdvanceFunctionCommand(BlockCommand):
    def __init__(self, func_name, args, with_vars, variable_scope, commands):
        super().__init__(variable_scope, commands)
        self.func_name, self.args, self.with_vars = func_name, args, with_vars

    def execute(self):
        self.variable_scope.set(self.func_name,
                                FunctionAdvance(self.args, self.with_vars, self.commands, self.variable_scope))


class ReturnCommand(Command):
    def __init__(self, variable_scope, ast):
        super().__init__(variable_scope)
        self.ast = ast

    def execute(self):
        raise ReturnException(self.ast.execute(self.variable_scope))


class IfCommand(BlockCommand):
    def __init__(self, variable_scope, condition_ast, commands):
        super().__init__(variable_scope, commands)
        self.condition_ast = condition_ast
        self.next_if_command = None

    def set_scope(self, new_variable_scope):
        super().set_scope(new_variable_scope)
        if self.next_if_command:
            self.next_if_command.set_scope(new_variable_scope)

    def hook_up(self, next_if_command):
        self.next_if_command = next_if_command

    def end(self):
        if self.next_if_command is None:
            return self
        return self.next_if_command.end()

    def execute(self):
        if self.condition_ast.execute(self.variable_scope):
            self.execute_inner()
        elif self.next_if_command:
            self.next_if_command.execute()


class BreakCommand:

    class BreakException(Exception):
        pass

    def execute(self):
        raise BreakCommand.BreakException


class ContinueCommand:

    class ContinueException(Exception):
        pass

    def execute(self):
        raise ContinueCommand.ContinueException


class WhileCommand(BlockCommand):

    def __init__(self, variable_scope, condition_ast, commands):
        super().__init__(variable_scope, commands)
        self.condition_ast = condition_ast

    def execute(self):
        while self.condition_ast.execute(self.variable_scope):
            try:
                self.execute_inner()
            except ContinueCommand.ContinueException:
                continue
            except BreakCommand.BreakException:
                break


class ForCommand(BlockCommand):

    UP = 'UP'
    DOWN = 'DOWN'

    def __init__(self, variable_scope, var_name, from_ast, to_ast, commands, direction):
        super().__init__(variable_scope, commands)
        self.var_name, self.from_ast, self.to_ast = var_name, from_ast, to_ast
        self.direction = direction

    def generate_range(self, from_value, to_value):
        if self.direction == 'UP':
            return range(int(from_value), int(to_value)+1)
        return range(int(from_value), int(to_value)-1, -1)

    def execute(self):
        from_value = self.from_ast.execute(self.variable_scope)
        to_value = self.to_ast.execute(self.variable_scope)
        if from_value <= to_value and self.direction == 'UP' or from_value >= to_value and self.direction == 'DOWN':
            for iterable_value in self.generate_range(from_value, to_value):
                try:
                    self.variable_scope.set(self.var_name, iterable_value)
                    self.execute_inner()
                except ContinueCommand.ContinueException:
                    continue
                except BreakCommand.BreakException:
                    break


class ExpressionCommand(Command):
    def __init__(self, variable_scope, ast):
        super().__init__(variable_scope)
        self.ast = ast

    def execute(self):
        self.ast.execute(self.variable_scope)
