#!/usr/bin/env python3

from abc import ABC, abstractmethod


class LogicError(Exception):
    pass


class UnknownStateError(LogicError):
    pass


class StateChangeUnableError(LogicError):
    pass


class InvalidOperandError(LogicError):
    pass


def parse(operand) -> 'Node':
    '''Parse to actual Node'''
    if isinstance(operand, int) or isinstance(operand, bool):
        return Const(operand)
    elif isinstance(operand, str):
        while operand.startswith('~~'):
            operand = operand[2:]
        if operand.startswith('~'):
            return Not(Var(operand[1:]))
        else:
            return Var(operand)
    elif isinstance(operand, Node):
        return operand
    else:
        return InvalidOperandError("The following operand isn't based on Node and can't be changed to Const(): %s" % repr(operand))


def _operandGenerator(operands):
    '''
    Generate guaranteed list of operands based on Node.
    Attempts to parse other types or raises InvalidOperandError!
    '''
    for operand in operands:
        yield parse(operand)


def isUnknown(node):
    try:
        node.state()
        return False
    except UnknownStateError:
        return True


class Node(ABC):
    def __init__(self):
        # Other Nodes that this class contains/depends upon
        self.operands = []

    @abstractmethod
    def state(self) -> bool:
        pass
    
    @abstractmethod
    def set_state(self, newState: bool):
        pass
    
    def __bool__(self) -> bool:
        return bool(self.state())
    
    def __or__(self, other) -> 'Node':
        # Would work without this assert, but allow dumb operator pairs like in JS
        assert isinstance(other, Node)

        if isinstance(self, Or) and isinstance(other, Or):
            return Or(*self.operands, *other.operands)
        elif isinstance(self, Or):
            return Or(*self.operands, other)
        elif isinstance(other, Or):
            return Or(self, *other.operands)
        else:
            return Or(self, other)
    
    def __and__(self, other) -> 'Node':
        # Would work without this assert, but allow dumb operator pairs like in JS
        assert isinstance(other, Node)
        
        if isinstance(self, And) and isinstance(other, And):
            return And(*self.operands, *other.operands)
        elif isinstance(self, And):
            return And(*self.operands, other)
        elif isinstance(other, And):
            return And(self, *other.operands)
        else:
            return And(self, other)
    
    def __invert__(self) -> 'Node':
        return Not(self)


class Var(Node):
    def __init__(self, name: str, state=None):
        '''
        state=None: Unknown value which prevents equation
                    from getting solved.
        '''
        Node.__init__(self)
        assert('"' not in name)
        assert('"' not in name)
        assert(' ' not in name)
        assert('\t' not in name)
        assert('=' not in name)
        self.name = name
        if state is None:
            self._state = None
        else:
            self._state = bool(state)

    def state(self) -> bool:
        if self._state is None:
            raise UnknownStateError("Variable '%s' isn't known, which prevents solving the equation!" % self.name)
        return bool(self._state)
    
    def set_state(self, newState: bool):
        self._state = newState
    
    def __repr__(self):
        if self._state is None:
            return "Var('%s')" % self.name
        else:
            return "Var('%s', %s)" % (self.name, bool(self.state()))
    
    def __str__(self):
        if self._state is None:
            return '%s=?' % self.name
        else:
            return '%s=%s' % (self.name, int(self.state()))


class Const(Node):
    def __init__(self, state: bool):
        Node.__init__(self)
        if state is None:
            raise InvalidOperandError('Const has to be termined!')
        self._state = bool(state)

    def state(self) -> bool:
        return self._state
    
    def set_state(self, newState: bool):
        if newState != self._state:
            raise StateChangeUnableError("Can't change value of constant!!!")
    
    def __repr__(self):
        return "Const(%s)" % bool(self.state())
    
    def __str__(self):
        return str(int(self.state()))


class And(Node):
    def __init__(self, *operands):
        Node.__init__(self)
        if len(operands) == 0:
            raise InvalidOperandError('Or needs to have at least one operand. None given')
        self.operands = list(_operandGenerator(operands))
    
    def state(self) -> bool:
        totalCount, trueCount, unknownCount = 0, 0, 0
        for operand in self.operands:
            totalCount += 1
            try:
                if operand.state():
                    trueCount += 1
                else:
                    return False
            except UnknownStateError:
                unknownCount += 1
        
        if trueCount == totalCount:
            return True
        if unknownCount > 0:
            raise UnknownStateError("Can't determine state of AND-Equation: %s" % repr(self))
    
    def set_state(self, newState: bool):
        # Ignore if state is already guarenteed to be the target one
        try:
            if self.state() == newState:
                return
        except UnknownStateError:
            pass
        
        if newState:
            # Goal: All operands have to be true to guarantee being true
            for operand in self.operands:
                operand.set_state(True)
        else:
            # Goal: Any value has to be false to guarantiee beeing false
            for operand in self.operands:
                try:
                    operand.set_state(False)
                    return
                except StateChangeUnableError:
                    pass
            
            # At this point no state could be set to false
            raise StateChangeUnableError("Can't get this AND-Equation to equal False: %s" % repr(self))
    
    def __repr__(self):
        return 'And(%s)' % ', '.join(map(lambda op: repr(op), self.operands))
    
    def __str__(self):
        return '(' + ' ^ '.join(map(lambda op: str(op), self.operands)) + ')'


