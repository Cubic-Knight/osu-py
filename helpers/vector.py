from itertools import zip_longest

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
