from .SAT_Solving import enum_projected_models, create_assumptions, from_assignment
from multiprocessing import Pool
from itertools import product
from pysat.formula import IDPool
from pysat.card import CardEnc, EncType
from time import time
from functools import partial, reduce
from .PropModels import to_ord

def construct_model_with_intermediate_vars(fs, precursor):
    vpool = IDPool()
    # add constraints for input
    if precursor:
        input_vars = tuple(vpool.id() for _ in range(64))
        count_vars = tuple(vpool.id() for _ in range(64))
        output_vars = tuple(vpool.id() for _ in range(64))
        model = tuple()
        for i, o, c in zip(input_vars, output_vars, count_vars):
            model += ((i, -o),)
            model += ((-i, o, c),)
            model += ((i, -c),)
            model += ((-o, -c),)
        models, input_varss, output_varss, key_varss, count_varss = [model], [input_vars], [output_vars], [tuple()], [count_vars]
    else:
        models, input_varss, output_varss, key_varss, count_varss = [], [], [], [], []

    # add contraints for rounds
    for f in fs:
        if len(output_varss) > 0:
            model, input_vars, output_vars, key_vars, count_vars = f.to_UT_model(pool=vpool, input_vars=output_varss[-1])
        else:
            model, input_vars, output_vars, key_vars, count_vars = f.to_UT_model(pool=vpool)
        models.append(tuple(model))
        input_varss.append(input_vars)
        output_varss.append(output_vars)
        key_varss.append(key_vars)
        count_varss.append(count_vars)
    
    return sum(models, tuple()), input_varss, output_varss, key_varss, sum(count_varss, tuple()), vpool.top

def reduce_propagated_set(s, m):
    for v in tuple(s.keys()):
        for k in tuple(s[v].keys()):
            if s[v][k] & ((1<<m) - 1) == 0:
                del s[v][k]
            else:
                s[v][k] &= ((1<<m) - 1)
        if len(s[v]) == 0:
            del s[v]
    return s

def extend_propagated_sets(s_old, s_prop, m):
    res = {}
    for (k0,s0), (k1,s1) in product(s_old.items(), s_prop.items()):
        if ((s0*s1) & ((1<<m) - 1)) != 0:
            res[k0 + k1] = (s0*s1) & ((1<<m) - 1)
    return res

def merge_propagated_sets(s1, s2, m):
    for u in s2:
        if u in s1:
            for k in s2[u]:
                if k in s1[u]:
                    s1[u][k] += s2[u][k]
                    s1[u][k] &= ((1<<m) - 1)
                    if s1[u][k] == 0:
                        del s1[u][k]
                else:
                    s1[u][k] = s2[u][k]
        else:
            s1[u] = s2[u]
    return s1

def intersect_propagated_sets(f, b, m):
    res = {}
    for u in f:
        if u in b:
            res2 = extend_propagated_sets(f[u], b[u], m)
            for k in res2:
                if k in res:
                    res[k] += res2[k]
                    res[k] &= (1<<m) - 1
                    if res[k] == 0:
                        del res[k]
                else:
                    res[k] = res2[k]
    return res

def propagate(model, fix_vars, enum_vars, key_vars, m, prev_cor, comp_cor, xs, backwards = False):
    res = {}
    for x in xs:
        res2 = {}
        assumptions = create_assumptions(fix_vars, x)
        for r in enum_projected_models(model, enum_vars + key_vars, assumptions=assumptions):
            y = from_assignment(enum_vars, r)
            k = from_assignment(key_vars, r)
            if backwards:
                ex = extend_propagated_sets({(k,): comp_cor(y, x, k) & ((1<<m) - 1)}, prev_cor[x], m)
            else:
                ex = extend_propagated_sets(prev_cor[x], {(k,): comp_cor(x, y, k) & ((1<<m) - 1)}, m)
            if y in res2:
                for a, b in ex.items():
                    res2[y][a] = b
            else:
                res2[y] = ex
        res = merge_propagated_sets(res, res2, m)
    return res

def compute_correlation_precursor_model(u, v, k):
    return 2**((v ^ u).bit_count())

def compute_exact_correlation_mod(functions, correlation_evals, u, v, m, precursor = True, NThreads = 1, debug = False):
    """
    functions: A list of compound functions (see Construction.CompoundFunction) that are evaluated in order
    correlation evals: functions that compute the correlation of the propagation through a single Function in functions,
        their input should be in order: input_vars, output_vars, key_vars
    u: input mask
    v: output mask
    m: compute correlation modulo $2^m$
    precursor: whether to model a precursor set as input or a unit vector
    """
    # create model
    model, input_varss, output_varss, key_varss, count_vars, top_var = construct_model_with_intermediate_vars(functions, precursor = precursor)
    model += tuple(CardEnc.atmost(count_vars, bound=m-1, top_id = top_var).clauses)
    for x in create_assumptions(input_varss[0], u) + create_assumptions(output_varss[-1], v):
        model += ((x,),)
    # update correlation_evals if necessary
    if precursor:
        correlation_evals = [compute_correlation_precursor_model] + list(correlation_evals)
    # instantiate backward propagation set
    backward = {v:{tuple():1}}
    bi = len(input_varss)
    # instantiate forward propagation set
    forward = {u:{tuple():1}}
    fi = 0

    # propagate either forwards or backwards until the fi and bi indices meet
    # the direction is decided based on the sizes of the forward and backward propagated sets
    while bi != fi:
        with Pool(NThreads) as pool:
            if len(backward) < len(forward): # propagate backwards
                if debug:
                    print("computing propagation backwards")
                    stime = time()
                bi -= 1
                parf = partial(propagate, model, output_varss[bi], input_varss[bi], key_varss[bi], m, backward, correlation_evals[bi], backwards=True)
                backward = reduce(partial(merge_propagated_sets, m=m), pool.map(parf, [tuple(backward.keys())[i::NThreads] for i in range(NThreads)], chunksize=1), {})
                if debug:
                    print(f"backwards propagation resulted in {len(backward)} v's after {time() - stime} seconds")
            else: # propagate forwards
                if debug:
                    print("computing propagation forwards")
                    stime = time()
                parf = partial(propagate, model, input_varss[fi], output_varss[fi], key_varss[fi], m, forward, correlation_evals[fi], backwards=False)
                forward = reduce(partial(merge_propagated_sets, m=m), pool.map(parf, [tuple(forward.keys())[i::NThreads] for i in range(NThreads)], chunksize=1), {})
                fi += 1
                if debug:
                    print(f"forwards propagation resulted in {len(forward)} u's after {time() - stime} seconds")
    
    # intersect bases and return
    return intersect_propagated_sets(forward, backward, m)

