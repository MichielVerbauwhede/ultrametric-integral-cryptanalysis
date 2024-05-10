from pysat.solvers import Glucose42 as Solver
from nnf.kissat import solve
from nnf import And, Or, Var
from functools import reduce

def _clauses2cnf(clauses, assumptions = []):
    variables_in_clauses = sorted(reduce(set.union, map(lambda x: set(abs(y) for y in x), clauses)))
    vs = {i:Var(i) for i in variables_in_clauses}
    formula = And([Or([vs[x] if x > 0 else ~vs[-x] for x in clause]) for clause in clauses] + [Or([vs[x] if x > 0 else ~vs[-x]]) for x in assumptions])
    return vs, formula

def _nnf_model2pysat_model(vs, model):
    res = []
    for v in sorted(vs.keys()):
        if model[v]:
            res.append(v)
        else:
            res.append(-v)
    return res

def SAT_solve(clauses, assumptions = []):
    # with Solver(bootstrap_with=clauses) as solver:
    #     res = solver.solve(assumptions=assumptions)
    # return res
    return solve(_clauses2cnf(clauses, assumptions)[1]) is not None

def enum_projected_models(clauses, projected_vars, assumptions=[]):
    # with Solver(bootstrap_with=clauses) as solver:
    #     while solver.solve(assumptions=assumptions):
    #         model = solver.get_model()
    #         solver.add_clause(tuple(-model[v-1] for v in projected_vars))
    #         yield model
    while True:
        vs, formula = _clauses2cnf(clauses, assumptions)
        m_inter = solve(formula)
        if m_inter is None:
            break
        m = _nnf_model2pysat_model(vs, m_inter)
        clauses += (tuple(-m[v-1] for v in projected_vars),)
        yield m

def enum_models(model, assumptions=[]):
    # with Solver(bootstrap_with=model) as solver:
    #     for m in solver.enum_models(assumptions = assumptions):
    #         yield m
    model_vars = sorted(reduce(set.union, map(lambda x: set(abs(y) for y in x), clauses)))
    for m in enum_projected_models(clauses, model_vars, assumptions):
        yield m

def create_assumptions(vs, x):
    res = []
    for i in range(len(vs)):
        if (x>>i) & 1:
            res.append(vs[i])
        else:
            res.append(-vs[i])
    return tuple(res)

def from_assignment(vs, m):
    x = 0
    for s in vs[::-1]:
        x <<= 1
        if m[s-1] > 0:
            x |= 1
    return x