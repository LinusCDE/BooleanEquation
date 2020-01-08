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


def _operandGenerator(operands):
    '''
    Generate guaranteed list of operands based on Node.
    Attempts to parse other types or raises InvalidOperandError!
    '''
    for operand in operands:
        if isinstance(operand, int) or isinstance(operand, bool):
            yield Const(operand)
        elif isinstance(operand, Node):
            yield operand
        else:
            raise InvalidOperandError("The following operand isn't based on Node and can't be changed to Const(): %s" % repr(operand))


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
        self.operand = next(_operandGenerator((operand,)))
    
    def state(self) -> bool:
        return not self.operand.state()
    
    def set_state(self, newState: bool):
        try:
            if self.state() == newState:
                return
        except UnknownStateError:
            pass
        
        self.operand.set_state(not newState)
    
    def __repr__(self):
        return 'Not(%s)' % repr(self.operand)
    
    def __str__(self):
        return '~(%s)' % self.operand


class Xor(Node):
    def __init__(self, *operands):
        '''
        All that matters is that there is ANY value that is True.
        Unknown values don't matter in that case.
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

def Nor(*operands):
    return Not(Or(operands))

def Nand(*operands):
    return Not(And(operands))
