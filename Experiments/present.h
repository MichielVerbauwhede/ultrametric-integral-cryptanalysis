#include <cstring>
#include <cstdlib>
#include <cstdint>
#include <cmath>
#include <iostream>

constexpr std::size_t nbSboxes = 16;//4;

constexpr std::size_t blockSize = 4 * nbSboxes / 8;
std::size_t rounds = 5;
constexpr std::size_t max_rounds = 10;

// Keys: always the same as for PRESENT-80
constexpr std::size_t keySize = 10; // In bytes
constexpr std::size_t roundKeySize = 8; // In bytes

constexpr std::size_t roundKeyOffset = roundKeySize - blockSize;

using std::uint8_t;

constexpr uint8_t sBox[16] = {
    0xC, 0x5, 0x6, 0xB, 0x9, 0x0, 0xA, 0xD, 0x3, 0xE, 0xF, 0x8, 0x4, 0x7, 0x1, 0x2
};

constexpr uint8_t sBoxInv[16] = {
    0x5, 0xE, 0xF, 0x8, 0xC, 0x1, 0x2, 0xD, 0xB, 0x4, 0x6, 0x3, 0x0, 0x7, 0x9, 0xA
};

void fillRoundKeys(const uint8_t* givenKey, uint8_t roundKeys[max_rounds][roundKeySize])
{
    uint8_t key[keySize];
    uint8_t newKey[keySize];
    memcpy(key, givenKey, keySize);
    memcpy(roundKeys[0], key, roundKeySize);

    for(uint8_t i = 1; i < rounds; ++i) {
        // Rotate left 61 bits
        for(uint8_t j = 0; j < keySize; ++j)
            newKey[j] = (key[(j + 7) % keySize] << 5) | (key[(j + 8) % keySize] >> 3);
        memcpy(key, newKey, keySize);
        // Pass leftmost 4 bits through sBox
        key[0] = (sBox[key[0] >> 4] << 4) | (key[0] & 0xF);
        // XOR round counter into bits 15 through 19
        key[8] ^= i << 7; // bit 15
        key[7] ^= i >> 1; // bits 19-16
        memcpy(roundKeys[i], key, roundKeySize);
    }
}

void xorRoundKey(uint8_t* block, uint8_t* roundKey)
{
    for(std::size_t i = 0; i < blockSize; ++i)
        block[i] ^= roundKey[roundKeyOffset + i];
}

void xorRoundKeyNoOffset(uint8_t* block, uint8_t* roundKey)
{
    for(std::size_t i = 0; i < blockSize; ++i)
        block[i] ^= roundKey[i];
}

void sBoxLayer(uint8_t* block) {
    for(std::size_t i = 0; i < blockSize; ++i)
        block[i] = (sBox[block[i] >> 4] << 4) | sBox[block[i] & 0xF];
}

void sBoxLayerInv(uint8_t* block) {
    for(std::size_t i = 0; i < blockSize; ++i)
        block[i] = (sBoxInv[block[i] >> 4] << 4) | sBoxInv[block[i] & 0xF];
}

void pLayer(uint8_t* block) {
    uint8_t initial[blockSize];
    memcpy(initial, block, blockSize);
    memset(block, 0, blockSize);
    const std::size_t modulus = 4 * nbSboxes - 1;

    for(std::size_t i = 0; i < 8 * blockSize; ++i) {
        const std::size_t j = (i == modulus) ? i : (nbSboxes * i) % modulus;
        //const uint8_t bit = (initial[blockSize - i / 8 - 1] >> (i % 8)) & 0x1;
        //block[blockSize - j / 8 - 1] |= bit << (j % 8);
        const uint8_t bit = (initial[i / 8] >> (i % 8)) & 0x1;
        block[j / 8] |= bit << (j % 8);
    }
}

void pLayerInv(uint8_t* block) {
    uint8_t initial[blockSize];
    memcpy(initial, block, blockSize);
    memset(block, 0, blockSize);
    const std::size_t modulus = 4 * nbSboxes - 1;

    for(std::size_t i = 0; i < 8 * blockSize; ++i) {
        const std::size_t j = (i == modulus) ? i : (4 * i) % modulus;
        const uint8_t bit = (initial[blockSize - i / 8 - 1] >> (i % 8)) & 0x1;
        block[blockSize - j / 8 - 1] |= bit << (j % 8);
    }
}

void encryptPlain(uint8_t* block, size_t rounds, uint8_t roundKeys[max_rounds][roundKeySize])
{
    for(std::size_t i = 0; i < rounds; ++i) {
        xorRoundKey(block, roundKeys[i]);
        sBoxLayer(block);
        pLayer(block);
    }
    //sBoxLayer(block);
    xorRoundKey(block, roundKeys[rounds]);
}

void encrypt(uint8_t* block, const uint8_t* key)
{
    uint8_t roundKeys[rounds][roundKeySize];
    fillRoundKeys(key, roundKeys);
    encryptPlain(block, rounds, roundKeys);
}

void fillRandom(uint8_t roundKeys[max_rounds][roundKeySize]) {
    for(std::size_t i = 0; i < rounds; ++i) {
        for(std::size_t j = 0; j < roundKeySize; ++j)
            roundKeys[i][j] = rand() % 256;
    }
}
