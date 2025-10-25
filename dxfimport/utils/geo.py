"""
Geospatial utilities for DXF import/export.

This module provides functions for handling coordinate systems, projections,
and other geospatial operations needed for DXF import/export.
"""

import math
from typing import Tuple, Optional, Union, Dict, Any
from mathutils import Vector, Matrix

# Type aliases
Vec3 = Tuple[float, float, float]

# Common EPSG codes and their corresponding proj4 strings
EPSG_PROJ4 = {
    # Common projected coordinate systems
    'EPSG:3857': '+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext +no_defs',  # Web Mercator
    'EPSG:4326': '+proj=longlat +datum=WGS84 +no_defs',  # WGS84 (lat/lon)
    'EPSG:3395': '+proj=merc +lon_0=0 +k=1 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs',  # World Mercator
    
    # Common projected coordinate systems by region
    'EPSG:32633': '+proj=utm +zone=33 +datum=WGS84 +units=m +no_defs',  # UTM zone 33N (Europe)
    'EPSG:26910': '+proj=utm +zone=10 +datum=NAD83 +units=m +no_defs',  # UTM zone 10N (NAD83)
    'EPSG:32651': '+proj=utm +zone=51 +datum=WGS84 +units=m +no_defs',  # UTM zone 51N (Asia)
    
    # National grid systems
    'EPSG:27700': '+proj=tmerc +lat_0=49 +lon_0=-2 +k=0.9996012717 +x_0=400000 +y_0=-100000 +ellps=airy +towgs84=446.448,-125.157,542.06,0.15,0.247,0.842,-20.489 +units=m +no_defs',  # OSGB36 / British National Grid
    'EPSG:28992': '+proj=sterea +lat_0=52.15616055555555 +lon_0=5.38763888888889 +k=0.9999079 +x_0=155000 +y_0=463000 +ellps=bessel +towgs84=565.417,50.3319,465.552,-0.398957,0.343988,-1.8774,4.0725 +units=m +no_defs',  # Amersfoort / RD New (Netherlands)
}

class GeoReference:
    """Class for handling georeferencing information."""
    
    def __init__(self, srid: Optional[str] = None, proj4: Optional[str] = None):
        """Initialize with either an SRID or a proj4 string.
        
        Args:
            srid: EPSG code (e.g., 'EPSG:4326')
            proj4: Proj4 definition string
        """
        self.srid = srid
        self.proj4 = proj4 or (EPSG_PROJ4.get(srid) if srid else None)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary for serialization."""
        return {
            'srid': self.srid,
            'proj4': self.proj4
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GeoReference':
        """Create from a dictionary."""
        return cls(srid=data.get('srid'), proj4=data.get('proj4'))

def distance(p1: Vec3, p2: Vec3) -> float:
    """Calculate the Euclidean distance between two 3D points."""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(p1, p2)))

def midpoint(p1: Vec3, p2: Vec3) -> Vec3:
    """Calculate the midpoint between two 3D points."""
    return tuple((a + b) / 2 for a, b in zip(p1, p2))

def transform_point(point: Vec3, transform_matrix: Matrix) -> Vec3:
    """Apply a transformation matrix to a point."""
    vec = Vector((point[0], point[1], point[2], 1.0))
    transformed = transform_matrix @ vec
    return (transformed.x, transformed.y, transformed.z)

def bounding_box(points) -> Tuple[Vec3, Vec3]:
    """Calculate the bounding box of a set of points.
    
    Returns:
        Tuple of (min_point, max_point)
    """
    if not points:
        return ((0, 0, 0), (0, 0, 0))
    
    min_co = [float('inf')] * 3
    max_co = [-float('inf')] * 3
    
    for point in points:
        for i in range(3):
            min_co[i] = min(min_co[i], point[i])
            max_co[i] = max(max_co[i], point[i])
    
    return tuple(min_co), tuple(max_co)

def center_of_mass(points) -> Vec3:
    """Calculate the center of mass of a set of points."""
    if not points:
        return (0, 0, 0)
    
    sum_x = sum(p[0] for p in points)
    sum_y = sum(p[1] for p in points)
    sum_z = sum(p[2] for p in points)
    n = len(points)
    
    return (sum_x / n, sum_y / n, sum_z / n)

def get_proj4_string(srid: str) -> Optional[str]:
    """Get the proj4 string for a given EPSG code."""
    return EPSG_PROJ4.get(srid.upper())

def convert_units(value: float, from_units: str, to_units: str) -> float:
    """Convert between different units.
    
    Args:
        value: The value to convert
        from_units: Source units (e.g., 'm', 'mm', 'ft')
        to_units: Target units
        
    Returns:
        The converted value
    """
    # Conversion factors to meters
    to_meters = {
        'm': 1.0,
        'cm': 0.01,
        'mm': 0.001,
        'ft': 0.3048,
        'in': 0.0254,
        'yd': 0.9144,
        'mi': 1609.344,
        'km': 1000.0,
    }
    
    # Convert to meters first
    meters = value * to_meters.get(from_units.lower(), 1.0)
    
    # Then convert to target units
    if to_units.lower() in to_meters:
        return meters / to_meters[to_units.lower()]
    return value  # Return original if units not recognized
