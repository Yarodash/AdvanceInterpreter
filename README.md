# AdvanceInterpreter
Simple, but not too much, python like interpreter
## How to use
Create file with source code and run script from console:

```
python AdvanceInterpreter --src=file_src
```

## Language syntax

AdvanceInterpreter is very similar to Python

### Variable assigment:
```python
a = 15
a = "test line"
a = func(10, 15)
```

### Condition blocks:
```python
if condition:
    ...
elif condition:
    ...
else:
    ...
```

### Loops:
#### While loop:
```python
while condition:
    ...
```

#### For loop:
```python
for i = 1 to 3:  # i becomes 1, 2, 3
    ...

for i = 7 downto 2:  # i becomes 7, 6, 5, 4, 3, 2
    ...
```

#### `break` command breakes current loop
#### `continue` command skips to next iteration


## Lambda functions:
```python
fn sum(a,b) => a + b
fn inc(a) => a + 1
fn factorial(x) => 1 if x < 1 else x * factorial(x - 1)
```

## Functions:
```python
def test(a, b):
    c = a + b
    return c
```

Usually functions creating variables in local scope, BUT with using `with` we can define than variable should be used in global scope
```python
def test(a) with x:
    x = a
    
x = 10
test(15)  # x becomes 15
```

### Commentary in source code
Every character after first appearing `#` defined to be commentary!
