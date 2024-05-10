from Modelling.SAT_Solving import SAT_solve, enum_models, enum_projected_models

def contains_nonzero_trail(model, input_vars, output_vars, u, v, partially_defined_v=False):
    assumptions = []
    for i in range(len(input_vars)):
        assumptions.append((-1+2*((u >> i) & 1))*input_vars[i])
    if partially_defined_v:
        for i in range(len(output_vars)):
            if ((v >> i) & 1) == 0:
                assumptions.append(-output_vars[i])
    else:
        for i in range(len(output_vars)):
            assumptions.append((-1+2*((v >> i) & 1))*output_vars[i])
    return SAT_solve(model, assumptions)

def contains_key_dependent_trail(model, input_vars, output_vars, key_vars, u, v):
    model += (key_vars, )
    return contains_nonzero_trail(model, input_vars, output_vars, u, v)

def is_key_dependent(model, input_vars, output_vars, key_vars, u, v):
    model += (key_vars, )
    assumptions = []
    for i in range(len(input_vars)):
        assumptions.append((-1+2*((u >> i) & 1))*input_vars[i])
    for i in range(len(output_vars)):
        assumptions.append((-1+2*((v >> i) & 1))*output_vars[i])
    assumptions = tuple(assumptions)
    for k in enum_projected_models(model, key_vars, assumptions=assumptions):
        if sum(1 for _ in enum_models(model, assumptions + k)) % 2 == 1:
            return True
    return False

def is_key_dependent_limited(model, input_vars, output_vars, key_vars, u, v, limit=2**6):
    # returns true if key dependent or when limit is reached
    model += (key_vars, )
    assumptions = []
    for i in range(len(input_vars)):
        assumptions.append((-1+2*((u >> i) & 1))*input_vars[i])
    for i in range(len(output_vars)):
        assumptions.append((-1+2*((v >> i) & 1))*output_vars[i])
    assumptions = tuple(assumptions)
    l = 0
    for k in enum_projected_models(model, key_vars, assumptions=assumptions):
        c = 0
        for _ in enum_models(model, assumptions + k):
            c+= 1
            l += 1
            if l > limit:
                return True
        if c % 2 == 1:
            return True
    return False

def get_sum(model, input_vars, output_vars, key_vars, u, v):
    assumptions = []
    for i in range(len(input_vars)):
        assumptions.append((-1+2*((u >> i) & 1))*input_vars[i])
    for i in range(len(output_vars)):
        assumptions.append((-1+2*((v >> i) & 1))*output_vars[i])
    assumptions = tuple(assumptions)
    V = set()
    for k in enum_projected_models(model, key_vars, assumptions=assumptions):
        if sum(1 for _ in enum_models(model, assumptions + k)) % 2 == 1:
            km = 0
            for v in k[::-1]:
                km <<= 1
                if v > 0:
                    km += 1
            if k in V:
                V.remove(km)
            else:
                V.add(km)
    return V

def get_key_independent_sum(model, input_vars, output_vars, key_vars, u, v):
    assumptions = []
    for i in range(len(input_vars)):
        assumptions.append((-1+2*((u >> i) & 1))*input_vars[i])
    for i in range(len(output_vars)):
        assumptions.append((-1+2*((v >> i) & 1))*output_vars[i])
    for k in key_vars:
        assumptions.append(-k)
    return sum(1 for _ in enum_models(model, assumptions)) % 2

def get_key_independent_sum_limited(model, input_vars, output_vars, key_vars, u, v, limit=2**6):
    # returns the key independent sum, except if the limit is reached, then it returns 1
    assumptions = []
    for i in range(len(input_vars)):
        assumptions.append((-1+2*((u >> i) & 1))*input_vars[i])
    for i in range(len(output_vars)):
        assumptions.append((-1+2*((v >> i) & 1))*output_vars[i])
    for k in key_vars:
        assumptions.append(-k)
    c = 0
    for _ in solver.enum_models(assumptions = assumptions):
        c += 1
        if c > limit:
            return 1
    return c % 2