class Or(Node):
    def __init__(self, *operands):
        '''
        All that matters is that there is ANY value that is True.
        Unknown values don't matter in that case.
        '''
        Node.__init__(self)
        if len(operands) == 0:
            raise InvalidOperandError('Or needs to have at least one operand. None given')
        self.operands = list(_operandGenerator(operands))

    def state(self) -> bool:
        totalCount, unknownCount, falseCount = 0, 0, 0
        for operand in self.operands:
            totalCount += 1
            try:
                if operand.state():
                    return True
                else:
                    falseCount += 1
            except UnknownStateError:
                unknownCount += 1
        
        if totalCount == (unknownCount + falseCount) and unknownCount > 0:
            raise UnknownStateError("Can't determine state of OR-Equation with no guarnteed outcome: %s" % repr(self))
        else:
            return False
    
    def set_state(self, newState: bool):
        # Ignore if state is already guarenteed to be the target one
        try:
            if self.state() == newState:
                return
        except UnknownStateError:
            pass
        
        if newState:
            # Goal: Make this equation return true (at least one value true to guarantee that)

            # Set next possible (changeable) state to true
            for operand in self.operands:
                try:
                    operand.set_state(True)
                    return
                except StateChangeUnableError:
                    pass
                break
            
            # Failed to change result of OR-Equation:
            raise StateChangeUnableError("Can't get this OR-Statement to equal True: %s" % repr(self))
        else:
            # Goal: Make this equation return false (all values false to guarantee that)

            # Try to make all known values false:
            for operand in self.operands:
                operand.set_state(False)    

    def __repr__(self):
        return 'Or(%s)' % ', '.join(map(lambda op: repr(op), self.operands))
    
    def __str__(self):
        return '(' + ' v '.join(map(lambda op: str(op), self.operands)) + ')'

class Not(Node):

    def __init__(self, operand):
        self.operands = [ next(_operandGenerator((operand,))) ]
    
    def state(self) -> bool:
        return not self.operands[0].state()
    
    def set_state(self, newState: bool):
        try:
            if self.state() == newState:
                return
        except UnknownStateError:
            pass
        
        self.operands[0].set_state(not newState)
    
    def __repr__(self):
        return 'Not(%s)' % repr(self.operands[0])
    
    def __str__(self):
        operand = self.operands[0]
        if isinstance(operand, And) or isinstance(operand, Or) or isinstance(operand, Xor) \
            or isinstance(operand, Not) or isinstance(operand, Var) or isinstance(operand, Const):
            return '~%s' % operand
        else:
            return '~(%s)' % operand


class Xor(Node):
    def __init__(self, *operands):
        '''
        Excately two operators. One has to be true and one false.
        No excuses!
        '''
        Node.__init__(self)
        if len(operands) != 2:
            raise InvalidOperandError('Xor needs to have EXCATCLY two operands. Given: %s' % repr(operands))
        self.operands = list(_operandGenerator(operands))

    def state(self) -> bool:
        return self.operands[0].state() != self.operands[1].state()
    
    def set_state(self, newState: bool):
        # Ignore if state is already guarenteed to be the target one
        try:
            if self.state() == newState:
                return
        except UnknownStateError:
            pass
        
        if newState:
            for operands in [ self.operands, self.operands[::-1] ]:
                try:
                    op1, op2 = operands
                    op1.set_state(not op2.state())
                    return
                except (StateChangeUnableError, UnknownStateError):
                    pass
            
            op1, op2 = self.operands
            if isUnknown(op1) and isUnknown(op2):
                for val in [ False, True ]:
                    try:
                        op1.set_state(val)
                        op2.set_state(not val)
                        return
                    except StateChangeUnableError:
                        pass
                    
            raise StateChangeUnableError("Can't make XOR-Equation to equal True: %s" % repr(self))
        else:
            for operands in [ self.operands, self.operands[::-1] ]:
                try:
                    op1, op2 = operands
                    op1.set_state(op2.state())
                    return
                except (StateChangeUnableError, UnknownStateError):
                    pass
                
            op1, op2 = self.operands
            if isUnknown(op1) and isUnknown(op2):
                for val in [ False, True ]:
                    try:
                        op1.set_state(val)
                        op2.set_state(val)
                        return
                    except StateChangeUnableError:
                        pass
            
            raise StateChangeUnableError("Can't make XOR-Equation to equal False: %s" % repr(self))


    def __repr__(self):
        return 'Xor(%s)' % ', '.join(map(lambda op: repr(op), self.operands))
    
    def __str__(self):
        return '(' + ' xor '.join(map(lambda op: str(op), self.operands)) + ')'


