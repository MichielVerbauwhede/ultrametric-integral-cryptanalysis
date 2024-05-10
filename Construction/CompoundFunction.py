from .Function import Function
from .Components import Component, XOR
from pysat.formula import IDPool

INPUT_ID = 0
OUTPUT_ID = 2**64
KEY_ID = -1
ERROR_ID = -2


class Null(Function):
    def __init__(self, input_size, output_size):
        super().__init__(input_size, output_size)
        self.n_cnf_vars = 0

    def __call__(self, v):
        return 0

class component_record(object):
    def __init__(self, f):
        self.f = f
        self.input_connections = [(ERROR_ID, ERROR_ID)]*f.input_size
        self.output_connections = [(ERROR_ID, ERROR_ID)]*f.output_size
        self.input_key_mask = 0
        self.output_key_mask = 0
        return


class CompoundFunction(Function):
    def __init__(self, input_size, output_size):
        super().__init__(input_size, output_size)
        # component list contains component, inputs, outputs, input_vars, output_vars
        self.components =\
            {INPUT_ID: component_record(Null(0, self.input_size)) ,
             OUTPUT_ID: component_record(Null(self.output_size, 0))}
        self.n_components = 0
        self.n_key_bits = 0
        self.key = 0
        self.local_model = tuple()
        self.local_UT_model = tuple()
        self.local_input_vars = tuple()
        self.local_output_vars = tuple()
        self.local_key_vars = tuple()
        self.local_c_vars = tuple()
        self.local_vars = {}
        self.n_vars = 0
        return

    def add_component(self, component):
        """
        Add component to Compound Function.
        Components should be added in order of execution.
        The id of the component is returned
        """
        assert(not isinstance(component, CompoundFunction) or component.n_key_bits == 0)
        self.n_components += 1
        self.components[self.n_components] = component_record(component)
        return self.n_components

    def connect_components(self, from_component, from_wire, to_component, to_wire):
        """
        connect one component to another
        """
        # check existence of components
        assert(-1 < from_component <= self.n_components)
        assert(-1 < to_component <= self.n_components or to_component == OUTPUT_ID)
        # check existence of wires
        assert(from_wire < self.components[from_component].f.output_size)
        assert(to_wire < self.components[to_component].f.input_size)
        # enforce order of computation
        assert(from_component < to_component)
        # update information
        assert(self.components[from_component].output_connections[from_wire] == (ERROR_ID, ERROR_ID))
        self.components[from_component].output_connections[from_wire] = (to_component, to_wire)
        assert(self.components[to_component].input_connections[to_wire] == (ERROR_ID, ERROR_ID))
        self.components[to_component].input_connections[to_wire] = (from_component, from_wire)
        return

    def connect_to_key(self, to_component, to_wire):
        assert(-1 < to_component <= self.n_components)
        assert(to_wire < self.components[to_component].f.input_size)
        assert(self.components[to_component].input_connections[to_wire] == (ERROR_ID, ERROR_ID))
        self.components[to_component].input_connections[to_wire] = (KEY_ID, self.n_key_bits)
        self.n_key_bits += 1
        return

    def __call__(self, v):
        # evaluates with random key based on the given key value
        outputs = [v]
        for i in range(1, self.n_components+1):
            # construct input
            x = 0
            for wire in self.components[i].input_connections[::-1]:
                x <<= 1
                if wire[0] == KEY_ID:
                    x |= ((key >> wire[1]) & 1)
                else:
                    x |= ((outputs[wire[0]] >> wire[1]) & 1)
            # get output
            outputs.append(self.components.get(i).f(x))
        # construct output
        x = 0
        for wire in self.components[OUTPUT_ID].input_connections[::-1]:
            x <<= 1
            if wire[0] == KEY_ID:
                x |= ((key >> wire[1]) & 1)
            else:
                x |= ((outputs[wire[0]] >> wire[1]) & 1)
        return x

    def __build_local_model(self):
        for record in self.components.values():
            assert((ERROR_ID, ERROR_ID) not in record.input_connections)
            assert((ERROR_ID, ERROR_ID) not in record.output_connections)

        pool = IDPool()
        self.local_model = []
        # build model
        all_component_output_vars = {}
        self.local_key_vars = tuple(pool.id() for _ in range(self.n_key_bits))
        for i in range(self.n_key_bits):
            all_component_output_vars[(KEY_ID, i)] = self.local_key_vars[i]
        for i in range(self.n_components+1):
            component = self.components[i]
            f = component.f
            # generate output vars
            output_vars = tuple(pool.id() for _ in range(f.output_size))
            for j in range(f.output_size):
                all_component_output_vars[(i, j)] = output_vars[j]
            # generate input vars
            input_vars = tuple(all_component_output_vars[wire] for wire in component.input_connections)
            # generate clauses
            if isinstance(f, Component):
                vs = [0]*(f.input_size + f.output_size+1)
                for j in range(f.input_size):
                    vs[j+1] = input_vars[j]
                for j in range(f.output_size):
                    vs[f.input_size + j + 1] = output_vars[j]
                self.local_vars[i] = vs.copy()
                vs += [-x for x in vs[1:][::-1]]
                for clause in f.get_parity_propagation_model(component.input_key_mask, component.output_key_mask):
                    self.local_model.append(tuple(vs[x] for x in clause))
            elif isinstance(f, CompoundFunction):
                clauses = f.to_model()[0]
                vs = [0]*(f.n_vars+1)
                for j in range(f.input_size):
                    vs[f.local_input_vars[j]] = input_vars[j]
                for j in range(f.output_size):
                    vs[f.local_output_vars[j]] = output_vars[j]
                for j in range(1, len(vs)):
                    if vs[j] == 0:
                        vs[j] = pool.id()
                self.local_vars[i] = vs.copy()
                vs += [-x for x in vs[1:][::-1]]
                for clause in clauses:
                    self.local_model.append(tuple(vs[x] for x in clause))
            else:
                self.local_input_vars = output_vars
            # recover local output vars
        self.local_output_vars = tuple(all_component_output_vars[wire] for wire in self.components[OUTPUT_ID].input_connections)
        self.n_vars = max(map(lambda x: max(map(abs, x)), self.local_model))
        return

    def to_model(self, pool=None, input_vars = tuple(), output_vars = tuple(), key_vars = tuple()):
        if len(self.local_model) == 0:
            self.__build_local_model()

        if pool is None:
            return tuple(self.local_model), self.local_input_vars, self.local_output_vars, self.local_key_vars
        
        if len(input_vars) == 0:
            input_vars = tuple(pool.id() for _ in range(self.input_size))
        else:
            input_vars = tuple(input_vars)
        if len(output_vars) == 0:
            output_vars = tuple(pool.id() for _ in range(self.output_size))
        else:
            output_vars = tuple(output_vars)

        vs = [0]*(self.n_vars+1)
        for i in range(self.input_size):
            vs[self.local_input_vars[i]] = input_vars[i]
        for i in range(self.output_size):
            vs[self.local_output_vars[i]] = output_vars[i]
        for i in range(1, len(vs)):
            if vs[i] == 0:
                vs[i] = pool.id()
        vs += [-x for x in vs[1:][::-1]]
        model = []
        for clause in self.local_model:
            model.append(tuple(vs[x] for x in clause))
        
        return model, input_vars, output_vars, key_vars

    def __build_local_UT_model(self):
        self.__build_local_model()
        pool = IDPool(start_from=self.n_vars+1)
        self.local_UT_model = []
        # build model
        for i in range(1, self.n_components+1):
            component = self.components[i]
            f = component.f
            # generate clauses
            if isinstance(f, Component):
                c_vars = tuple(pool.id() for _ in range(f.get_n_cvars()))
                vs = self.local_vars[i] + list(c_vars)
                vs += [-x for x in vs[1:][::-1]]
                for clause in f.get_UT_propagation_model():
                    self.local_UT_model.append(tuple(vs[x] for x in clause))
                self.local_c_vars += c_vars
            elif isinstance(f, CompoundFunction):
                clauses, _, _, _, cv = f.to_UT_model()
                c_vars = tuple(pool.id() for _ in range(len(cv)))
                vs = self.local_vars[i] + list(c_vars)
                vs += [-x for x in vs[1:][::-1]]
                for clause in clauses:
                    self.local_UT_model.append(tuple(vs[x] for x in clause))
                self.local_c_vars += c_vars
        return

    def to_UT_model(self, pool=None, input_vars = tuple(), output_vars = tuple(), key_vars = tuple(), c_vars = tuple()):
        # this model does not include the possible gain at the input set
        if len(self.local_UT_model) == 0:
            self.__build_local_UT_model()

        if pool is None:
            return tuple(self.local_UT_model), self.local_input_vars, self.local_output_vars, self.local_key_vars, self.local_c_vars
        
        if len(input_vars) == 0:
            input_vars = tuple(pool.id() for _ in range(self.input_size))
        else:
            input_vars = tuple(input_vars)
        if len(output_vars) == 0:
            output_vars = tuple(pool.id() for _ in range(self.output_size))
        else:
            output_vars = tuple(output_vars)
        if len(key_vars) == 0:
            key_vars = tuple(pool.id() for _ in range(self.n_key_bits))
        else:
            key_vars = tuple(key_vars)
        if len(c_vars) == 0:
            c_vars = tuple(pool.id() for _ in range(len(self.local_c_vars)))
        else:
            c_vars = tuple(c_vars)

        vs = [0]*(self.n_vars+len(self.local_c_vars)+1)
        for i in range(self.input_size):
            vs[self.local_input_vars[i]] = input_vars[i]
        for i in range(self.output_size):
            vs[self.local_output_vars[i]] = output_vars[i]
        for i in range(self.n_key_bits):
            vs[self.local_key_vars[i]] = key_vars[i]
        for i in range(len(self.local_c_vars)):
            vs[self.local_c_vars[i]] = c_vars[i]
        for i in range(1, len(vs)):
            if vs[i] == 0:
                vs[i] = pool.id()
        vs += [-x for x in vs[1:][::-1]]
        model = []
        for clause in self.local_UT_model:
            model.append(tuple(vs[x] for x in clause))
        
        return model, input_vars, output_vars, key_vars, c_vars
        