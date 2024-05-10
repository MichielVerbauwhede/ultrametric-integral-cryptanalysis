from LogicOptimisation.QMC import QMC_optimise_CNF, QMC_THREADS
from bitarrays import bitarray
from bitarrays.bitarray import BitArray
from bitarrays.bitset import BitSet
import numpy as np
from functools import partialmethod, reduce
from math import log2, inf

def transition_matrix(f, input_size, output_size):
    res = BitArray((2**output_size, 2**input_size))
    for i in range(2**input_size):
        res.set((f(i), i))
    return res

def ANF_matrix(f, input_size, output_size):
    res = transition_matrix(f, input_size, output_size)
    res.XORdown(0, -1)
    res.XORup(1, -1)
    return res

def ANF_prop_table(F, input_mask, output_mask):
    res = ANF_matrix(lambda x: F(x), F.input_size, F.output_size)
    res.ORup(0, output_mask)
    res.ORdown(1, input_mask)
    return res

def compute_parity_propagation_model(F, input_mask, output_mask):
    m = ANF_prop_table(F, input_mask, output_mask)
    dont_care = BitSet(2**(F.input_size + F.output_size))
    return QMC_optimise_CNF(m, dont_care)

def UT_matrix(f, input_size, output_size):
    def row_transform(M):
        ns = M.shape[0] // 2
        if ns > 0:
            x = row_transform(M[:ns, :])
            y = row_transform(M[ns:, :])
        else:
            return M
        return np.vstack([x+y, y])

    def column_transform(M):
        ns = M.shape[1] // 2
        if ns > 0:
            x = column_transform(M[:, :ns])
            y = column_transform(M[:, ns:])
        else:
            return M
        return np.hstack([x, y-x])

    # Transition matrix over the natural numbers
    res = np.zeros((2**output_size, 2**input_size), dtype='longlong')
    for i in range(2**input_size):
        res[f(i), i] = 1
    res = row_transform(res)
    res = column_transform(res)

    return res

def to_ord(v):
    if v == 0:
        return inf
    return log2(int(abs(v)) & (-int(abs(v))))

def compute_UT_propagation_model(F):
    
    ov = np.vectorize(to_ord)
    M = UT_matrix(F, F.input_size, F.output_size)
    M_ord = ov(M)
    n_extra_vars = int(np.max(np.ma.masked_invalid(M_ord)))

    m = BitSet(2**(F.input_size + F.output_size + n_extra_vars))
    for j in range(2**F.output_size):
        for i in range(2**F.input_size):
            if M_ord[j, i] != inf:
                m.set(((2**int(M_ord[j, i])-1)<<(F.input_size+F.output_size)) + (j << F.input_size) + i)

    dont_care = BitSet(2**(F.input_size + F.output_size + n_extra_vars))
    return QMC_optimise_CNF(m, dont_care), n_extra_vars # variables are in order of input, output, power vars, also returns the number of variables used to model the power