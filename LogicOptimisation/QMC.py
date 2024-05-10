from math import log2
from bitarrays.bitset import BitSet
from ortools.sat.python import cp_model
from multiprocessing import Pool, Manager
from functools import partial

QMC_THREADS = 32
def __f(truth_table, S, a):
    if not BitSet.test(truth_table, a):
        # X = ~(a + P)
        X = BitSet(truth_table)
        X.swap(a)
        # X = ~upperclosure(X)
        X.ORup()
        X.flip()
        # X = maxset(X)
        X.ORdown()
        X.MOREdown()
        for u in X:
            if (u & a) == 0:
                S.append((a, u))

def DNF_prime_implicants_complement(truth_table, threads=QMC_THREADS):
    if threads > 1:
        with Manager() as manager:
            S = manager.list()
            with Pool(threads) as pool:
                for _ in pool.imap_unordered(partial(__f, truth_table, S), range(truth_table.size()), 4*QMC_THREADS):
                    pass
            S = list(S)
    else:
        S = []
        for a in range(truth_table.size()):
            __f(truth_table, S, a)
    return S

def __g(S, variables, v):
    constraint_vars = list()
    for i in range(len(S)):
        if (((S[i][0] ^ v) & (~S[i][1])) == 0):
            constraint_vars.append(variables[i])
    return tuple(constraint_vars)

def QMC_optimise_CNF(truth_table, dont_care, max_search_time=60, threads=QMC_THREADS):
    # expected that truth_table is zero where dont_care is one
    # generate prime implicants (for DNF of ~F) (as per Boura and Coggia 2020 and Udovenko 2021)
    S = DNF_prime_implicants_complement(truth_table, threads)
    # model set cover problem as CP-SAT
    model = cp_model.CpModel()
    # generate variables
    variables = []
    for i in range(len(S)):
        variables.append(model.NewBoolVar(f"x{i}"))
    # generate constraints
    if threads > 1:
        with Pool(threads) as pool:
            for constraint_vars in pool.imap_unordered(partial(__g, S, variables), filter(lambda v: (not truth_table.test(v) and not dont_care.test(v)),  range(truth_table.size())), 4*QMC_THREADS):
                model.AddAtLeastOne(constraint_vars)
    else:
        for constraint_vars in map(partial(__g, S, variables), filter(lambda v: (not truth_table.test(v) and not dont_care.test(v)),  range(truth_table.size()))):
                model.AddAtLeastOne(constraint_vars)
    model.Minimize(sum(variables))
    
    # solve problem
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = max_search_time
    solver.parameters.num_search_workers = threads 
    status = solver.Solve(model)
    res = []
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        for i in range(len(S)):
            if (solver.Value(variables[i])):
                a = S[i][0]
                u = S[i][1]
                clause = []
                for j in range(int(log2(truth_table.size()))):
                    if (u & 1) == 0:
                        clause.append((1 - 2 * (a & 1)) * (j + 1))
                    a >>= 1
                    u >>= 1
                res.append(clause)
    else:
        res.append([])
    return res