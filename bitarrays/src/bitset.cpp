#include "bitset.hpp"
#include <pybind11/pybind11.h>
#include <pybind11/operators.h>
#include <pybind11/stl.h>

namespace py = pybind11;
using namespace pybind11::literals;

BitSet::BitSet(const std::size_t size) : s(size), data((size >> 6U) + (((size % 64U) > 0) ? 1 : 0))
{
}

BitSet::BitSet(const BitSet &other) : s(other.s), data(other.data)
{
}

BitSet::~BitSet()
{
}

inline void BitSet::set(std::size_t index)
{
    assert(index < s);
    data[index >> 6ULL] |= 1ULL << (index % 64ULL);
}

inline void BitSet::unset(std::size_t index)
{
    assert(index < s);
    data[index >> 6ULL] &= ~(1ULL << (index % 64ULL));
}

inline bool BitSet::test(std::size_t index) const
{
    return (data[index >> 6ULL] & 1ULL << (index % 64ULL)) > 0;
}

bool BitSet::all() const
{
    std::size_t i;
    for (i = 0; i < data.size() - 1; i++)
    {
        if (data[i] != -1ULL)
            return false;
    }
    if (data[i] != (-1ULL & ((1ULL << (s % 64ULL)) - 1ULL)))
        return false;
    return true;
}

bool BitSet::any() const
{
    for (std::size_t i = 0; i < data.size(); i++)
    {
        if (data[i] > 0)
            return true;
    }
    return false;
}

bool BitSet::none() const
{
    for (std::size_t i = 0; i < data.size(); i++)
    {
        if (data[i] != 0)
            return false;
    }
    return true;
}

std::size_t BitSet::count() const
{
    std::size_t res = 0;
    for (std::size_t i = 0; i < data.size(); i++)
    {
        res += std::popcount(data[i]);
    }
    return res;
}

std::size_t BitSet::size() const
{
    return s;
}

void BitSet::fill()
{
    std::fill(data.begin(), data.end(), -1ULL);
}

void BitSet::clear()
{
    std::fill(data.begin(), data.end(), 0ULL);
}

void BitSet::flip()
{
    for (std::size_t i = 0; i < data.size(); i++)
    {
        data[i] ^= -1ULL;
    }
}

SuppIterator BitSet::supp() const
{
    return SuppIterator(this);
}

void BitSet::operator&=(const BitSet &other)
{
    assert(s == other.size());
    for (std::size_t i = 0; i < data.size(); i++)
    {
        data[i] &= other.data[i];
    }
}

void BitSet::operator|=(const BitSet &other)
{
    assert(s == other.size());
    for (std::size_t i = 0; i < data.size(); i++)
    {
        data[i] |= other.data[i];
    }
}

void BitSet::operator^=(const BitSet &other)
{
    assert(s == other.size());
    for (std::size_t i = 0; i < data.size(); i++)
    {
        data[i] ^= other.data[i];
    }
}

std::string BitSet::to_string(const char zero, const char one) const
{
    std::string res;
    std::size_t i = s;
    while (i != 0)
    {
        res += (test(--i)) ? one : zero;
    }

    return res;
}

inline std::string BitSet::to_onezero() const
{
    return to_string('0', '1');
}

void BitSet::join(const BitSet &other){
    data.reserve(data.size() + other.data.size());
    if (s == data.size()<<6)
    {
        data.insert(data.end(), other.data.begin(), other.data.end());
    }
    else
    {
        std::size_t shift = s % 64;
        for (std::size_t i=0; i < other.data.size() - 1; i++)
        {
            data.back() |= other.data[i]<<shift;
            data.push_back(other.data[i]>>shift);
        }
        data.back() |= other.data.back()<<shift;
        if ((s + other.s) > 64 && ((s + other.s)%64) > 0) data.push_back(other.data.back()>>shift);
    }
    s += other.s;
}

inline void BitSet::swap(const std::size_t mask) { transform<op::swap>(mask); }
inline void BitSet::XORup(const std::size_t mask) { transform<op::xor_up>(mask); }
inline void BitSet::XORdown(const std::size_t mask) { transform<op::xor_down>(mask); }
inline void BitSet::ORup(const std::size_t mask) { transform<op::or_up>(mask); }
inline void BitSet::ORdown(const std::size_t mask) { transform<op::or_down>(mask); }
inline void BitSet::LESSup(const std::size_t mask) { transform<op::less_up>(mask); }
inline void BitSet::MOREdown(const std::size_t mask) { transform<op::more_down>(mask); }

