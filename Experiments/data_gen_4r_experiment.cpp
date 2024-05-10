#include "present.h"
#include <iostream>

void check_4rounds(uint8_t roundKeys[max_rounds][roundKeySize], size_t* count)
{
    // Input set: Prec(0x000000000000000f)
    for(int x0 = 0; x0 < 16; ++x0) {
        uint8_t block[blockSize] {0};
        block[0] = x0;
        encryptPlain(block, 4, roundKeys);
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

    size_t res[64][17] = {};
    std::srand(0);
    for(size_t n = 0; n < nb_experiments; ++n) {
        uint8_t roundKeys[max_rounds][roundKeySize], key[keySize];
        for(std::size_t i = 0; i <= max_rounds; ++i) {
            for(std::size_t j = 0; j < roundKeySize; ++j)
                roundKeys[i][j] = std::rand() % 256;
        }
        size_t count[64] = {};
        check_4rounds(roundKeys, count);
        for (size_t i = 0; i < 64; i++)
        {
            res[i][count[i]]++;
        }
    }
    for (size_t i = 0; i < 64; i++)
    {
        for (size_t j = 0; j < 17; j++)
        {
            std::cout << res[i][j] << " ";
        }
        std::cout << std::endl;
    }
}