"""
Transformation utilities for DXF import/export.

This module provides functions for handling coordinate transformations,
coordinate system conversions, and other geometric transformations.
"""

import math
from typing import List, Tuple, Optional, Union, Dict, Any
from mathutils import Vector, Matrix, Quaternion, Euler

# Type aliases
Vec3 = Tuple[float, float, float]
Mat4 = List[List[float]]

# Default tolerance for floating-point comparisons
DEFAULT_TOLERANCE = 1e-6

def identity_matrix() -> Mat4:
    """Return a 4x4 identity matrix."""
    return [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]

def translation_matrix(offset: Vec3) -> Mat4:
    """Create a translation matrix.
    
    Args:
        offset: Translation vector (x, y, z)
        
    Returns:
        4x4 translation matrix
    """
    return [
        [1.0, 0.0, 0.0, offset[0]],
        [0.0, 1.0, 0.0, offset[1]],
        [0.0, 0.0, 1.0, offset[2]],
        [0.0, 0.0, 0.0, 1.0],
    ]

def scale_matrix(scale: Union[float, Vec3]) -> Mat4:
    """Create a scale matrix.
    
    Args:
        scale: Uniform scale factor or (x, y, z) scale factors
        
    Returns:
        4x4 scale matrix
    """
    if isinstance(scale, (int, float)):
        scale = (scale, scale, scale)
    
    return [
        [scale[0], 0.0, 0.0, 0.0],
        [0.0, scale[1], 0.0, 0.0],
        [0.0, 0.0, scale[2], 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]

def rotation_matrix(axis: Vec3, angle: float) -> Mat4:
    """Create a rotation matrix around an axis.
    
    Args:
        axis: Rotation axis (x, y, z)
        angle: Rotation angle in radians
        
    Returns:
        4x4 rotation matrix
    """
    # Normalize the axis
    length = math.sqrt(sum(x*x for x in axis))
    if abs(length) < 1e-6:
        return identity_matrix()
    
    x, y, z = (v/length for v in axis)
    c = math.cos(angle)
    s = math.sin(angle)
    t = 1 - c
    
    return [
        [t*x*x + c,    t*x*y - s*z,  t*x*z + s*y,  0.0],
        [t*x*y + s*z,  t*y*y + c,    t*y*z - s*x,  0.0],
        [t*x*z - s*y,  t*y*z + s*x,  t*z*z + c,    0.0],
        [0.0,          0.0,          0.0,          1.0],
    ]

def matrix_multiply(a: Mat4, b: Mat4) -> Mat4:
    """Multiply two 4x4 matrices."""
    return [
        [
            sum(a[i][k] * b[k][j] for k in range(4))
            for j in range(4)
        ]
        for i in range(4)
    ]

def transform_point_matrix(point: Vec3, matrix: Mat4) -> Vec3:
    """Transform a point using a 4x4 matrix."""
    x, y, z = point
    w = 1.0
    
    tx = matrix[0][0]*x + matrix[0][1]*y + matrix[0][2]*z + matrix[0][3]*w
    ty = matrix[1][0]*x + matrix[1][1]*y + matrix[1][2]*z + matrix[1][3]*w
    tz = matrix[2][0]*x + matrix[2][1]*y + matrix[2][2]*z + matrix[2][3]*w
    tw = matrix[3][0]*x + matrix[3][1]*y + matrix[3][2]*z + matrix[3][3]*w
    
    if abs(tw) > 1e-6:
        return (tx/tw, ty/tw, tz/tw)
    return (tx, ty, tz)

def transform_normal_matrix(normal: Vec3, matrix: Mat4) -> Vec3:
    """Transform a normal vector using the inverse transpose of a 4x4 matrix."""
    # Extract the 3x3 rotation/scale part of the matrix
    m = [row[:3] for row in matrix[:3]]
    
    # Calculate the inverse transpose
    det = m[0][0] * (m[1][1]*m[2][2] - m[1][2]*m[2][1]) - \
          m[0][1] * (m[1][0]*m[2][2] - m[1][2]*m[2][0]) + \
          m[0][2] * (m[1][0]*m[2][1] - m[1][1]*m[2][0])
    
    if abs(det) < 1e-6:
        return normal
    
    inv_det = 1.0 / det
    inv_transpose = [
        [
            (m[1][1] * m[2][2] - m[1][2] * m[2][1]) * inv_det,
            (m[0][2] * m[2][1] - m[0][1] * m[2][2]) * inv_det,
            (m[0][1] * m[1][2] - m[0][2] * m[1][1]) * inv_det,
        ],
        [
            (m[1][2] * m[2][0] - m[1][0] * m[2][2]) * inv_det,
            (m[0][0] * m[2][2] - m[0][2] * m[2][0]) * inv_det,
            (m[0][2] * m[1][0] - m[0][0] * m[1][2]) * inv_det,
        ],
        [
            (m[1][0] * m[2][1] - m[1][1] * m[2][0]) * inv_det,
            (m[0][1] * m[2][0] - m[0][0] * m[2][1]) * inv_det,
            (m[0][0] * m[1][1] - m[0][1] * m[1][0]) * inv_det,
        ],
    ]
    
    # Transform the normal
    x, y, z = normal
    tx = inv_transpose[0][0]*x + inv_transpose[0][1]*y + inv_transpose[0][2]*z
    ty = inv_transpose[1][0]*x + inv_transpose[1][1]*y + inv_transpose[1][2]*z
    tz = inv_transpose[2][0]*x + inv_transpose[2][1]*y + inv_transpose[2][2]*z
    
    # Normalize the result
    length = math.sqrt(tx*tx + ty*ty + tz*tz)
    if length > 1e-6:
        return (tx/length, ty/length, tz/length)
    return normal

def matrix_to_euler(matrix: Mat4, order: str = 'XYZ') -> Tuple[float, float, float]:
    """Convert a rotation matrix to Euler angles."""
    # Convert to Blender's Matrix and then to Euler
    m = Matrix([row[:3] for row in matrix[:3]])
    euler = m.to_euler(order)
    return (euler.x, euler.y, euler.z)

def euler_to_matrix(euler: Tuple[float, float, float], order: str = 'XYZ') -> Mat4:
    """Convert Euler angles to a rotation matrix."""
    # Convert to Blender's Euler and then to matrix
    eul = Euler(euler, order)
    m = eul.to_matrix().to_4x4()
    return [list(row) for row in m]

def quaternion_to_matrix(quat: Tuple[float, float, float, float]) -> Mat4:
    """Convert a quaternion to a rotation matrix."""
    q = Quaternion(quat)
    m = q.to_matrix().to_4x4()
    return [list(row) for row in m]

def matrix_to_quaternion(matrix: Mat4) -> Tuple[float, float, float, float]:
    """Convert a rotation matrix to a quaternion."""
    m = Matrix([row[:3] for row in matrix[:3]])
    q = m.to_quaternion()
    return (q.w, q.x, q.y, q.z)

def transform_points(points: List[Vec3], matrix: Mat4) -> List[Vec3]:
    """Transform a list of points using a 4x4 matrix."""
    return [transform_point_matrix(p, matrix) for p in points]

def transform_vectors(vectors: List[Vec3], matrix: Mat4) -> List[Vec3]:
    """Transform a list of vectors (without translation) using a 4x4 matrix."""
    # Create a matrix without translation
    no_translation = [row[:] for row in matrix]
    no_translation[0][3] = 0.0
    no_translation[1][3] = 0.0
    no_translation[2][3] = 0.0
    
    return [transform_point_matrix(v, no_translation) for v in vectors]

def compose_matrix(location: Optional[Vec3] = None,
                 rotation: Optional[Tuple[float, float, float]] = None,
                 scale: Optional[Union[float, Tuple[float, float, float]]] = None) -> Mat4:
    """Compose a transformation matrix from location, rotation, and scale."""
    # Start with identity
    result = identity_matrix()
    
    # Apply scale
    if scale is not None:
        if isinstance(scale, (int, float)):
            scale = (scale, scale, scale)
        result = matrix_multiply(result, scale_matrix(scale))
    
    # Apply rotation
    if rotation is not None:
        result = matrix_multiply(result, euler_to_matrix(rotation))
    
    # Apply location
    if location is not None:
        result = matrix_multiply(result, translation_matrix(location))
    
    return result

def decompose_matrix(matrix: Mat4) -> Dict[str, Any]:
    """Decompose a transformation matrix into location, rotation, and scale."""
    # Extract translation
    location = (matrix[0][3], matrix[1][3], matrix[2][3])
    
    # Extract scale
    x_scale = math.sqrt(sum(x*x for x in [matrix[i][0] for i in range(3)]))
    y_scale = math.sqrt(sum(y*y for y in [matrix[i][1] for i in range(3)]))
    z_scale = math.sqrt(sum(z*z for z in [matrix[i][2] for i in range(3)]))
    scale = (x_scale, y_scale, z_scale)
    
    # Extract rotation (remove scale first)
    rot_matrix = [
        [matrix[i][j] / scale[j] for j in range(3)]
        for i in range(3)
    ]
    
    # Convert to Euler angles (using XYZ order by default)
    rotation = matrix_to_euler(rot_matrix + [[0, 0, 0, 1]], 'XYZ')
    
    return {
        'location': location,
        'rotation': rotation,
        'scale': scale,
    }