std::partial_ordering operator<=>(const BitSet &lhs, const BitSet &rhs)
{
    assert(lhs.data.size() == rhs.data.size());
    bool gt = false;
    bool lt = false;
    for (std::size_t i = 0; i < lhs.data.size(); i++)
    {
        if (lhs.data[i] != rhs.data[i])
        {
            if (((lhs.data[i] & ~rhs.data[i]) > 0))
                gt = true;
            else
                lt = true;
        }
    }
    if (gt && lt)
        return std::partial_ordering::unordered;
    if (gt)
        return std::partial_ordering::greater;
    if (lt)
        return std::partial_ordering::less;
    return std::partial_ordering::equivalent;
}

bool operator==(const BitSet &lhs, const BitSet &rhs)
{
    return lhs.data == rhs.data;
}

SuppIterator::SuppIterator(const BitSet *bitset) : bs(bitset)
{
}
std::size_t SuppIterator::next()
{
    while (((i64 << 6U) + i) < bs->size())
    {
        if (bs->data[i64] > 0)
        {
            while ((i < 64) && ((i64 << 6U) + i) < bs->size())
            {
                if (bs->test((i64 << 6U) + i))
                {
                    return (i64 << 6U) + i++;
                }
                i++;
            }
        }
        i = 0;
        i64++;
    }
    throw pybind11::stop_iteration();
}

PYBIND11_MODULE(bitset, m)
{
    m.doc() = "Dense bitsets implemented in C++"; // optional module docstring

    py::class_<SuppIterator>(m, "SuppIterator")
        .def("__next__", &SuppIterator::next);

    py::class_<BitSet>(m, "BitSet")
        .def(py::init<const std::size_t>())
        .def(py::init<const BitSet &>())
        .def("set", &BitSet::set)
        .def("unset", &BitSet::unset)
        .def("test", &BitSet::test)
        .def("all", &BitSet::all)
        .def("any", &BitSet::any)
        .def("none", &BitSet::none)
        .def("count", &BitSet::count)
        .def("size", &BitSet::size)
        .def("fill", &BitSet::fill)
        .def("clear", &BitSet::clear)
        .def("flip", &BitSet::flip)
        .def("__iter__", &BitSet::supp)
        .def("to_string", &BitSet::to_string)
        .def("join", &BitSet::join)
        .def("swap", &BitSet::swap, py::arg("mask") = -1ULL)
        .def("XORup", &BitSet::XORup, py::arg("mask") = -1ULL)
        .def("XORdown", &BitSet::XORdown, py::arg("mask") = -1ULL)
        .def("ORup", &BitSet::ORup, py::arg("mask") = -1ULL)
        .def("ORdown", &BitSet::ORdown, py::arg("mask") = -1ULL)
        .def("LESSup", &BitSet::LESSup, py::arg("mask") = -1ULL)
        .def("MOREdown", &BitSet::MOREdown, py::arg("mask") = -1ULL)
        .def(py::self &= py::self)
        .def(py::self |= py::self)
        .def(py::self ^= py::self)
        .def(py::self < py::self)
        .def(py::self <= py::self)
        .def(py::self > py::self)
        .def(py::self >= py::self)
        .def(py::self == py::self)
        .def("__str__", &BitSet::to_onezero)
        .def("__copy__", [](const BitSet &self)
             { return BitSet(self); })
        .def(
            "__deepcopy__", [](const BitSet &self, py::dict)
            { return BitSet(self); },
            "memo"_a)
        .def(py::pickle(
            [](const BitSet &bs) { // __getstate__
                /* Return a tuple that fully encodes the state of the object */
                return py::make_tuple(bs.s, bs.data);
            },
            [](py::tuple t) { // __setstate__
                if (t.size() != 2)
                    throw std::runtime_error("Invalid state!");

                /* Create a new C++ instance */
                BitSet bs(t[0].cast<std::size_t>());

                /* Assign any additional state */
                bs.data = t[1].cast<std::vector<uint64_t>>();

                return bs;
            }));
}