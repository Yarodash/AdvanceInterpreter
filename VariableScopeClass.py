from my_builtins import BuiltInFunction


class VariableScope:

    class VariableNameAlreadyUsed(Exception):
        def __init__(self, var_name, is_func=False):
            self.var_name, self.is_func = var_name, is_func

        def __repr__(self):
            return 'Name {} already used for {}'.format(self.var_name, 'function' if self.is_func else 'variable')

    class UndefinedVariable(Exception):
        def __init__(self, var_name):
            self.var_name = var_name

        def __repr__(self):
            return 'Undefined variable {}'.format(self.var_name)

    class UndefinedFunction(Exception):
        def __init__(self, var_name):
            self.var_name = var_name

        def __repr__(self):
            return 'Undefined function {}'.format(self.var_name)

    def __init__(self):
        self.vars = {}

    def clear(self):
        self.vars = {}

    def set(self, name, value):
        self.vars[name] = value

    def get(self, name):
        if name not in self.vars:
            if name in BuiltInFunction.arr:
                return BuiltInFunction.arr[name]
            raise self.UndefinedVariable(name)
        return self.vars[name]

    def __repr__(self):
        return 'Variable Scope:\n | Vars: {}'.format(self.vars)


class VariableScopeLocalAdvance:
    def __init__(self, global_variables, with_variables):
        self.global_variables, self.with_variables = global_variables, with_variables
        self.vars = {}

    def admin_set_variable(self, key, value):
        self.vars[key] = value

    def set(self, name, value):
        if name in self.with_variables:
            self.global_variables.set(name, value)
        self.vars[name] = value

    def get(self, name):
        if name in self.vars:
            return self.vars[name]
        return self.global_variables.get(name)

