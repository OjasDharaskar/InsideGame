"""
Custom 2D Math and 3x3 Homogeneous Transformation Matrix Pipeline.
Fulfills Rule 2 & Rule 4 of Development Skill:
Custom functions for translation, transformation, and rotation using 3x3 homogeneous matrices.
Zero usage of built-in transformation functions.
"""

import math
from typing import List, Tuple, Sequence


class Matrix3x3:
    """
    3x3 Homogeneous transformation matrix for 2D affine transformations:
    [ m00  m01  m02 ]
    [ m10  m11  m12 ]
    [ m20  m21  m22 ]
    
    Coordinates are represented as column vectors [x, y, 1]^T.
    """
    __slots__ = ('m00', 'm01', 'm02', 'm10', 'm11', 'm12', 'm20', 'm21', 'm22')

    def __init__(
        self,
        m00: float = 1.0, m01: float = 0.0, m02: float = 0.0,
        m10: float = 0.0, m11: float = 1.0, m12: float = 0.0,
        m20: float = 0.0, m21: float = 0.0, m22: float = 1.0
    ):
        self.m00 = float(m00)
        self.m01 = float(m01)
        self.m02 = float(m02)
        self.m10 = float(m10)
        self.m11 = float(m11)
        self.m12 = float(m12)
        self.m20 = float(m20)
        self.m21 = float(m21)
        self.m22 = float(m22)

    @classmethod
    def identity(cls) -> 'Matrix3x3':
        """Returns the 3x3 identity matrix."""
        return cls(1.0, 0.0, 0.0,
                   0.0, 1.0, 0.0,
                   0.0, 0.0, 1.0)

    @classmethod
    def translation(cls, tx: float, ty: float) -> 'Matrix3x3':
        """
        Returns a 2D translation matrix:
        [ 1  0  tx ]
        [ 0  1  ty ]
        [ 0  0  1  ]
        """
        return cls(1.0, 0.0, float(tx),
                   0.0, 1.0, float(ty),
                   0.0, 0.0, 1.0)

    @classmethod
    def rotation(cls, angle_rad: float) -> 'Matrix3x3':
        """
        Returns a 2D rotation matrix around origin (0, 0) by angle in radians:
        [ cos(θ) -sin(θ)  0 ]
        [ sin(θ)  cos(θ)  0 ]
        [   0       0     1 ]
        """
        c = math.cos(angle_rad)
        s = math.sin(angle_rad)
        return cls(c, -s, 0.0,
                   s,  c, 0.0,
                   0.0, 0.0, 1.0)

    @classmethod
    def rotation_degrees(cls, angle_deg: float) -> 'Matrix3x3':
        """Returns a 2D rotation matrix for angle in degrees."""
        return cls.rotation(math.radians(angle_deg))

    @classmethod
    def scale(cls, sx: float, sy: float) -> 'Matrix3x3':
        """
        Returns a 2D scaling matrix:
        [ sx  0   0 ]
        [ 0   sy  0 ]
        [ 0   0   1 ]
        """
        return cls(float(sx), 0.0, 0.0,
                   0.0, float(sy), 0.0,
                   0.0, 0.0, 1.0)

    def multiply(self, other: 'Matrix3x3') -> 'Matrix3x3':
        """
        Multiplies this matrix by another 3x3 matrix: result = self * other.
        """
        return Matrix3x3(
            self.m00 * other.m00 + self.m01 * other.m10 + self.m02 * other.m20,
            self.m00 * other.m01 + self.m01 * other.m11 + self.m02 * other.m21,
            self.m00 * other.m02 + self.m01 * other.m12 + self.m02 * other.m22,

            self.m10 * other.m00 + self.m11 * other.m10 + self.m12 * other.m20,
            self.m10 * other.m01 + self.m11 * other.m11 + self.m12 * other.m21,
            self.m10 * other.m02 + self.m11 * other.m12 + self.m12 * other.m22,

            self.m20 * other.m00 + self.m21 * other.m10 + self.m22 * other.m20,
            self.m20 * other.m01 + self.m21 * other.m11 + self.m22 * other.m21,
            self.m20 * other.m02 + self.m21 * other.m12 + self.m22 * other.m22,
        )

    def __matmul__(self, other: 'Matrix3x3') -> 'Matrix3x3':
        return self.multiply(other)

    def transform_point(self, x: float, y: float) -> Tuple[float, float]:
        """
        Transforms a 2D point (x, y) by this homogeneous matrix:
        [x', y', 1]^T = M * [x, y, 1]^T
        """
        x_new = self.m00 * x + self.m01 * y + self.m02
        y_new = self.m10 * x + self.m11 * y + self.m12
        w = self.m20 * x + self.m21 * y + self.m22
        if abs(w - 1.0) > 1e-7 and abs(w) > 1e-9:
            return (x_new / w, y_new / w)
        return (x_new, y_new)

    def transform_points(self, points: Sequence[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Transforms a collection of 2D points."""
        return [self.transform_point(px, py) for px, py in points]


# Standalone custom transformation helper functions (Rule 2 compliance)

def custom_translate_point(x: float, y: float, tx: float, ty: float) -> Tuple[float, float]:
    """Translates a point without built-in functions via homogeneous matrix."""
    mat = Matrix3x3.translation(tx, ty)
    return mat.transform_point(x, y)


def custom_rotate_point(x: float, y: float, angle_rad: float, cx: float = 0.0, cy: float = 0.0) -> Tuple[float, float]:
    """
    Rotates a point (x, y) around pivot (cx, cy) by angle_rad using homogeneous matrices:
    M = T(cx, cy) * R(angle) * T(-cx, -cy)
    """
    t_to = Matrix3x3.translation(-cx, -cy)
    r = Matrix3x3.rotation(angle_rad)
    t_back = Matrix3x3.translation(cx, cy)
    m = t_back.multiply(r).multiply(t_to)
    return m.transform_point(x, y)


def create_srt_matrix(
    tx: float, ty: float,
    angle_rad: float = 0.0,
    sx: float = 1.0, sy: float = 1.0,
    pivot_x: float = 0.0, pivot_y: float = 0.0
) -> Matrix3x3:
    """
    Creates a composite homogeneous transformation matrix:
    Translation * PivotTranslate * Rotation * Scale * InversePivotTranslate
    """
    m_trans = Matrix3x3.translation(tx, ty)
    m_p_back = Matrix3x3.translation(pivot_x, pivot_y)
    m_rot = Matrix3x3.rotation(angle_rad)
    m_scale = Matrix3x3.scale(sx, sy)
    m_p_to = Matrix3x3.translation(-pivot_x, -pivot_y)

    return m_trans.multiply(m_p_back).multiply(m_rot).multiply(m_scale).multiply(m_p_to)
