#pragma once

#include <vector>
#include <compare>
#include <cstdint>
#include <string>
#include <cassert>
#include <bit>

enum class op
{
    swap,
    xor_up,
    xor_down,
    or_up,
    or_down,
    less_up,
    more_down
};

class BitSet;

class SuppIterator
{
private:
    std::size_t i64=0;
    std::size_t i=0;
    const BitSet* bs;
public:
    SuppIterator(const BitSet* bs);
    std::size_t next();
};

class BitSet
{
public:
    std::size_t s;
    std::vector<uint64_t> data;
    BitSet(const std::size_t size);
    BitSet(const BitSet &other);
    ~BitSet();
    void set(const std::size_t index);
    void unset(const std::size_t index);
    bool test(const std::size_t index) const;
    bool all() const;
    bool any() const;
    bool none() const;
    std::size_t count() const;
    std::size_t size() const;
    void fill();
    void clear();
    void flip();
    SuppIterator supp() const;
    void operator&=(const BitSet &other);
    void operator|=(const BitSet &other);
    void operator^=(const BitSet &other);
    std::string to_string(const char zero, const char one) const;
    std::string to_onezero() const;
    void join(const BitSet &other);
   
    template <op OP>
    void transform(const std::size_t mask=-1ULL);
    void swap(const std::size_t mask=-1ULL);
    void XORup(const std::size_t mask=-1ULL);
    void XORdown(const std::size_t mask=-1ULL);
    void ORup(const std::size_t mask=-1ULL);
    void ORdown(const std::size_t mask=-1ULL);
    void LESSup(const std::size_t mask=-1ULL);
    void MOREdown(const std::size_t mask=-1ULL);
};

std::partial_ordering operator<=>(const BitSet &lhs, const BitSet &rhs);
bool operator==(const BitSet &lhs, const BitSet &rhs);

