from itertools import product
from cmath import isclose

_NOT_FOUND = object()


class cached_property:
    def __init__(self, func):
        self.func = func
        self.attrname = None
        self.__doc__ = func.__doc__

    def __set_name__(self, owner, name):
        self.attrname = name

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        if self.attrname is None:
            raise TypeError(
                "Cannot use cached_property instance without calling __set_name__ on it."
            )
        cache = instance.__dict__
        val = cache.get(self.attrname, _NOT_FOUND)
        if val is _NOT_FOUND:
            val = self.func(instance)
            cache[self.attrname] = val
        return val


class Vector:
    """Pure python basic R3 vector class designed for simple operations.

    Notes
    -----
    Instances of the Vector class are immutable.
    """

    def __init__(self, components):
        """Vector class constructor.

        Parameters
        ----------
        components : array-like
            An iterable with length equal to 3, corresponding to x, y and z
            components.
        """
        self.components = components

    def __getitem__(self, i):
        return self.components[i]

    def __len__(self):
        return 3

    @cached_property
    def x(self):
        """First component of the vector."""
        return self.components[0]

    @cached_property
    def y(self):
        """Second component of the vector."""
        return self.components[1]

    @cached_property
    def z(self):
        """Third component of the vector."""
        return self.components[2]

    @cached_property
    def unit_vector(self):
        """R3 vector with the same direction of self, but normalized."""
        return self / abs(self)

    @cached_property
    def cross_matrix(self):
        """Skew symmetric matrix used for cross product."""
        return Matrix(
            [[0, -self.z, self.y], [self.z, 0, -self.x], [-self.y, self.x, 0]]
        )

    def __abs__(self):
        """R3 vector norm, magnitude or absolute value."""
        return (self.x**2 + self.y**2 + self.z**2) ** 0.5

    def __neg__(self):
        """-1 times R3 vector self."""
        return Vector([-self.x, -self.y, -self.z])

    def __add__(self, other):
        """Sum two R3 vectors."""
        result = [self[i] + other[i] for i in range(3)]
        return Vector(result)

    def __radd__(self, other):
        """Sum two R3 vectors."""
        return self.__add__(other)

    def __sub__(self, other):
        """Subtract two R3 vectors."""
        result = [self[i] - other[i] for i in range(3)]
        return Vector(result)

    def __rsub__(self, other):
        """Subtract two R3 vectors."""
        result = [other[i] - self[i] for i in range(3)]
        return Vector(result)

    def __mul__(self, other):
        """Component wise multiplication between R3 vector and scalar other."""
        return self.__rmul__(other)

    def __rmul__(self, other):
        """Component wise multiplication between R3 vector and scalar other."""
        return Vector([other * self.x, other * self.y, other * self.z])

    def __truediv__(self, other):
        """Component wise division between R3 vector and scalar other."""
        return Vector([self.x / other, self.y / other, self.z / other])

    def __xor__(self, other):
        """Cross product between self and other."""
        x = self[1] * other[2] - self[2] * other[1]
        y = -self[0] * other[2] + self[2] * other[0]
        z = self[0] * other[1] - self[1] * other[0]
        return Vector([x, y, z])

    def __matmul__(self, other):
        """Dot product between two R3 vectors."""
        return sum([self[i] * other[i] for i in range(3)])

    def __rmatmul__(self, other):
        """Dot product between two R3 vectors."""
        return self.__matmul__(other)

    def __eq__(self, other):
        return (
            len(other) == 3
            and isclose(self.x, other[0])
            and isclose(self.y, other[1])
            and isclose(self.z, other[2])
        )

    def is_parallel_to(self, other):
        """Returns True if self is parallel to R3 vector other. False otherwise."""
        return isclose(self @ other, abs(self) * abs(other))

    def is_perpendicular_to(self, other):
        """Returns True if self is perpendicular to R3 vector other. False otherwise."""
        return isclose(self @ other, 0, rel_tol=0, abs_tol=1e-9)

    def element_wise(self, operation):
        """Element wise operation.

        Parameters
        ----------
        operation : callable
            Callable with a single argument, which should take an element and
            return the result of the desired operation.
        """
        return Vector([operation(self.x), operation(self.y), operation(self.z)])

    def dot(self, other):
        """Dot product between two R3 vectors."""
        return self.__matmul__(other)

    def cross(self, other):
        """Cross product between two R3 vectors."""
        return self.__xor__(other)

    def proj(self, other):
        """Scalar projection of R3 vector self onto R3 vector other."""
        return (self @ other) / abs(other)

    def __str__(self):
        return f"({self.x}, {self.y}, {self.z})"

    def __repr__(self):
        return f"Vector({self.x}, {self.y}, {self.z})"

    @staticmethod
    def zeros():
        return Vector([0, 0, 0])

    @staticmethod
    def i():
        return Vector([1, 0, 0])

    @staticmethod
    def j():
        return Vector([0, 1, 0])

    @staticmethod
    def k():
        return Vector([0, 0, 1])