def extend_propagated_sets_var(k, c, prop, m, backwards):
    res = {}
    for (k0, k1), c2 in prop.items():
        c3 = (c*c2) & ((1<<m) - 1)
        if c3 != 0:
            if backwards:
                res[(k0, (k, ) + k1)] = c3
            else:
                res[(k0 + (k, ), k1)] = c3
    return res

def propagate_var(model, count_vars, top_var, input_vars, output_vars, enum_vars, key_vars, m, comp_cor, ios, backwards = False):
    res = {}
    for (u, v), prop in ios:
        res2 = {}
        assumptions = create_assumptions(input_vars, u)
        assumptions += create_assumptions(output_vars, v)
        # create cardinality constraints
        o = int(min(map(to_ord, prop.values())))
        new_model = model + tuple(CardEnc.atmost(count_vars, bound=m-1-o, top_id = top_var).clauses)
        for r in enum_projected_models(new_model, enum_vars + key_vars, assumptions=assumptions):
            x = from_assignment(enum_vars, r)
            k = from_assignment(key_vars, r)

            if backwards:
                ex = extend_propagated_sets_var(k, comp_cor(x, v, k) & ((1<<m) - 1), prop, m, True)
                s = (u, x)
            else:
                ex = extend_propagated_sets_var(k, comp_cor(u, x, k) & ((1<<m) - 1), prop, m, False)
                s = (x, v)
            
            if s in res2:
                for a, b in ex.items():
                    res2[s][a] = b
            else:
                res2[s] = ex

        res = merge_propagated_sets(res, res2, m)
    return res

def compute_exact_correlation_mod_var(functions, correlation_evals, u, v, m, precursor = True, NThreads = 1, debug = False):
    """
    functions: A list of compound functions (see Construction.CompoundFunction) that are evaluated in order
    correlation evals: functions that compute the correlation of the propagation through a single Function in functions,
        their input should be in order: input_vars, output_vars, key_vars
    u: input mask
    v: output mask
    m: compute correlation modulo $2^m$
    precursor: whether to model a precursor set as input or a unit vector
    """
    # debug setup
    if debug:
        dbg_msg = {True:"back", False:"for"}
    # update correlation_evals if necessary
    if precursor:
        correlation_evals = [compute_correlation_precursor_model] + list(correlation_evals)
    # instantiate propagation set and indices
    io = {(u, v): {(tuple(), tuple()) : 1}}
    fi = 0
    bi = len(correlation_evals)

    # propagate either forwards or backwards until the fi and bi indices meet
    # the direction is decided based on the sizes number of unique u's or v's
            
    while bi != fi:
        with Pool(NThreads) as pool:
            # compute model
            if precursor:
                if fi == 0:
                    model, input_varss, output_varss, key_varss, count_vars, top_var = construct_model_with_intermediate_vars(functions[fi:bi-1], precursor = precursor)
                else:
                    model, input_varss, output_varss, key_varss, count_vars, top_var = construct_model_with_intermediate_vars(functions[fi-1:bi-1], precursor=False)
            else:
                model, input_varss, output_varss, key_varss, count_vars, top_var = construct_model_with_intermediate_vars(functions[fi:bi], precursor=False)
            # decide on propagation direction
            us, vs = set(), set()
            for u, v in io.keys():
                us.add(u); vs.add(v)
            go_backwards = len(vs) <= len(us)
            io = tuple(io.items())
            # go_backwards = True

            if debug:
                # print(f"There are {len(us)} unique u's and {len(vs)} unique v's.")
                print(f"computing propagation {dbg_msg[go_backwards]}wards")
                stime = time()   

            if go_backwards:
                bi -= 1
                enum_vars = input_varss[-1]
                key_vars = key_varss[-1]
                comp_cor = correlation_evals[bi]
            else:
                enum_vars = output_varss[0]
                key_vars = key_varss[0]
                comp_cor = correlation_evals[fi]
                fi += 1

            parf = partial(propagate_var, model, count_vars, top_var, input_varss[0], output_varss[-1], enum_vars, key_vars, m, comp_cor, backwards=go_backwards)
            io = reduce(partial(merge_propagated_sets, m=m), pool.map(parf, [tuple(io)[i::8*NThreads] for i in range(8*NThreads)], chunksize=1), {})
            io = reduce_propagated_set(io, m)
            
            if debug:
                print(f"{dbg_msg[go_backwards]}wards propagation resulted in {len(io)} pairs after {time() - stime} seconds")

    # compute final result
    res = {}
    for _, prop in io.items():
        for (k1, k2), c in prop.items():
            res[k1 + k2] = res.get(k1+k2, 0) + c
    for k in tuple(res.keys()):
        res[k] &= ((1<<m) - 1)
        if res[k] == 0:
            del res[k]
    return res