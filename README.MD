# BooleanEquation

This Python Library can be used to:
- Quickly write boolean equations
- Just solve an equation
- compare equations in lookup tables
- Generate valid variable values for variables to get a desired result

The library is best used when having all fields imported into your current context.  
It is meant to easy or check excercises you may get in university.

I made this library, initially to backtrack equations and later added capabilities that helped me verify whether my equivalent transformations worked out.

## Requirements

- Modern python 3
- The file boolean_equation from this repository

## Getting started

To start, either create a file and import the library...

```python
from boolean_equation import *

# Your code here
```

... or just use it in the python interpreter

```
$ python3 -i boolean_equation.py
>>> # Your code here
```

## How to write code

These calls generate so called Nodes, you can play with (with typical examples):

 Initialisation                   | Examples 
----------------------------------|---------------
Var('name', \[state\])            | x, y, z
Const(\<state\>)                  | 0, 1
And(\<Node\>, \<Node\>, \[...\])  | x ∧ y
Or(\<Node\>, \<Node\>, \[...\])   | x ∨ y
Not(\<Node\>)                     | ¬x
Xor(\<Node\>, \<Node\>)           | x ⊻ y
Nor(\<Node\>, \<Node\>, \[...\])  | ¬(x ∨ y)
Nand(\<Node\>, \<Node\>, \[...\]) | ¬(x ∧ y)
Implication(\<Node\>, \<Node\>)   | x → y
Equivalent(\<Node\>, \<Node\>)    | x ⇔ y

Adding nodes together and nesting them alway just creates new nodes.  
A statement is also just a Node with many nested ones.

## How to create statements

There are several ways to create statements.

You can either nest the statements, or write them in a more traditional way.

This is how you can express this eqauation:

```python
x = Var('x')
y = Var('y')
z = Var('z')
statement = (~x | ~y | ~z) & (~y | z) & (x | ((y | z) & ~z)) & (~x | y)
```

```python
x, y, z = Var('x'), Var('y'), Var('z')
statement = Or(~x, ~y, ~z) & Or(~y, z) & Or(x, And(Or(y, z), ~z)) & Or(~x, y)
```

```python
x, y, z = Var('x'), Var('y'), Var('z')
statement = And(Or(~x, ~y, ~z), Or(~y, z), Or(x, And(Or(y, z), ~z)), Or(~x, y))
```

```python
statement = And(Or(Not(Var('x')), Not(Var('y')), Not(Var('z'))), Or(Not(Var('y')), Var('z')), Or(Var('x'), And(Or(Var('y'), Var('z')), Not(Var('z')))), Or(Not(Var('x')), Var('y')))
```

```python
statement = Or('~x', '~y', '~z') & Or('~y', 'z') & Or('x', And(Or('y', 'z'), '~z')) & Or('~x', 'y')
```

When you type `print(repr(statement))` or just `statement`, you'll get the composition of all nested nodes that are needed to create this statement.  
You can just copy and paste that and it will work (as long as all fields are in the current context).

```python
And(Or(Not(Var('x')), Not(Var('y')), Not(Var('z'))), Or(Not(Var('y')), Var('z')), Or(Var('x'), And(Or(Var('y'), Var('z')), Not(Var('z')))), Or(Not(Var('x')), Var('y')))
```

When you type `print(statement)` or just `str(statement)`, you'll get a nice string representation of your statement.

```python
'((~x=? v ~y=? v ~z=?) ^ (~y=? v z=?) ^ (x=? v ((y=? v z=?) ^ ~z=?)) ^ (~x=? v y=?))'
```

You can also print a lookup table for this statement using `print_lookup_table`.
The result of the above statement would be:
```
 | x | y | z | ((~x v ~y v ~z) ^ (~y v z) ^ (x v ((y v z) ^ ~z)) ^ (~x v y))
 | 0 | 0 | 0 | 0                                                            
 | 0 | 0 | 1 | 0                                                            
 | 0 | 1 | 0 | 0                                                            
 | 0 | 1 | 1 | 0                                                            
 | 1 | 0 | 0 | 0                                                            
 | 1 | 0 | 1 | 0                                                            
 | 1 | 1 | 0 | 0                                                            
 | 1 | 1 | 1 | 0                                                             
```

You can also print more then one eqation at once as long as the variables match by name. That if often a nice way to compare, if two equations are equal.

```python
original = Or('~x', '~y', '~z') & Or('~y', 'z') & Or('x', And(Or('y', 'z'), '~z')) & Or('~x', 'y')
shortened = Or('~x', '~y', '~z') & Or('~y', 'z') & Or('x', 'y') & Or('x', '~z') & Or('~x', 'y')
print_lookup_table(shortened, original)
```

```
 | x | y | z | ((~x v ~y v ~z) ^ (~y v z) ^ (x v y) ^ (x v ~z) ^ (~x v y)) | ((~x v ~y v ~z) ^ (~y v z) ^ (x v ((y v z) ^ ~z)) ^ (~x v y))
 | 0 | 0 | 0 | 0                                                           | 0                                                             
 | 0 | 0 | 1 | 0                                                           | 0                                                             
 | 0 | 1 | 0 | 0                                                           | 0                                                             
 | 0 | 1 | 1 | 0                                                           | 0                                                             
 | 1 | 0 | 0 | 0                                                           | 0                                                             
 | 1 | 0 | 1 | 0                                                           | 0                                                             
 | 1 | 1 | 0 | 0                                                           | 0                                                             
 | 1 | 1 | 1 | 0                                                           | 0                                                             
Same results: True
```

## States

You can query the state of every node with `your_node.state()`. If it isn't certain, you'll get an `UnknownStateError`. Getting a state also doesn't mean that every variable has a state. Sometimes that might not matter to determine a statement.

With `your_node.set_state(True/False/1/0)`, you can set the current state. The most trivial one is a variable. But you can also use that on a state to change all variables result in your wished state. If this isn't possible, you'll get a `StateChangeUnableError`.  
Note that not all Variables have to get a state to get your wished result. If they are still raising an `UnknownStateError`, it simply doesn't matter.

Also keep in mind, that changing the state of a complex statement, will give you one possible solution. Not all of them.

## Notes

In Nodes (except Var and Const) you can use a string to indicate a Var and even negate it with '~'.

While strings can be used inside of statements (e.g. `And('a', '~b')`) you can't use strings directly with the supported operators `&`, `|` and `~`.  
In this case please specify your variables in advance and use those (or just `Var('x')`).

Using the *bitwise and* (`&`) or *or* (`|`) on two Nodes wraps them into an `And`-Node or 'Or'-Node.  
The *bitwise not* (`~`) wraps that into a `Not`-Node.  
More than two Nodes in an `And` or `Or` also get optimized to reduce unecessary nesting of those operators.  
Python prefers ∧ to ∨ in these cases as excpected and you can override this behaviour using brackets.

`Nand` and `Nor` are not classes (as the rest of the nodes), but functions that return the nested classes for that.

There is a function `de_morgan`. You can use it, but it's not that efficient and is probably experimental (seems to be correct though). If you want, you can implement more methods of those kind and send me a PR. I would be glade to create a collection of functions to work with those statements.