template <op OP>
void BitSet::transform(const std::size_t mask)
{
    assert(s == (1ULL << (std::bit_width(s) - 1)));
    std::size_t mm = (1ULL << (std::bit_width(s) - 1)) - 1;
    if (mm & mask & 1ULL)
    {
        constexpr std::size_t shft = 1;
        constexpr std::size_t m = 0x5555555555555555ULL;
        if (OP == op::swap)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] = ((data[i] >> shft) & m) | ((data[i] & m) << shft);
        if (OP == op::xor_up)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] ^= (data[i] & m) << shft;
        if (OP == op::xor_down)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] ^= (data[i] >> shft) & m;
        if (OP == op::or_up)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] |= (data[i] & m) << shft;
        if (OP == op::or_down)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] |= (data[i] >> shft) & m;
        if (OP == op::less_up)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] &= m | (((data[i] ^ m) & m) << shft);
        if (OP == op::more_down)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] &= (~m) | (((data[i] >> shft) ^ m) & m);
    }
    if (mm & mask & 2ULL)
    {
        constexpr std::size_t shft = 2;
        constexpr std::size_t m = 0x3333333333333333ULL;
        if (OP == op::swap)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] = ((data[i] >> shft) & m) | ((data[i] & m) << shft);
        if (OP == op::xor_up)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] ^= (data[i] & m) << shft;
        if (OP == op::xor_down)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] ^= (data[i] >> shft) & m;
        if (OP == op::or_up)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] |= (data[i] & m) << shft;
        if (OP == op::or_down)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] |= (data[i] >> shft) & m;
        if (OP == op::less_up)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] &= m | (((data[i] ^ m) & m) << shft);
        if (OP == op::more_down)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] &= (~m) | (((data[i] >> shft) ^ m) & m);
    }
    if (mm & mask & 4ULL)
    {
        constexpr std::size_t shft = 4;
        constexpr std::size_t m = 0x0f0f0f0f0f0f0f0fULL;
        if (OP == op::swap)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] = ((data[i] >> shft) & m) | ((data[i] & m) << shft);
        if (OP == op::xor_up)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] ^= (data[i] & m) << shft;
        if (OP == op::xor_down)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] ^= (data[i] >> shft) & m;
        if (OP == op::or_up)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] |= (data[i] & m) << shft;
        if (OP == op::or_down)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] |= (data[i] >> shft) & m;
        if (OP == op::less_up)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] &= m | (((data[i] ^ m) & m) << shft);
        if (OP == op::more_down)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] &= (~m) | (((data[i] >> shft) ^ m) & m);
    }
    if (mm & mask & 8ULL)
    {
        constexpr std::size_t shft = 8;
        constexpr std::size_t m = 0x00ff00ff00ff00ffULL;
        if (OP == op::swap)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] = ((data[i] >> shft) & m) | ((data[i] & m) << shft);
        if (OP == op::xor_up)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] ^= (data[i] & m) << shft;
        if (OP == op::xor_down)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] ^= (data[i] >> shft) & m;
        if (OP == op::or_up)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] |= (data[i] & m) << shft;
        if (OP == op::or_down)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] |= (data[i] >> shft) & m;
        if (OP == op::less_up)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] &= m | (((data[i] ^ m) & m) << shft);
        if (OP == op::more_down)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] &= (~m) | (((data[i] >> shft) ^ m) & m);
    }
    if (mm & mask & 16ULL)
    {
        constexpr std::size_t shft = 16;
        constexpr std::size_t m = 0x0000ffff0000ffffULL;
        if (OP == op::swap)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] = ((data[i] >> shft) & m) | ((data[i] & m) << shft);
        if (OP == op::xor_up)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] ^= (data[i] & m) << shft;
        if (OP == op::xor_down)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] ^= (data[i] >> shft) & m;
        if (OP == op::or_up)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] |= (data[i] & m) << shft;
        if (OP == op::or_down)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] |= (data[i] >> shft) & m;
        if (OP == op::less_up)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] &= m | (((data[i] ^ m) & m) << shft);
        if (OP == op::more_down)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] &= (~m) | (((data[i] >> shft) ^ m) & m);
    }
    if (mm & mask & 32ULL)
    {
        constexpr std::size_t shft = 32;
        constexpr std::size_t m = 0x00000000ffffffffULL;
        if (OP == op::swap)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] = ((data[i] >> shft) & m) | ((data[i] & m) << shft);
        if (OP == op::xor_up)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] ^= (data[i] & m) << shft;
        if (OP == op::xor_down)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] ^= (data[i] >> shft) & m;
        if (OP == op::or_up)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] |= (data[i] & m) << shft;
        if (OP == op::or_down)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] |= (data[i] >> shft) & m;
        if (OP == op::less_up)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] &= m | (((data[i] ^ m) & m) << shft);
        if (OP == op::more_down)
            for (std::size_t i = 0; i < data.size(); i++)
                data[i] &= (~m) | (((data[i] >> shft) ^ m) & m);
    }
    const std::size_t N = std::max(6, ((int) std::bit_width(s) - 1));
    for (std::size_t i = 0; i < N - 6U; i++)
    {
        if ((mask >> (i + 6U)) & 1U)
        {
            if (OP == op::swap)
            {
                uint64_t temp;
                for (std::size_t j = 0; j < data.size(); j += (1U << (i + 1)))
                {
                    for (std::size_t k = j; k < j + (1ULL << i); k++)
                    {
                        temp = data[k];
                        data[k] = data[k + (1ULL << i)];
                        data[k + (1ULL << i)] = temp;
                    }
                }
            }
            if (OP == op::xor_up)
                for (std::size_t j = 0; j < data.size(); j += (1U << (i + 1)))
                    for (std::size_t k = j; k < j + (1ULL << i); k++)
                        data[k + (1ULL << i)] ^= data[k];
            if (OP == op::xor_down)
                for (std::size_t j = 0; j < data.size(); j += (1U << (i + 1)))
                    for (std::size_t k = j; k < j + (1ULL << i); k++)
                        data[k] ^= data[k + (1ULL << i)];
            if (OP == op::or_up)
                for (std::size_t j = 0; j < data.size(); j += (1U << (i + 1)))
                    for (std::size_t k = j; k < j + (1ULL << i); k++)
                        data[k + (1ULL << i)] |= data[k];
            if (OP == op::or_down)
                for (std::size_t j = 0; j < data.size(); j += (1U << (i + 1)))
                    for (std::size_t k = j; k < j + (1ULL << i); k++)
                        data[k] |= data[k + (1ULL << i)];
            if (OP == op::less_up)
                for (std::size_t j = 0; j < data.size(); j += (1U << (i + 1)))
                    for (std::size_t k = j; k < j + (1ULL << i); k++)
                        data[k + (1ULL << i)] &= ~(data[k]);
            if (OP == op::more_down)
                for (std::size_t j = 0; j < data.size(); j += (1U << (i + 1)))
                    for (std::size_t k = j; k < j + (1ULL << i); k++)
                        data[k] &= ~(data[k + (1ULL << i)]);
        }
    }
}

