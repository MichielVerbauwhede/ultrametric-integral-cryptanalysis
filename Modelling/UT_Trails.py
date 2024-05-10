from Modelling.Trails import contains_nonzero_trail, contains_key_dependent_trail, is_key_dependent
from Modelling.SAT_Solving import enum_projected_models, create_assumptions, from_assignment
from pysat.card import CardEnc, EncType
from pysat.formula import IDPool
from math import inf, log2
from functools import reduce

def _add_input_reduction(model, input_vars):
    nvars = max(map(lambda x: max(map(abs, x)), model))
    pool = IDPool(nvars+1)
    # modify model to add input reduction
    new_input_vars = tuple(pool.id() for _ in input_vars)
    extra_count_vars = tuple(pool.id() for _ in input_vars)
    for i, o, c in zip(new_input_vars, input_vars, extra_count_vars):
        model += ((i, -o),)
        model += ((-i, o, c),)
        model += ((i, -c),)
        model += ((-o, -c),)

    return model, new_input_vars, extra_count_vars

def get_divisibility_no_trail(model, input_vars, output_vars, key_vars, count_vars, u, v, precursor=True, partially_defined_v=False, debug=False):
    if precursor:
        model, input_vars, ecv = _add_input_reduction(model, input_vars)
        count_vars += ecv
    if not contains_nonzero_trail(model, input_vars, output_vars, u, v):
        return inf
    r = 0
    nvars = max(map(lambda x: max(map(abs, x)), model))
    while not contains_nonzero_trail(model + tuple(CardEnc.equals(count_vars, r, top_id=nvars+1).clauses), input_vars, output_vars, u, v, partially_defined_v):
        r += 1
        if debug:
            print(f"debug: at least divisible by 2^{r}")

    return r
        
def get_divisibility_no_key_dependent_trail(model, input_vars, output_vars, key_vars, count_vars, u, v, precursor=True):
    if precursor:
        model, input_vars, ecv = _add_input_reduction(model, input_vars)
        count_vars += ecv

    assumptions = []
    for i in range(len(input_vars)):
        assumptions.append((-1+2*((u >> i) & 1))*input_vars[i])
    for i in range(len(output_vars)):
        assumptions.append((-1+2*((v >> i) & 1))*output_vars[i])
    for k in key_vars:
            assumptions.append(-k)
    
    if not contains_nonzero_trail(model, input_vars, output_vars, u, v):
        return inf

    enumeration_vars = reduce(set.union, map(lambda x: set(abs(y) for y in x), model))
    d = 0
    card_enc = tuple(CardEnc.equals(count_vars, d, top_id=len(enumeration_vars)+1).clauses)
    while True:
        if contains_key_dependent_trail(model + card_enc, input_vars, output_vars, key_vars, u, v):
            return d
        s = sum(1 for _ in enum_projected_models(model + card_enc, enumeration_vars, assumptions = assumptions))
        if s > 0:
            if s % 2 == 1:
                return d
            else:
                return d + 1
        d += 1
        # if d > u.bit_count():
        #     return inf
        card_enc = tuple(CardEnc.equals(count_vars, d, top_id=len(enumeration_vars)+1).clauses)

def get_divisibility_no_key_dependence(model, input_vars, output_vars, key_vars, count_vars, u, v, precursor=True, return_key_mon = False):
    if precursor:
        model, input_vars, ecv = _add_input_reduction(model, input_vars)
        count_vars += ecv

    assumptions = create_assumptions(input_vars, u) + create_assumptions(output_vars, v)
    
    if not contains_nonzero_trail(model, input_vars, output_vars, u, v):
        return inf

    enumeration_vars = reduce(set.union, map(lambda x: set(abs(y) for y in x), model))
    d = 0
    while True:
        key_mons = {}
        # collect new key candidates
        card_enc = tuple(CardEnc.equals(count_vars, d, top_id=len(enumeration_vars)+1).clauses)
        exists_models = False
        for m in enum_projected_models(model + card_enc, key_vars, assumptions = assumptions):
            exists_models = True
            km = from_assignment(key_vars, m)
            assumptions2 = create_assumptions(key_vars, km)
            c = 0
            for m in enum_projected_models(model + card_enc, enumeration_vars, assumptions = assumptions+assumptions2):
                c += 1
            if c % 2 == 1:
                if return_key_mon:
                    return d, km
                else:
                    return d
        
        if exists_models:
            if return_key_mon:
                return d + 1, None
            return d + 1
        d += 1
        # if d > u.bit_count():
        #     if return_higher_divisibility_poly:
        #         return inf, None
        #     return inf

def get_divisibility_of_key_dependence_no_trail(model, input_vars, output_vars, key_vars, count_vars, u, v, precursor=True):
    if precursor:
        model, input_vars, ecv = _add_input_reduction(model, input_vars)
        count_vars += ecv

    assumptions = []
    for i in range(len(input_vars)):
        assumptions.append((-1+2*((u >> i) & 1))*input_vars[i])
    for i in range(len(output_vars)):
        assumptions.append((-1+2*((v >> i) & 1))*output_vars[i])
    for k in key_vars:
            assumptions.append(-k)
    
    if not contains_nonzero_trail(model, input_vars, output_vars, u, v):
        return inf

    enumeration_vars = reduce(set.union, map(lambda x: set(abs(y) for y in x), model))
    d = 0
    card_enc = tuple(CardEnc.equals(count_vars, d, top_id=len(enumeration_vars)+1).clauses)
    while True:
        if contains_key_dependent_trail(model + card_enc, input_vars, output_vars, key_vars, u, v):
            return d
        d += 1
        # if d > u.bit_count():
        #     return inf
        card_enc = tuple(CardEnc.equals(count_vars, d, top_id=len(enumeration_vars)+1).clauses)