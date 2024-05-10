from .CompoundFunction import CompoundFunction, INPUT_ID, OUTPUT_ID
from .Components import get_COPYn, get_XORn, Component
from galois import GF, GF2
from numpy import matmul

def convert_to_F2_matrix(mat):
    res = GF2.Zeros((mat.shape[0]*mat._degree, mat.shape[1]*mat._degree))
    Field = GF(mat._order)
    for i in range(mat.shape[1]):
        for j in range(mat._degree):
            x = Field.Zeros((mat.shape[0], 1))
            x[i, 0] = Field(1<<j)
            v = matmul(mat, x)
            for a in range(mat.shape[0]):
                for b in range(mat._degree):
                    res[mat._degree*a+b, mat._degree*i+j] = (int(v[a])>>b)&1
    return res

class Linear(Component):
    def __init__(self, mat):
        if mat._degree == 1:
            self.mat = mat
        else:
            self.mat = convert_to_F2_matrix(mat)
        super().__init__(self.mat.shape[1], self.mat.shape[0])

    def __call__(self, v, key=0):
        x = GF2([[(v >> i) & 1] for i in range(self.input_size)])
        y = matmul(self.mat, x)
        res = 0
        for i in range(self.output_size):
            res <<= 1
            if y[self.output_size-1-i]:
                res += 1
        return res

def linear_to_compound_COPY_XOR(f):
    Lc = CompoundFunction(f.input_size, f.output_size)
    cids=[]
    cnis=[]
    for i in range(f.input_size):
        ni = 0
        for j in range(f.output_size):
            if f.mat[j, i] == 1:
                ni += 1
        cids.append(Lc.add_component(get_COPYn(ni)))
        Lc.connect_components(INPUT_ID, i, cids[-1], 0)
        cnis.append(0)
    for i in range(f.output_size):
        ni = 0
        for j in range(f.input_size):
            if f.mat[i, j] == 1:
                ni += 1
        idl = Lc.add_component(get_XORn(ni))
        l = 0
        for j in range(f.input_size):
            if f.mat[i, j] == 1:
                Lc.connect_components(cids[j], cnis[j], idl, l)
                cnis[j]+=1
                l+=1
        Lc.connect_components(idl, 0, OUTPUT_ID, i)
    return Lc
