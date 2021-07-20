class BuiltInFunction:
    arr = {}

    def __init__(self, name, func):
        self.name, self.func = name, func
        BuiltInFunction.arr[name] = self

    def execute(self, args, variable_scope):
        return self.func(*args)


INT_FUNC = BuiltInFunction('int', lambda x: int(x))
STR_FUNC = BuiltInFunction('str', lambda x: str(x))
LEN_FUNC = BuiltInFunction('len', lambda x: len(x))
SLICE = BuiltInFunction('slice', lambda string, left, right: string[left:right])
INPUT = BuiltInFunction('input', lambda prompt: input(prompt))
PRINT = BuiltInFunction('print', lambda *args: print(*args))
ORD_FUNC = BuiltInFunction('ord', lambda char: ord(char))
CHR_FUNC = BuiltInFunction('chr', lambda num: chr(num))
LIST_INIT = BuiltInFunction('list', lambda *args: list(args))
LIST_GET = BuiltInFunction('getitem', lambda arr, index: arr[index])
