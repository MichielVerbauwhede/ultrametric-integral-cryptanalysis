#include "present.h"
#include <iostream>

int valuation(unsigned int v)
{
    float f = (float)(v & -v); // cast the least significant bit in v to a float
    return (*(uint32_t *)&f >> 23) - 0x7f;
}

void check_5rounds(uint8_t roundKeys[max_rounds][roundKeySize], size_t* count)
{
    // Input set: Prec(0x000000000000fff0)
    for(int x0 = 0; x0 < 1<<12; ++x0) {
        uint8_t block[blockSize] {0};
        block[0] = (x0>>4) & 0xf0;
        block[1] = x0;
        encryptPlain(block, 5, roundKeys);
        for (size_t i = 0; i < 8; i++)
        {
            for (size_t j = 0; j < 8; j++)
            {
                count[8*i+j] += (block[i]>>j) & 0x1;
            }
        }
    }
}

int main(int argc, char** argv)
{
    const size_t nb_experiments = 1<<16;

    size_t res[64][14] = {};
    for(size_t n = 0; n < nb_experiments; ++n) {
        std::srand(n);
        uint8_t roundKeys[max_rounds][roundKeySize], key[keySize];
        for(std::size_t i = 0; i <= max_rounds; ++i) {
            for(std::size_t j = 0; j < roundKeySize; ++j)
                roundKeys[i][j] = rand() % 256;
        }
        size_t count[64] = {};
        check_5rounds(roundKeys, count);
        for (size_t i = 0; i < 64; i++)
        {   
            int v = valuation(count[i]);
            res[i][(v >=0 && v < 13) ? v : 13]++;
        }
    }
    for (size_t i = 0; i < 64; i++)
    {
        for (size_t j = 0; j < 14; j++)
        {
            std::cout << res[i][j] << " ";
        }
        std::cout << std::endl;
    }
}