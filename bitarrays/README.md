# bitarrays

A python interface to a C++ implementation of bitsets and bitarrays with multidimensional transforms, as in [Udovenko 2019](https://link.springer.com/chapter/10.1007/978-3-030-92062-3_12).

## compile

```sh
clang++ -O3 -Wall -shared -std=c++20 -DNDEBUG -march=native -funroll-loops -fvisibility=hidden -fPIC $(python -m pybind11 --includes) src/bitset.cpp -o bitset$(python3.11-config --extension-suffix)
```