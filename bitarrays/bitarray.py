from bitarrays.bitset import BitSet
from functools import reduce

def to_index(pos, shape):
    if isinstance(pos, int):
        return pos
    i = 0
    for j in range(len(shape)):
        i += pos[j] * reduce(int.__mul__, shape[j+1:], 1)
    return i

def from_index(i, shape):
    pos = [0]*len(shape)
    for j in range(len(shape)):
        pos[j], i = divmod(i, reduce(int.__mul__, shape[j+1:], 1))
    return pos

def print_matrix(ba):
    s = str(ba)[::-1]
    smod = ""
    for i in range(ba.shape[0]):
        for j in range(ba.shape[1]):
            smod += s[to_index((i, j), ba.shape)]
        smod += "\n"
    print(smod)

class SuppBitArrayIterator:
    def __init__(self, iterator, shape):
        self.shape = shape
        self.iterator = iterator
    
    def __next__(self):
        try:
            return from_index(self.iterator.__next__(), self.shape)
        except StopIteration:
            raise StopIteration()

class BitArray(BitSet):

    def __init__(self, shape):
        super().__init__(reduce(int.__mul__, shape))
        self.shape = shape

    def set(self, pos):
        super().set(to_index(pos, self.shape))

    def unset(self, pos):
        super().unset(to_index(pos, self.shape))

    def test(self, pos):
        return super().test(to_index(pos, self.shape))

    def __iter__(self):
        return SuppBitArrayIterator(super().__iter__(), self.shape)

    def swap(self, dim, mask):
        super().swap((mask & (self.shape[dim]-1)) * (reduce(int.__mul__, self.shape[dim+1:], 1)))
    
    def XORup(self, dim, mask):
        super().XORup((mask & (self.shape[dim]-1)) * (reduce(int.__mul__, self.shape[dim+1:], 1)))

    def XORdown(self, dim, mask):
        super().XORdown((mask & (self.shape[dim]-1)) * (reduce(int.__mul__, self.shape[dim+1:], 1)))

    def ORup(self, dim, mask):
        super().ORup((mask & (self.shape[dim]-1)) * (reduce(int.__mul__, self.shape[dim+1:], 1)))

    def ORdown(self, dim, mask):
        super().ORdown((mask & (self.shape[dim]-1)) * (reduce(int.__mul__, self.shape[dim+1:], 1)))

    def LESSup(self, dim, mask):
        super().LESSup((mask & (self.shape[dim]-1)) * (reduce(int.__mul__, self.shape[dim+1:], 1)))

    def MOREdown(self, dim, mask):
        super().MOREdown((mask & (self.shape[dim]-1)) * (reduce(int.__mul__, self.shape[dim+1:], 1)))

    