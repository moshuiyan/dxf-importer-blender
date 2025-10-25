""
Converters for DXF line and point entities.

This module provides converters for LINE and POINT entities.
"""

import bpy
import bmesh
from mathutils import Vector
from typing import List, Optional, Tuple, Dict, Any

from .base import BaseConverter, ConversionOptions

# Type aliases
Vec3 = Tuple[float, float, float]

@BaseConverter.register_converter('LINE')
class LineConverter(BaseConverter):
    """Converter for DXF LINE entities."""
    
    def convert(self, collection, parent=None, **kwargs) -> List[bpy.types.Object]:
        """Convert a DXF LINE to a Blender curve."""
        # Get line vertices
        start = self.transform_point(self.entity.dxf.start)
        end = self.transform_point(self.entity.dxf.end)
        
        # Skip zero-length lines
        if Vector(start).length < 1e-6 or Vector(end).length < 1e-6:
            return []
        
        # Create a new curve data
        curve_data = bpy.data.curves.new(f"Line_{self.entity.dxf.handle}", 'CURVE')
        curve_data.dimensions = '3D'
        
        # Create a new spline
        polyline = curve_data.splines.new('POLY')
        polyline.points.add(1)  # Add one point (will have 2 points total)
        
        # Set the points
        polyline.points[0].co = (*start, 1.0)
        polyline.points[1].co = (*end, 1.0)
        
        # Create object
        obj = self.create_object(
            curve_data,
            f"Line_{self.entity.dxf.handle}",
            collection,
            parent=parent,
            **self.get_object_attributes()
        )
        
        return [obj]
    
    def get_object_attributes(self) -> Dict[str, Any]:
        """Get attributes for the Blender object."""
        attrs = {
            'dxf_type': 'LINE',
            'dxf_handle': self.entity.dxf.handle,
            'dxf_layer': self.entity.dxf.layer,
        }
        
        # Add color if specified
        if hasattr(self.entity.dxf, 'color'):
            attrs['color'] = self.get_dxf_color(self.entity.dxf.color)
            
        return attrs
    
    def get_dxf_color(self, color_index: int) -> Tuple[float, float, float, float]:
        """Convert DXF color index to Blender color."""
        # Default color (white)
        if color_index < 0 or color_index > 255:
            return (1.0, 1.0, 1.0, 1.0)
            
        # Get RGB values from DXF color index (0-255)
        # This is a simplified mapping - you may want to use a more accurate color table
        r = min(1.0, (color_index % 7) / 6.0)
        g = min(1.0, ((color_index + 3) % 7) / 6.0)
        b = min(1.0, ((color_index + 5) % 7) / 6.0)
        
        return (r, g, b, 1.0)


@BaseConverter.register_converter('POINT')
class PointConverter(BaseConverter):
    """Converter for DXF POINT entities."""
    
    def convert(self, collection, parent=None, **kwargs) -> List[bpy.types.Object]:
        """Convert a DXF POINT to a Blender mesh object."""
        # Get point position
        pos = self.transform_point(self.entity.dxf.location)
        
        # Create a new mesh and object
        mesh = bpy.data.meshes.new(f"Point_{self.entity.dxf.handle}")
        obj = bpy.data.objects.new(f"Point_{self.entity.dxf.handle}", mesh)
        
        # Create a single vertex at the point location
        bm = bmesh.new()
        bm.verts.new(pos)
        bm.to_mesh(mesh)
        bm.free()
        
        # Set object properties
        obj.location = pos
        obj.dxf_type = 'POINT'
        obj.dxf_handle = self.entity.dxf.handle
        obj.dxf_layer = self.entity.dxf.layer
        
        # Link to collection and set parent
        if collection:
            collection.objects.link(obj)
        if parent:
            obj.parent = parent
        
        return [obj]
