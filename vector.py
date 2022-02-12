from math import pi, asin, acos


class Vector:
    cos: float
    sin: float
    len: float

    # creating vector
    def __init__(self, x, y):
        self.len = (x ** 2 + y ** 2) ** (1 / 2)  # Pythagoras
        try:  # a piece from trigonometry to configure direction
            self.cos = x / self.len
            self.sin = y / self.len
        except ZeroDivisionError:  # even math isn't perfect
            self.sin = 0
            self.cos = 1

    def __add__(self, v2):
        if type(v2) == type(self):
            return Vector((self.x() + v2.x()), (self.y() + v2.y()))

    def __mul__(self, other):
        if type(other) in (int, float):
            return Vector(self.x() * other, self.y() * other)

    @staticmethod
    def __module(__x):
        if __x < 0: __x *= -1
        return __x

    def radians(self):
        if self.len == 0: return 0
        d = [asin(self.sin),
             pi - asin(self.sin),
             acos(self.cos),
             2 * pi - acos(self.cos)]
        diffs = []
        for it in range(len(d)):
            test = d[it]
            if test < 0: test += 2 * pi
            for ir in range(len(d[it + 1:])):
                ref = d[it + 1:][ir]
                if ref < 0: ref += 2 * pi
                diffs.append(self.__module(test - ref))
        d = d[[0, 0, 0, 1, 1, 2][diffs.index(min(diffs))]]
        if d < 0: d += 2 * pi
        return d

    def degrees(self):
        return (self.radians() * 180) / pi

    def x(self):
        return self.cos * self.len

    def y(self):
        return self.sin * self.len