class Matrix:
    """Pure Python 3x3 Matrix class for simple matrix-matrix and matrix-vector
    operations.

    Notes
    -----
    Instances of the Matrix class are immutable.
    """

    def __init__(self, components):
        """Matrix class constructor.

        Parameters
        ----------
        components : 3x3 array-like
            3x3 array-like with matrix components. Indexing must be
            [row, column].
        """
        self.components = components

    def __getitem__(self, args):
        if isinstance(args, int):
            return self.components[args]
        else:
            return self.components[args[0]][args[1]]

    def __len__(self):
        return 3

    @cached_property
    def shape(self):
        return (3, 3)

    @cached_property
    def xx(self):
        return self[0, 0]

    @cached_property
    def xy(self):
        return self[0, 1]

    @cached_property
    def xz(self):
        return self[0, 2]

    @cached_property
    def yx(self):
        return self[1, 0]

    @cached_property
    def yy(self):
        return self[1, 1]

    @cached_property
    def yz(self):
        return self[1, 2]

    @cached_property
    def zx(self):
        return self[2, 0]

    @cached_property
    def zy(self):
        return self[2, 1]

    @cached_property
    def zz(self):
        return self[2, 2]

    @cached_property
    def trace(self):
        """Matrix trace, sum of its diagonal components."""
        return self.xx + self.yy + self.zz

    @cached_property
    def transpose(self):
        """Matrix transpose."""
        return Matrix(
            [
                [self.xx, self.yx, self.zx],
                [self.xy, self.yy, self.zy],
                [self.xz, self.yz, self.zz],
            ]
        )

    @cached_property
    def det(self):
        return self.__abs__()

    @cached_property
    def is_diagonal(self, tol=1e-6):
        """Boolean indicating if matrix is diagonal.

        Parameters
        ----------
        tol : float, optional
            Tolerance used to determine if non-diagonal elements are negligible.
        """
        for i, j in product(range(3), range(3)):
            if i == j:
                continue
            if abs(self[i, j]) > tol:
                return False
        return True

    @cached_property
    def inverse(self):
        """Matrix inverse."""
        if self.is_diagonal:
            return Matrix(
                [[1 / self.xx, 0, 0], [0, 1 / self.yy, 0], [0, 0, 1 / self.zz]]
            )
        else:
            ixx = self.yy * self.zz - self.zy * self.yz
            iyx = self.zx * self.yz - self.yx * self.zz
            izx = self.yx * self.zy - self.zx * self.yy
            ixy = self.zy * self.xz - self.xy * self.zz
            iyy = self.xx * self.zz - self.zx * self.xz
            izy = self.zx * self.xy - self.xx * self.zy
            ixz = self.xy * self.yz - self.yy * self.xz
            iyz = self.yx * self.xz - self.yz * self.xx
            izz = self.xx * self.yy - self.yx * self.xy
            det = self.xx * ixx + self.xy * iyx + self.xz * izx
            return Matrix(
                [
                    [ixx / det, ixy / det, ixz / det],
                    [iyx / det, iyy / det, iyz / det],
                    [izx / det, izy / det, izz / det],
                ]
            )

    def __abs__(self):
        """Matrix determinant."""
        ixx = self.yy * self.zz - self.zy * self.yz
        iyx = self.zx * self.yz - self.yx * self.zz
        izx = self.yx * self.zy - self.zx * self.yy
        det = self.xx * ixx + self.xy * iyx + self.xz * izx
        return det

    def __neg__(self):
        """-1 times 3x3 matrix self."""
        return Matrix(
            [
                [-self.xx, -self.xy, -self.xz],
                [-self.yx, -self.yy, -self.yz],
                [-self.zx, -self.zy, -self.zz],
            ]
        )

    def __add__(self, other):
        """Sum two 3x3 matrices."""
        return Matrix(
            [
                [self.xx + other[0][0], self.xy + other[0][1], self.xz + other[0][2]],
                [self.yx + other[1][0], self.yy + other[1][1], self.yz + other[1][2]],
                [self.zx + other[2][0], self.zy + other[2][1], self.zz + other[2][2]],
            ]
        )

    def __radd__(self, other):
        """Sum two 3x3 matrices."""
        return self.__add__(other)

    def __sub__(self, other):
        """Subtract two 3x3 matrices."""
        return Matrix(
            [
                [self.xx - other[0][0], self.xy - other[0][1], self.xz - other[0][2]],
                [self.yx - other[1][0], self.yy - other[1][1], self.yz - other[1][2]],
                [self.zx - other[2][0], self.zy - other[2][1], self.zz - other[2][2]],
            ]
        )

    def __rsub__(self, other):
        """Subtract two 3x3 matrices."""
        return Matrix(
            [
                [other[0][0] - self.xx, other[0][1] - self.xy, other[0][2] - self.xz],
                [other[1][0] - self.yx, other[1][1] - self.yy, other[1][2] - self.yz],
                [other[2][0] - self.zx, other[2][1] - self.zy, other[2][2] - self.zz],
            ]
        )

    def __mul__(self, other):
        """Element wise multiplication of 3x3 matrix self by scalar other."""
        return Matrix(
            [
                [other * self.xx, other * self.xy, other * self.xz],
                [other * self.yx, other * self.yy, other * self.yz],
                [other * self.zx, other * self.zy, other * self.zz],
            ]
        )

    def __rmul__(self, other):
        """Element wise multiplication of 3x3 matrix self by scalar other."""
        return self.__mul__(other)

    def __truediv__(self, other):
        """Element wise division is carried out."""
        return Matrix(
            [
                [self.xx / other, self.xy / other, self.xz / other],
                [self.yx / other, self.yy / other, self.yz / other],
                [self.zx / other, self.zy / other, self.zz / other],
            ]
        )

    def __matmul__(self, other):
        """Dot product between two 3x3 matrices or between 3x3 matrix and R3
        vector."""
        try:
            result = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
            for i, j in product(range(3), range(3)):
                result[i][j] = Vector(self[i, :]) @ Vector(
                    [other[0][j], other[1][j], other[2][j]]
                )
            return Matrix(result)
        except (TypeError, IndexError):
            return Vector([Vector(self[i, :]) @ other for i in range(3)])

    def __rmatmul__(self, other):
        """Dot product between two 3x3 matrices or between 3x3 matrix and R3
        vector."""
        result = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        for i, j in product(range(3), range(3)):
            result[i][j] = Vector([other[i][0], other[i][1], other[i][2]]) @ Vector(
                [self[0][j], self[1][j], self[2][j]]
            )
        return Matrix(result)

    def __pow__(self, other):
        """Exponentiation of 3x3 matrix by integer other."""
        result = Matrix.identity()
        for i in range(other):
            result = self @ result
        return result

    def __eq__(self, other):
        return (
            len(other) == 3
            and isclose(self.xx, other[0][0], abs_tol=1e-9)
            and isclose(self.xy, other[0][1], abs_tol=1e-9)
            and isclose(self.xz, other[0][2], abs_tol=1e-9)
            and isclose(self.yx, other[1][0], abs_tol=1e-9)
            and isclose(self.yy, other[1][1], abs_tol=1e-9)
            and isclose(self.yz, other[1][2], abs_tol=1e-9)
            and isclose(self.zx, other[2][0], abs_tol=1e-9)
            and isclose(self.zy, other[2][1], abs_tol=1e-9)
            and isclose(self.zz, other[2][2], abs_tol=1e-9)
        )

    def element_wise(self, operation):
        """Element wise operation.

        Parameters
        ----------
        operation : callable
            Callable with a single argument, which should take an element and
            return the result of the desired operation.
        """
        return Matrix(
            [
                [operation(self.xx), operation(self.xy), operation(self.xz)],
                [operation(self.yx), operation(self.yy), operation(self.yz)],
                [operation(self.zx), operation(self.zy), operation(self.zz)],
            ]
        )

    def dot(self, other):
        """Dot product between two 3x3 matrices or between 3x3 matrix and R3
        vector."""
        return self.__matmul__(other)

    def __str__(self):
        return (
            f"[{self.xx}, {self.xy}, {self.xz}]\n"
            + f"[{self.yx}, {self.yy}, {self.yz}]\n"
            + f"[{self.zx}, {self.zy}, {self.zz}]]"
        )

    def __repr__(self):
        return (
            f"Matrix([{self.xx}, {self.xy}, {self.xz}],\n"
            + f"       [{self.yx}, {self.yy}, {self.yz}],\n"
            + f"       [{self.zx}, {self.zy}, {self.zz}])"
        )

    @staticmethod
    def identity():
        return Matrix([[1, 0, 0], [0, 1, 0], [0, 0, 1]])

    @staticmethod
    def zeros():
        return Matrix([[0, 0, 0], [0, 0, 0], [0, 0, 0]])
