from .CompoundFunction import CompoundFunction, INPUT_ID, OUTPUT_ID, ERROR_ID
from .Components import XOR

def construct_iterated_cipher(rounds, key_masks):
    assert(len(rounds)+1 == len(key_masks))
    input_sizes = [r.input_size for r in rounds] + [rounds[-1].output_size]
    f = CompoundFunction(input_sizes[0], input_sizes[-1])
    idc = INPUT_ID
    for i in range(len(rounds)+1):
        idp = idc
        km = key_masks[i]
        idx = [f.add_component(XOR) if ((km >> j) & 1) == 1 else ERROR_ID for j in range(input_sizes[i])]
        if i < len(rounds):
            idc = f.add_component(rounds[i])
        else:
            idc = OUTPUT_ID
        for j in range(input_sizes[i]):
            if idx[j] == ERROR_ID:
                f.connect_components(idp, j, idc, j)
            else:
                f.connect_components(idp, j, idx[j], 0)
                f.connect_to_key(idx[j], 1)
                f.connect_components(idx[j], 0, idc, j)
    return f