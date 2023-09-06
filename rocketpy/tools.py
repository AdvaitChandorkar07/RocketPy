import importlib
from bisect import bisect_left
from cmath import isclose
from itertools import product

import pytz
from cftime import num2pydate

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
    Real and complex components are supported.

    Examples
    --------
    Creating a Vector instance requires passing its components as an iterable:
    >>> v = Vector([1, 2, 3])
    >>> v
    Vector(1, 2, 3)

    Vector components can be accessed by x, y and z or by indexing:
    >>> v.x, v.y, v.z
    (1, 2, 3)
    >>> v[0], v[1], v[2]
    (1, 2, 3)

    Vector instances can be added, subtracted, multiplied by a scalar, divided
    by a scalar, negated, and cross and dot product can be computed:
    >>> v + v
    Vector(2, 4, 6)
    >>> v - v
    Vector(0, 0, 0)
    >>> v * 2
    Vector(2, 4, 6)
    >>> v / 2
    Vector(0.5, 1.0, 1.5)
    >>> -v
    Vector(-1, -2, -3)
    >>> v @ v # Dot product
    14

    Cross products need to be wrapped in parentheses to ensure the ^ operator
    precedence:
    >>> (v ^ v)
    Vector(0, 0, 0)

    Vector instances can be called as functions if their elements are callable:
    >>> v = Vector([lambda x: x**2, lambda x: x**3, lambda x: x**4])
    >>> v(2)
    Vector(4, 8, 16)

    Vector instances magnitudes can be accessed as its absolute value:
    >>> v = Vector([1, 2, 3])
    >>> abs(v)
    3.7416573867739413

    Vector instances can be normalized:
    >>> v.unit_vector
    Vector(0.2672612419124244, 0.5345224838248488, 0.8017837257372732)

    Vector instances can be compared for equality:
    >>> v = Vector([1, 2, 3])
    >>> u = Vector([1, 2, 3])
    >>> v == u
    True
    >>> v != u
    False

    And last, but not least, it is also possible to check if two vectors are
    parallel or orthogonal:
    >>> v = Vector([1, 2, 3])
    >>> u = Vector([2, 4, 6])
    >>> v.is_parallel_to(u)
    True
    >>> v.is_orthogonal_to(u)
    False
    """

    __array_ufunc__ = None

    def __init__(self, components):
        """Vector class constructor.

        Parameters
        ----------
        components : array-like, iterable
            An iterable with length equal to 3, corresponding to x, y and z
            components.

        Examples
        --------
        >>> v = Vector([1, 2, 3])
        >>> v
        Vector(1, 2, 3)
        """
        self.components = components
        self.x, self.y, self.z = self.components

    def __getitem__(self, i):
        """Access vector components by indexing."""
        return self.components[i]

    def __iter__(self):
        """Adds support for iteration."""
        return iter(self.components)

    def __call__(self, *args):
        """Adds support for calling a vector as a function, if its elements are
        callable.

        Parameters
        ----------
        args : arguments
            Arguments to be passed to the vector elements.

        Returns
        -------
        Vector
            Vector with the return of each element called with the given
            arguments.

        Examples
        --------
        >>> v = Vector([lambda x: x**2, lambda x: x**3, lambda x: x**4])
        >>> v(2)
        Vector(4, 8, 16)
        """
        try:
            return self.element_wise(lambda f: f(*args))
        except TypeError as exc:
            msg = "One or more elements of this vector is not callable."
            raise TypeError(msg) from exc

    def __len__(self):
        return 3

    @cached_property
    def unit_vector(self):
        """R3 vector with the same direction of self, but normalized."""
        return self / abs(self)

    @cached_property
    def cross_matrix(self):
        """Skew symmetric matrix used for cross product.

        Notes
        -----
        The cross product between two vectors can be computed as the matrix
        product between the cross matrix of the first vector and the second
        vector.

        Examples
        --------
        >>> v = Vector([1, 7, 3])
        >>> u = Vector([2, 5, 6])
        >>> (v ^ u) == v.cross_matrix @ u
        True
        """
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
        return Vector([self.x + other.x, self.y + other.y, self.z + other.z])

    def __sub__(self, other):
        """Subtract two R3 vectors."""
        return Vector([self.x - other.x, self.y - other.y, self.z - other.z])

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
        """Cross product between self and other.

        Parameters
        ----------
        other : Vector
            R3 vector to be crossed with self.

        Returns
        -------
        Vector
            R3 vector resulting from the cross product between self and other.

        Examples
        --------
        >>> v = Vector([1, 7, 3])
        >>> u = Vector([2, 5, 6])
        >>> (v ^ u)
        Vector(27, 0, -9)

        Notes
        -----
        Parameters order matters, since cross product is not commutative.
        Parentheses are required when using cross product with the ^ operator
        to avoid ambiguity with the bitwise xor operator and keep the
        precedence of the operators.
        """
        return Vector(
            [
                self.y * other.z - self.z * other.y,
                -self.x * other.z + self.z * other.x,
                self.x * other.y - self.y * other.x,
            ]
        )

    def __matmul__(self, other):
        """Dot product between two R3 vectors."""
        return self.x * other.x + self.y * other.y + self.z * other.z

    def __eq__(self, other):
        """Check if two R3 vectors are equal.

        Parameters
        ----------
        other : Vector
            R3 vector to be compared with self.

        Returns
        -------
        bool
            True if self and other are equal. False otherwise.

        Examples
        --------
        >>> v = Vector([1, 7, 3])
        >>> u = Vector([1, 7, 3])
        >>> v == u
        True

        Notes
        -----
        Two R3 vectors are equal if their components are equal or almost equal.
        Python's cmath.isclose function is used to compare the components.
        """
        return (
            len(other) == 3
            and isclose(self.x, other[0], rel_tol=0, abs_tol=1e-9)
            and isclose(self.y, other[1], rel_tol=0, abs_tol=1e-9)
            and isclose(self.z, other[2], rel_tol=0, abs_tol=1e-9)
        )

    def is_parallel_to(self, other):
        """Returns True if self is parallel to R3 vector other. False otherwise.

        Parameters
        ----------
        other : Vector
            R3 vector to be compared with self.

        Returns
        -------
        bool
            True if self and other are parallel. False otherwise.

        Notes
        -----
        Two R3 vectors are parallel if their cross product is the zero vector.
        Python's cmath.isclose function is used to assert this.
        """
        return self ^ other == Vector([0, 0, 0])

    def is_orthogonal_to(self, other):
        """Returns True if self is perpendicular to R3 vector other. False
        otherwise.

        Parameters
        ----------
        other : Vector
            R3 vector to be compared with self.

        Returns
        -------
        bool
            True if self and other are perpendicular. False otherwise.

        Notes
        -----
        Two R3 vectors are perpendicular if their dot product is zero.
        Python's cmath.isclose function is used to assert this with absolute
        tolerance of 1e-9.
        """
        return isclose(self @ other, 0, rel_tol=0, abs_tol=1e-9)

    def element_wise(self, operation):
        """Element wise operation.

        Parameters
        ----------
        operation : callable
            Callable with a single argument, which should take an element and
            return the result of the desired operation.

        Examples
        --------
        >>> v = Vector([1, 7, 3])
        >>> v.element_wise(lambda x: x**2)
        Vector(1, 49, 9)
        """
        return Vector([operation(self.x), operation(self.y), operation(self.z)])

    def dot(self, other):
        """Dot product between two R3 vectors."""
        return self.__matmul__(other)

    def cross(self, other):
        """Cross product between two R3 vectors."""
        return self.__xor__(other)

    def proj(self, other):
        """Scalar projection of R3 vector self onto R3 vector other.

        Parameters
        ----------
        other : Vector
            R3 vector to be projected onto.

        Returns
        -------
        float
            Scalar projection of self onto other.

        Examples
        --------
        >>> v = Vector([1, 7, 3])
        >>> u = Vector([2, 5, 6])
        >>> v.proj(u)
        6.821910402406465
        """
        return (self @ other) / abs(other)

    def __str__(self):
        return f"({self.x}, {self.y}, {self.z})"

    def __repr__(self):
        return f"Vector({self.x}, {self.y}, {self.z})"

    @staticmethod
    def zeros():
        """Returns the zero vector."""
        return Vector([0, 0, 0])

    @staticmethod
    def i():
        """Returns the i vector, [1, 0, 0]."""
        return Vector([1, 0, 0])

    @staticmethod
    def j():
        """Returns the j vector, [0, 1, 0]."""
        return Vector([0, 1, 0])

    @staticmethod
    def k():
        """Returns the k vector, [0, 0, 1]."""
        return Vector([0, 0, 1])


class Matrix:
    """Pure Python 3x3 Matrix class for simple matrix-matrix and matrix-vector
    operations.

    Notes
    -----
    Instances of the Matrix class are immutable.
    Real and complex components are supported.

    Examples
    --------
    Creating a Matrix instance requires passing its components as a nested
    iterable:
    >>> M = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    >>> M
    Matrix([1, 2, 3],
           [4, 5, 6],
           [7, 8, 9])

    Matrix instances can be indexed and sliced like lists:
    >>> M[0]
    [1, 2, 3]
    >>> M[0][0]
    1
    >>> M[0, 0]
    1
    >>> M[0, 0:2]
    [1, 2]

    Matrix instances components can be accessed as attributes:
    >>> M.xx, M.xy, M.xz
    (1, 2, 3)

    Matrix instances can be called as functions, if their elements are
    callable:
    >>> M = Matrix([[lambda x: x**1, lambda x: x**2, lambda x: x**3],
    ...             [lambda x: x**4, lambda x: x**5, lambda x: x**6],
    ...             [lambda x: x**7, lambda x: x**8, lambda x: x**9]])
    >>> M(2)
    Matrix([2, 4, 8],
           [16, 32, 64],
           [128, 256, 512])

    Matrix instances can be added, subtracted, multiplied and divided by
    scalars:
    >>> M = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    >>> M + M
    Matrix([2, 4, 6],
           [8, 10, 12],
           [14, 16, 18])
    >>> M - M
    Matrix([0, 0, 0],
           [0, 0, 0],
           [0, 0, 0])
    >>> M * 2
    Matrix([2, 4, 6],
           [8, 10, 12],
           [14, 16, 18])
    >>> M / 2
    Matrix([0.5, 1.0, 1.5],
           [2.0, 2.5, 3.0],
           [3.5, 4.0, 4.5])

    Matrix instances can be multiplied (inner product) by other matrices:
    >>> M = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    >>> N = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    >>> M @ N
    Matrix([30, 36, 42],
           [66, 81, 96],
           [102, 126, 150])

    Matrix instances can be used to transform vectors by the inner product:
    >>> M = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    >>> v = Vector([1, 2, 3])
    >>> M @ v
    Vector(14, 32, 50)

    Matrix instances can be transposed and inverted:
    >>> M = Matrix([[1, 2, 3], [4, 0, 6], [7, 8, 9]])
    >>> M.transpose
    Matrix([1, 4, 7],
           [2, 0, 8],
           [3, 6, 9])
    >>> M.inverse
    Matrix([-0.8, 0.1, 0.2],
           [0.1, -0.2, 0.1],
           [0.5333333333333333, 0.1, -0.13333333333333333])

    Matrix instances can be element-wise operated on by callables:
    >>> M = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    >>> M.element_wise(lambda x: x**2)
    Matrix([1, 4, 9],
           [16, 25, 36],
           [49, 64, 81])

    Determinants can be calculated:
    >>> M = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    >>> M.det
    0
    >>> abs(M)
    0

    Matrices can be compared for equality:
    >>> M = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    >>> N = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    >>> M == N
    True
    >>> M != N
    False
    """

    __array_ufunc__ = None

    def __init__(self, components):
        """Matrix class constructor.

        Parameters
        ----------
        components : 3x3 array-like
            3x3 array-like with matrix components. Indexing must be
            [row, column].

        Examples
        --------
        >>> M = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        >>> M
        Matrix([1, 2, 3],
               [4, 5, 6],
               [7, 8, 9])
        """
        self.components = components
        self.x, self.y, self.z = self.components
        self.xx, self.xy, self.xz = self.x
        self.yx, self.yy, self.yz = self.y
        self.zx, self.zy, self.zz = self.z

    def __getitem__(self, args):
        """Adds support for indexing and slicing."""
        if isinstance(args, int):
            return self.components[args]
        else:
            return self.components[args[0]][args[1]]

    def __iter__(self):
        """Adds support for iteration."""
        return iter(self.components)

    def __call__(self, *args):
        """Adds support for calling a matrix as a function, if its elements are
        callable.

        Parameters
        ----------
        args : tuple
            Arguments to be passed to the matrix elements.

        Returns
        -------
        Matrix
            Matrix with the same shape as the original, but with its elements
            replaced by the result of calling them with the given arguments.

        Examples
        --------
        >>> M = Matrix([[lambda x: x**1, lambda x: x**2, lambda x: x**3],
        ...             [lambda x: x**4, lambda x: x**5, lambda x: x**6],
        ...             [lambda x: x**7, lambda x: x**8, lambda x: x**9]])
        >>> M(2)
        Matrix([2, 4, 8],
               [16, 32, 64],
               [128, 256, 512])
        """
        try:
            return self.element_wise(lambda f: f(*args))
        except TypeError as exc:
            msg = "One or more elements of this matrix is not callable."
            raise TypeError(msg) from exc

    def __len__(self):
        """Adds support for the len() function."""
        return 3

    @cached_property
    def shape(self):
        """tuple: Shape of the matrix."""
        return (3, 3)

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
        """Matrix determinant."""
        return self.__abs__()

    @cached_property
    def is_diagonal(self, tol=1e-6):
        """Boolean indicating if matrix is diagonal.

        Parameters
        ----------
        tol : float, optional
            Tolerance used to determine if non-diagonal elements are negligible.
            Defaults to 1e-6.

        Returns
        -------
        bool
            True if matrix is diagonal, False otherwise.

        Examples
        --------
        >>> M = Matrix([[1, 0, 0], [0, 2, 0], [0, 0, 3]])
        >>> M.is_diagonal
        True

        >>> M = Matrix([[1, 0, 0], [0, 2, 0], [0, 1e-7, 3]])
        >>> M.is_diagonal
        True

        >>> M = Matrix([[1, 0, 0], [0, 2, 0], [0, 1e-5, 3]])
        >>> M.is_diagonal
        False
        """
        for i, j in product(range(3), range(3)):
            if i == j:
                continue
            if abs(self[i, j]) > tol:
                return False
        return True

    @cached_property
    def inverse(self):
        """Matrix inverse.

        Returns
        -------
        Matrix
            Inverse of the matrix.

        Notes
        -----
        If the matrix is diagonal, the inverse is computed by inverting its
        diagonal elements. If not, the inverse is computed using the adjugate
        matrix.

        Raises
        ------
        ZeroDivisionError
            If the matrix is singular.
        """
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
                [self.xx + other.xx, self.xy + other.xy, self.xz + other.xz],
                [self.yx + other.yx, self.yy + other.yy, self.yz + other.yz],
                [self.zx + other.zx, self.zy + other.zy, self.zz + other.zz],
            ]
        )

    def __sub__(self, other):
        """Subtract two 3x3 matrices."""
        return Matrix(
            [
                [self.xx - other.xx, self.xy - other.xy, self.xz - other.xz],
                [self.yx - other.yx, self.yy - other.yy, self.yz - other.yz],
                [self.zx - other.zx, self.zy - other.zy, self.zz - other.zz],
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
        """Dot (inner) product between two 3x3 matrices or between 3x3 matrix
        and R3 vector.

        Parameters
        ----------
        other : Matrix or Vector
            The other matrix or vector.

        Returns
        -------
        Matrix or Vector
            The result of the dot product. A Matrix if other if Matrix, and
            a Vector if other is Vector.

        Examples
        --------
        >>> M = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        >>> v = Vector([1, 2, 3])
        >>> M @ v
        Vector(14, 32, 50)

        >>> M = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        >>> N = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        >>> M @ N
        Matrix([30, 36, 42],
               [66, 81, 96],
               [102, 126, 150])
        """
        if isinstance(other, Vector):
            return Vector(
                [
                    self.xx * other.x + self.xy * other.y + self.xz * other.z,
                    self.yx * other.x + self.yy * other.y + self.yz * other.z,
                    self.zx * other.x + self.zy * other.y + self.zz * other.z,
                ]
            )
        elif isinstance(other, Matrix):
            return Matrix(
                [
                    [
                        self.xx * other.xx + self.xy * other.yx + self.xz * other.zx,
                        self.xx * other.xy + self.xy * other.yy + self.xz * other.zy,
                        self.xx * other.xz + self.xy * other.yz + self.xz * other.zz,
                    ],
                    [
                        self.yx * other.xx + self.yy * other.yx + self.yz * other.zx,
                        self.yx * other.xy + self.yy * other.yy + self.yz * other.zy,
                        self.yx * other.xz + self.yy * other.yz + self.yz * other.zz,
                    ],
                    [
                        self.zx * other.xx + self.zy * other.yx + self.zz * other.zx,
                        self.zx * other.xy + self.zy * other.yy + self.zz * other.zy,
                        self.zx * other.xz + self.zy * other.yz + self.zz * other.zz,
                    ],
                ]
            )
        else:
            raise TypeError("Can only dot product with Matrix or Vector.")

    def __pow__(self, other):
        """Exponentiation of 3x3 matrix by integer other.

        Parameters
        ----------
        other : int
            The exponent.

        Returns
        -------
        Matrix
            The result of exponentiation.

        Examples
        --------
        >>> M = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        >>> M ** 2
        Matrix([30, 36, 42],
               [66, 81, 96],
               [102, 126, 150])
        """
        result = Matrix.identity()
        for _ in range(other):
            result = result @ self
        return result

    def __eq__(self, other):
        """Equality of two 3x3 matrices.

        Parameters
        ----------
        other : Matrix
            The other matrix.

        Returns
        -------
        bool
            True if the two matrices are equal, False otherwise.

        Examples
        --------
        >>> M = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        >>> N = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        >>> M == N
        True

        >>> M = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        >>> N = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 10]])
        >>> M == N
        False

        Notes
        -----
        Equality is determined by comparing each element of the two matrices
        with an absolute tolerance of 1e-9 using Python's cmath.isclose.
        """
        return (
            len(other) == 3
            and isclose(self.xx, other[0][0], rel_tol=0, abs_tol=1e-9)
            and isclose(self.xy, other[0][1], rel_tol=0, abs_tol=1e-9)
            and isclose(self.xz, other[0][2], rel_tol=0, abs_tol=1e-9)
            and isclose(self.yx, other[1][0], rel_tol=0, abs_tol=1e-9)
            and isclose(self.yy, other[1][1], rel_tol=0, abs_tol=1e-9)
            and isclose(self.yz, other[1][2], rel_tol=0, abs_tol=1e-9)
            and isclose(self.zx, other[2][0], rel_tol=0, abs_tol=1e-9)
            and isclose(self.zy, other[2][1], rel_tol=0, abs_tol=1e-9)
            and isclose(self.zz, other[2][2], rel_tol=0, abs_tol=1e-9)
        )

    def element_wise(self, operation):
        """Element wise operation.

        Parameters
        ----------
        operation : callable
            Callable with a single argument, which should take an element and
            return the result of the desired operation.

        Returns
        -------
        Matrix
            The result of the element wise operation.

        Examples
        --------
        >>> M = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        >>> M.element_wise(lambda x: x ** 2)
        Matrix([1, 4, 9],
               [16, 25, 36],
               [49, 64, 81])
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
        vector.

        See Also
        --------
        Matrix.__matmul__
        """
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
        """Returns the 3x3 identity matrix."""
        return Matrix([[1, 0, 0], [0, 1, 0], [0, 0, 1]])

    @staticmethod
    def zeros():
        """Returns the 3x3 zero matrix."""
        return Matrix([[0, 0, 0], [0, 0, 0], [0, 0, 0]])

    @staticmethod
    def transformation(quaternion):
        """Returns the transformation Matrix from frame B to frame A, where B
        is rotated by the quaternion q with respect to A.

        Parameters
        ----------
        q : tuple of 4 floats
            The quaternion representing the rotation from frame A to frame B.
            Example: (cos(phi/2), 0, 0, sin(phi/2)) represents a rotation of
            phi around the z-axis.
            Note: the quaternion must be normalized.

        Returns
        -------
        Matrix
            The transformation matrix from frame B to frame A.
        """
        q_w, q_x, q_y, q_z = quaternion
        return Matrix(
            [
                [
                    1 - 2 * (q_y**2 + q_z**2),
                    2 * (q_x * q_y - q_w * q_z),
                    2 * (q_x * q_z + q_w * q_y),
                ],
                [
                    2 * (q_x * q_y + q_w * q_z),
                    1 - 2 * (q_x**2 + q_z**2),
                    2 * (q_y * q_z - q_w * q_x),
                ],
                [
                    2 * (q_x * q_z - q_w * q_y),
                    2 * (q_y * q_z + q_w * q_x),
                    1 - 2 * (q_x**2 + q_y**2),
                ],
            ]
        )


def tuple_handler(value):
    """Transforms the input value into a tuple that
    represents a range. If the input is an input or float,
    the output is a tuple from zero to the input value. If
    the input is a tuple or list, the output is a tuple with
    the same range.

    Parameters
    ----------
    value : int, float, tuple, list
        Input value.

    Returns
    -------
    tuple
        Tuple that represents the inputted range.
    """
    if isinstance(value, (int, float)):
        return (0, value)
    elif isinstance(value, (list, tuple)):
        if len(value) == 1:
            return (0, value[0])
        elif len(value) == 2:
            return tuple(value)
        else:
            raise ValueError("value must be a list or tuple of length 1 or 2.")


def bilinear_interpolation(x, y, x1, x2, y1, y2, z11, z12, z21, z22):
    """Bilinear interpolation. It considers the values of the four points
    around the point to be interpolated and returns the interpolated value.
    Made with a lot of help from GitHub Copilot.

    Parameters
    ----------
    x : float
        x coordinate to which the value will be interpolated.
    y : float
        y coordinate to which the value will be interpolated.
    x1 : float
        x coordinate of the first point.
    x2 : float
        x coordinate of the second point.
    y1 : float
        y coordinate of the first point.
    y2 : float
        y coordinate of the second point.
    z11 : float
        Value at the first point.
    z12 : float
        Value at the second point.
    z21 : float
        Value at the third point.
    z22 : float
        Value at the fourth point.

    Returns
    -------
    float
        Interpolated value.

    Examples
    --------
    >>> from rocketpy.tools import bilinear_interpolation
    >>> bilinear_interpolation(0.5, 0.5, 0, 1, 0, 1, 0, 1, 1, 0)
    0.5
    """
    return (
        z11 * (x2 - x) * (y2 - y)
        + z21 * (x - x1) * (y2 - y)
        + z12 * (x2 - x) * (y - y1)
        + z22 * (x - x1) * (y - y1)
    ) / ((x2 - x1) * (y2 - y1))


def find_two_closest_integers(number):
    """Find the two closest integer factors of a number.

    Parameters
    ----------
    number: int

    Returns
    -------
    tuple
        Two closest integer factors of the number.

    Examples
    --------
    >>> from rocketpy.tools import find_two_closest_integers
    >>> find_two_closest_integers(10)
    (2, 5)
    >>> find_two_closest_integers(12)
    (3, 4)
    >>> find_two_closest_integers(13)
    (1, 13)
    >>> find_two_closest_integers(150)
    (10, 15)
    """
    number_sqrt = number**0.5
    if isinstance(number_sqrt, int):
        return number_sqrt, number_sqrt
    else:
        guess = int(number_sqrt)
        while True:
            if number % guess == 0:
                return guess, number // guess
            else:
                guess -= 1


def time_num_to_date_string(time_num, units, timezone, calendar="gregorian"):
    """Convert time number (usually hours before a certain date) into two
    strings: one for the date (example: 2022.04.31) and one for the hour
    (example: 14). See cftime.num2date for details on units and calendar.
    Automatically converts time number from UTC to local timezone based on
    lat, lon coordinates. This function was created originally for the
    EnvironmentAnalysis class.

    Parameters
    ----------
    time_num : float
        Time number to be converted.
    units : str
        Units of the time number. See cftime.num2date for details.
    timezone : pytz.timezone
        Timezone to which the time number will be converted. See
        pytz.timezone for details.
    calendar : str, optional
        Calendar to be used. See cftime.num2date for details.

    Returns
    -------
    date_string : str
        Date string.
    hour_string : str
        Hour string.
    date_time : datetime.datetime
        Datetime object.
    """
    date_time_utc = num2pydate(time_num, units, calendar=calendar)
    date_time_utc = date_time_utc.replace(tzinfo=pytz.UTC)
    date_time = date_time_utc.astimezone(timezone)
    date_string = f"{date_time.year}.{date_time.month}.{date_time.day}"
    hour_string = f"{date_time.hour}"
    return date_string, hour_string, date_time


def geopotential_to_height_asl(geopotential, radius=63781370, g=9.80665):
    """Compute height above sea level from geopotential.

    Source: https://en.wikipedia.org/wiki/Geopotential

    Parameters
    ----------
    geopotential : float
        Geopotential in m^2/s^2. It is the geopotential value at a given
        pressure level, to be converted to height above sea level.
    radius : float, optional
        Earth radius in m. Default is 63781370 m.
    g : float, optional
        Gravity acceleration in m/s^2. Default is 9.80665 m/s^2.

    Returns
    -------
    geopotential_to_height_asl : float
        Height above sea level in m

    Examples
    --------
    >>> from rocketpy.tools import geopotential_to_height_asl
    >>> geopotential_to_height_asl(0)
    0.0
    >>> geopotential_to_height_asl(100000)
    10198.792680243916
    >>> geopotential_to_height_asl(200000)
    20400.84750449947
    """
    geopotential_height = geopotential / g
    return radius * geopotential_height / (radius - geopotential_height)


def geopotential_to_height_agl(geopotential, elevation, radius=63781370, g=9.80665):
    """Compute height above ground level from geopotential and elevation.

    Parameters
    ----------
    geopotential : float
        Geopotential in m^2/s^2. It is the geopotential value at a given
        pressure level, to be converted to height above ground level.
    elevation : float
        Surface elevation in m
    radius : float, optional
        Earth radius in m. Default is 63781370 m.
    g : float, optional
        Gravity acceleration in m/s^2. Default is 9.80665 m/s^2.

    Returns
    -------
    height_above_ground_level : float
        Height above ground level in m

    Examples
    --------
    >>> from rocketpy.tools import geopotential_to_height_agl
    >>> geopotential_to_height_agl(0, 0)
    0.0
    >>> geopotential_to_height_agl(100000, 0)
    10198.792680243916
    >>> geopotential_to_height_agl(100000, 1000)
    9198.792680243916
    """
    return geopotential_to_height_asl(geopotential, radius, g) - elevation


def find_closest(ordered_sequence, value):
    """Find the index of the closest value to a given value within an ordered
    sequence.

    Parameters
    ----------
    ordered_sequence : list
        A sequence of values that is ordered from smallest to largest.
    value : float
        The value to which you want to find the closest value.

    Returns
    -------
    index : int
        The index of the closest value to the given value within the ordered
        sequence. If the given value is less than the first value in the
        sequence, then 0 is returned. If the given value is greater than the
        last value in the sequence, then the index of the last value in the
        sequence is returned.
    """
    if len(ordered_sequence) == 1:
        return 0

    pivot_index = bisect_left(ordered_sequence, value)
    if pivot_index == 0:
        return pivot_index
    if pivot_index == len(ordered_sequence):
        return pivot_index - 1

    smaller, greater = ordered_sequence[pivot_index - 1], ordered_sequence[pivot_index]

    return pivot_index - 1 if value - smaller <= greater - value else pivot_index


def import_optional_dependency(name):
    """Import an optional dependency. If the dependency is not installed, an
    ImportError is raised. This function is based on the implementation found in
    pandas repository:
    github.com/pandas-dev/pandas/blob/main/pandas/compat/_optional.py

    Parameters
    ----------
    name : str
        The name of the module to import. Can be used to import submodules too.
        The name will be used as an argument to importlib.import_module method.

    Examples:
    ---------
    >>> from rocketpy.tools import import_optional_dependency
    >>> matplotlib = import_optional_dependency("matplotlib")
    >>> matplotlib.__name__
    'matplotlib'
    >>> plt = import_optional_dependency("matplotlib.pyplot")
    >>> plt.__name__
    'matplotlib.pyplot'
    """
    try:
        module = importlib.import_module(name)
    except ImportError as exc:
        package_name = name.split(".")[0]
        raise ImportError(
            f"{package_name} is an optional dependency and is not installed.\n"
            + f"\t\tUse 'pip install {package_name}' to install it or "
            + "'pip install rocketpy[all]' to install all optional dependencies."
        ) from exc
    return module


if __name__ == "__main__":
    import doctest

    doctest.testmod()
