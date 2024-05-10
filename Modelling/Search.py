from multiprocessing import Pool
from functools import partial, reduce
from itertools import product

def search_simple_properties_mod_2(test, input_size, output_size, is_permutation, num_threads=1):
    # test returns true if the sum is non-zero
    invmask = 2**input_size - 1
    input_modifiers = tuple((1<<x) ^ invmask for x in range(input_size))
    output_modifiers = tuple(1<<x for x in range(output_size))
    
    Bi = [set()]
    with Pool(num_threads) as pool:
        while len(Bi) == 1 or len(Bi[-1]) > 0:
            if len(Bi) == 1 and not is_permutation:
                to_test = [(invmask, x) for x in output_modifiers]
            elif len(Bi) == 1 and is_permutation:
                Bi.append(set())
                to_test = list(product(input_modifiers, output_modifiers))
            else:
                to_test = set()
                for u1, v1 in Bi[-1]:
                    for u2 in input_modifiers:
                        u = u1 & u2
                        if (u ^ invmask).bit_count() + v1.bit_count() == len(Bi):
                            flag = True
                            for u3 in input_modifiers:
                                if ((u | u3) ^ invmask) > 0 and not (u^u3^invmask, v1) in Bi[-1]:
                                    flag = False
                                    break
                            if flag:
                                to_test.add((u, v1))
                    for v2 in output_modifiers:
                        v = v1 | v2
                        if (u1 ^ invmask).bit_count() + v.bit_count() == len(Bi):
                            flag = True
                            for v3 in output_modifiers:
                                if (v & v3) > 0 and not (u1, v^v3) in Bi[-1]:
                                    flag = False
                                    break
                            if flag:
                                to_test.add((u1, v))
                to_test = list(to_test)
            Bi.append(set())
            for uv, nonzero in zip(to_test, pool.starmap(test, to_test, 1)):
                if not nonzero:
                    Bi[-1].add(uv)

    return reduce(set.union, Bi, set())