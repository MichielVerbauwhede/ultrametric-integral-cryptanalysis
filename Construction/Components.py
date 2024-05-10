from .Function import Function 
from Modelling.PropModels import compute_parity_propagation_model, compute_UT_propagation_model
from abc import abstractmethod
from pysat.card import CardEnc, EncType

class Component(Function):
    def __init__(self, input_size, output_size):
        super().__init__(input_size, output_size)
        self.parity_prop_models = {}
        self.n_cvars = 0
        self.UT_prop_model = None

    def compute_parity_propagation_model(self, input_key_mask, output_key_mask):
        return compute_parity_propagation_model(self, input_key_mask, output_key_mask)

    def get_parity_propagation_model(self, input_key_mask, output_key_mask):
        if (input_key_mask, output_key_mask) not in self.parity_prop_models:
            self.parity_prop_models[(input_key_mask, output_key_mask)] = self.compute_parity_propagation_model(input_key_mask, output_key_mask)
        return self.parity_prop_models[(input_key_mask, output_key_mask)]

    def compute_UT_propagation_model(self):
        return compute_UT_propagation_model(self)

    def get_UT_propagation_model(self):
        if self.UT_prop_model is None:
            self.UT_prop_model, self.n_cvars = self.compute_UT_propagation_model()
        return self.UT_prop_model

    def get_n_cvars(self):
        if self.UT_prop_model is None:
            self.UT_prop_model, self.n_cvars = self.compute_UT_propagation_model()
        return self.n_cvars

    @abstractmethod
    def __call__(self, v):
        return 0

class SBox(Component):

    def __init__(self, input_size, output_size, lookup_table: list):
        self.lookup_table = lookup_table
        super().__init__(input_size, output_size)

    def __call__(self, v):
        return self.lookup_table[v]

class __COPYn(Component):
    def __init__(self, n):
        self.n = n
        super().__init__(1, n)

    def __call__(self, v):
        r = 0
        for _ in range(self.n):
            r <<= 1
            r += v & 1
        return r

_COPYs = {}
def get_COPYn(i):
    global _COPYs
    if i not in _COPYs:
        _COPYs[i] = __COPYn(i)
    return _COPYs[i]

class __XORn(Component):

    def __init__(self, n):
        super().__init__(n, 1)
        self.n = n

    def __call__(self, v):
        r = 0
        for i in range(self.n):
            r ^= v & 1
            v >>= 1
        return r
    
    def compute_parity_propagation_model(self, input_key_mask, output_key_mask):
        atmost1 = tuple(tuple(x) for x in CardEnc.atmost(lits = list(range(1, self.n+1)), encoding = EncType.pairwise).clauses)
        if input_key_mask.bit_count() == output_key_mask.bit_count() == 0:
            return atmost1 +  tuple((-v, self.n+1) for v in range(1, self.n+1)) + (tuple(range(1, self.n+1)) + (-self.n+1,),)
        else:
            return atmost1 + tuple((-v, self.n+1) for v in range(1, self.n+1))


_XORs = {}
def get_XORn(i):
    global _XORs
    if i not in _XORs.keys():
        _XORs[i] = __XORn(i)
    return _XORs[i]

XOR = get_XORn(2)

class __Sink(Component):

    def __init__(self):
        super().__init__(1, 0)

    def __call__(self, v):
        return 0

    def compute_parity_propagation_model(self, input_key_mask, output_key_mask):
        return ((-1,),)

Sink = __Sink()

class __IDn(Component):

    def __init__(self, n):
        super().__init__(n, n)
        self.n = n

    def __call__(self, v):
        return v
    
    def compute_parity_propagation_model(self, input_key_mask, output_key_mask):
        clauses = []
        km = input_key_mask | output_key_mask
        for i in range(self.n):
            clauses.append((-i-1, i+1+self.n))
            if km & (1<<i) == 0:
                clauses.append((i+1, -i-1-self.n))
        return tuple(clauses)

    def compute_UT_propagation_model(self):
        return self.compute_parity_propagation_model(0, 0), 0
    
_IDs = {}
def get_IDn(i):
    global _IDs
    if i not in _IDs.keys():
        _IDs[i] = __IDn(i)
    return _IDs[i]

ID = get_IDn(1)

class __addKey(Component):

    def __init__(self): # assume second input is key
        super().__init__(2, 1)

    def __call__(self, v):
        return (v&1) ^ (v>>1)
    
    def compute_parity_propagation_model(self, input_key_mask, output_key_mask): # ignore key masks
        return XOR.compute_parity_propagation_model(0, 0)
    
    def compute_UT_propagation_model(self):
        return XOR.compute_parity_propagation_model(0, 0), 0

addKey = __addKey()

class __feistel_xor(Component):
    # duplicate first input in r0 and xor of inputs in r1
    def __init__(self):
        super().__init__(2, 2)

    def __call__(self, v):
        v0, v1 = v & 1, (v>>1) & 1
        return (v0 ^ v1) << 1 | v0

feistel_xor = __feistel_xor()

class FakeComponent(Component):
    def __init__(self, n, m, ut_cnf, n_extra_vars):
        super().__init__(n, m)
        self.ut_cnf = ut_cnf
        self.ut_ncntv = n_extra_vars
        cnf_clauses = []
        for clause in ut_cnf:
            if all(x >= -n-m for x in clause):
                cnf_clauses.append(tuple(x for x in clause if x <= n+m))
        self.cnf = tuple(cnf_clauses)

    def compute_parity_propagation_model(self, input_key_mask, output_key_mask): # ignore key masks
        return self.cnf
    
    def compute_UT_propagation_model(self):
        return self.ut_cnf, self.ut_ncntv

    def __call__(self, v):
        return 0