class Implication(Node):
    def __init__(self, a, b):
        Node.__init__(self)
        parsedA, parsedB = parse(a), parse(b)
        self.operands = [parsedA, parsedB]
        self.base = Or(Not(parsedA), parsedB)
    
    def state(self):
        return self.base.state()
    
    def set_state(self, new_state):
        return self.base.set_state(new_state)

    def __repr__(self):
        return 'Implication(%s, %s)' % (repr(self.operands[0]), repr(self.operands[1]))
    
    def __str__(self):
        return '%s \u2192 %s' % (str(self.operands[0]), str(self.operands[1]))


class Equivalent(Node):
    def __init__(self, a, b):
        Node.__init__(self)
        parsedA, parsedB = parse(a), parse(b)
        self.operands = [parsedA, parsedB]
        self.base = And(Implication(parsedA, parsedB), Implication(parsedB, parsedA))
    
    def state(self):
        return self.base.state()
    
    def set_state(self, new_state):
        return self.base.set_state(new_state)

    def __repr__(self):
        return 'Equivalent(%s, %s)' % (repr(self.operands[0]), repr(self.operands[1]))
    
    def __str__(self):
        return '%s \u2194 %s' % (str(self.operands[0]), str(self.operands[1]))


def Nor(*operands):
    return Not(Or(*operands))


def Nand(*operands):
    return Not(And(*operands))


def find_variables(operand):
    operands = [ operand ]
    while len(operands) > 0:
        operand = operands.pop()
        if isinstance(operand, Var):
            yield operand
        else:
            for suboperand in operand.operands:
                operands.append(suboperand)


def find_variable_state(operand, variable_name):
    state = None
    count = 0
    for variable in find_variables(operand):
        if variable.name != variable_name:
            continue

        count += 1
        if variable.state() is not state and state is not None:
            raise LogicError('The variable %s does not always has the same state!' % repr(variable_name))
        else:
            state = variable.state()
    
    if count == 0:  
        raise LogicError('Variable %s could not be found.' % repr(variable_name))
    return state


def find_variable_state_or_default(operand, variable_name, default=None):
    try:
        return find_variable_state(operand, variable_name)
    except UnknownStateError:
        return default


def set_variable_state(operand, variable_name, new_state):
    for variable in find_variables(operand):
        if variable.name != variable_name:
            continue
        variable.set_state(new_state)


def print_lookup_table(*statements, sorted_variables=True):
    variable_names = list(set(map(lambda var: var.name, find_variables(statements[0]))))
    if sorted_variables:
        variable_names.sort()
    
    if len(statements) > 1:
        variable_name_sets = [ set(map(lambda var: var.name, find_variables(statement))) for statement in statements ]
        for prev_var_set, var_set in zip(variable_name_sets[:1], variable_name_sets[1:]):
            if prev_var_set != var_set:
                raise LogicError('Variable names are not matching for all given statements.')

    # Backup states
    orig_states = []
    for statement in statements:
        orig_states.append([ [name, find_variable_state_or_default(statement, name)] for name in variable_names ])
    
    # Header
    print('', *variable_names, sep=' | ', end='')
    for variable_name in variable_names:
        for statement in statements:
            set_variable_state(statement, variable_name, None)
    statement_strings = list(map(lambda s: str(s).replace('=?', ''), statements))
    for i, statement_string in enumerate(statement_strings):
        if len(statement_string) > 32:
            statement_strings[i] = statement_string[:29] + '...'
    print('', *statement_strings, sep=' | ')

    # Data
    cols = len(variable_names)
    states = [ [name, 0] for name in variable_names ]
    sameResults = True
    for row in range(2**len(variable_names)):
        for col, name in enumerate(variable_names):
            state = (row // (2**(cols - 1 - col))) % 2
            states[col][1] = state
            print(' | ', state, sep='', end='')
            print(' '*(len(name) - 1), end='')
        
        lastState = None

        for statement, statement_string in zip(statements, statement_strings):
            for state_data in states:
                set_variable_state(statement, state_data[0], state_data[1])
            state = int(statement.state())
            if lastState is not None and lastState != state:
                sameResults = False
            lastState = state
            print(' | ', state, sep='', end='')
            print(' '*(len(statement_string) - 1), end='')
        print()

    if len(statements) > 1:
        print('Same results: %s' % sameResults)    

    # Restore states
    for statement, states in zip(statements, orig_states):
        for state_data in states:
            set_variable_state(statement, state_data[0], state_data[1])


def de_morgan(statement) -> Node:
    connHolder = None
    conn = statement
    while isinstance(conn, Not):
        connHolder = conn
        conn = conn.operands[0]
    
    negatedOperands = map(lambda o: Not(o), conn.operands)
    if isinstance(conn, And):
        oppositeConn = Not(Or(*negatedOperands))
    elif isinstance(conn, Or):
        oppositeConn = Not(And(*negatedOperands))
    else:
        raise LogicError('Invalid Note found for de morgan!')

    if connHolder is not None:
        connHolder.operands[0] = oppositeConn
    else:
        statement = oppositeConn
    
    return statement
