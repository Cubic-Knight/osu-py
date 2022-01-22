from itertools import zip_longest
from typing import Tuple
from math import isclose

class Vector(tuple):
    def __new__(cls, *args):
        if len(args) == 1 and not isinstance(args[0], (int, float)):
            args = args[0]
        if not all(isinstance(e, (int, float)) for e in args):
            raise TypeError("Vector can only contain ints or floats")
        return super().__new__(cls, args)

    def __add__(self, other):
        if not isinstance(other, tuple):
            raise TypeError(f"can't add 'Vector' and '{type(other).__name__}'")
        return Vector( [a+b for a, b in zip_longest(self, other, fillvalue=0)] )

    def __sub__(self, other):
        if not isinstance(other, tuple):
            raise TypeError(f"can't subtract 'Vector' by '{type(other).__name__}'")
        return Vector( [a-b for a, b in zip_longest(self, other, fillvalue=0)] )

    def __neg__(self):
        return Vector( [-a for a in self] )

    def __mul__(self, other):
        if not isinstance(other, (int, float)):
            raise TypeError(f"can't multiply 'Vector' by '{type(other).__name__}'")
        return Vector( [a*other for a in self] )

    def __truediv__(self, other):
        if not isinstance(other, (int, float)):
            raise TypeError(f"can't divide 'Vector' by '{type(other).__name__}'")
        return Vector( [a/other for a in self] )

    def __radd__(self, other): return self + other
    def __iadd__(self, other): return self + other
    def __rsub__(self, other): return (-self) + other
    def __isub__(self, other): return self - other
    def __rmul__(self, other): return self * other
    def __imul__(self, other): return self * other
    def __itruediv__(self, other): return self / other


class CartesianLine:
    def __init__(self, a: float, b: float, c: float):
        self.a = a
        self.b = b
        self.c = c

    @classmethod
    def from_two_points(cls, p1: Tuple[float, float], p2: Tuple[float, float]):
        a = p2[1] - p1[1]
        b = p1[0] - p2[0]
        c = -a*p1[0] - b*p1[1]
        return cls(a, b, c)

    @classmethod
    def as_perp_bis_of_two_points(cls, p1: Vector, p2: Vector):
        x, y = (p1+p2) / 2  # Compute position of the point in the middle of p1 and p2
        a, b = p2 - p1
        c = -a*x - b*y
        return cls(a, b, c)

    def is_parallel_with(self, other):
        if not isinstance(other, CartesianLine): return NotImplemented
        return isclose(self.a * other.b, other.a * self.b)

    def intersection_point(self, other):
        if not isinstance(other, CartesianLine):  return NotImplemented
        if self.is_parallel_with(other): return None
        x = (self.b * other.c - other.b * self.c) / (self.a * other.b - other.a * self.b)
        y = (self.c * other.a - other.c * self.a) / (self.a * other.b - other.a * self.b)
        return Vector(x, y)
