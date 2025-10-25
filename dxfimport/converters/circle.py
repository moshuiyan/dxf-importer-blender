""
Converters for DXF circular entities.

This module provides converters for CIRCLE and ARC entities.
"""

import bpy
import math
import mathutils
from mathutils import Vector, Matrix
from typing import List, Optional, Tuple, Dict, Any

from .base import BaseConverter, ConversionOptions

# Type aliases
Vec3 = Tuple[float, float, float]

@BaseConverter.register_converter('CIRCLE')
class CircleConverter(BaseConverter):
    """Converter for DXF CIRCLE entities."""
    
    def convert(self, collection, parent=None, **kwargs) -> List[bpy.types.Object]:
        """Convert a DXF CIRCLE to a Blender curve."""
        # Get circle parameters
        center = self.transform_point(self.entity.dxf.center)
        radius = self.entity.dxf.radius * self.options.scale
        
        # Skip invalid circles
        if radius <= 0 or math.isinf(radius) or math.isnan(radius):
            return []
        
        # Create a new curve data
        curve_data = bpy.data.curves.new(f"Circle_{self.entity.dxf.handle}", 'CURVE')
        curve_data.dimensions = '3D'
        
        # Create a new spline for the circle
        spline = curve_data.splines.new('NURBS')
        spline.use_cyclic_u = True
        spline.use_endpoint_u = True
        spline.order_u = 3
        
        # Calculate points on the circle
        segments = self.options.curve_segments
        points = []
        
        for i in range(segments + 1):
            angle = 2.0 * math.pi * i / segments
            x = center[0] + radius * math.cos(angle)
            y = center[1] + radius * math.sin(angle)
            points.append((x, y, center[2], 1.0))
        
        # Set the points
        spline.points.add(segments)  # segments points (0 to segments-1)
        for i, point in enumerate(points):
            spline.points[i].co = point
        
        # Create object
        obj = self.create_object(
            curve_data,
            f"Circle_{self.entity.dxf.handle}",
            collection,
            parent=parent,
            **self.get_object_attributes()
        )
        
        return [obj]
    
    def get_object_attributes(self) -> Dict[str, Any]:
        """Get attributes for the Blender object."""
        return {
            'dxf_type': 'CIRCLE',
            'dxf_handle': self.entity.dxf.handle,
            'dxf_layer': self.entity.dxf.layer,
            'dxf_radius': self.entity.dxf.radius,
        }

@BaseConverter.register_converter('ARC')
class ArcConverter(BaseConverter):
    """Converter for DXF ARC entities."""
    
    def convert(self, collection, parent=None, **kwargs) -> List[bpy.types.Object]:
        """Convert a DXF ARC to a Blender curve."""
        # Get arc parameters
        center = self.transform_point(self.entity.dxf.center)
        radius = self.entity.dxf.radius * self.options.scale
        start_angle = math.radians(self.entity.dxf.start_angle)
        end_angle = math.radians(self.entity.dxf.end_angle)
        
        # Handle angle wrapping
        if end_angle <= start_angle:
            end_angle += 2.0 * math.pi
        
        # Skip invalid arcs
        if radius <= 0 or math.isinf(radius) or math.isnan(radius):
            return []
        
        # Create a new curve data
        curve_data = bpy.data.curves.new(f"Arc_{self.entity.dxf.handle}", 'CURVE')
        curve_data.dimensions = '3D'
        
        # Create a new spline for the arc
        spline = curve_data.splines.new('NURBS')
        spline.use_cyclic_u = False
        spline.use_endpoint_u = True
        spline.order_u = 3
        
        # Calculate points on the arc
        segments = self.options.curve_segments
        angle_range = end_angle - start_angle
        points = []
        
        for i in range(segments + 1):
            t = i / segments
            angle = start_angle + t * angle_range
            x = center[0] + radius * math.cos(angle)
            y = center[1] + radius * math.sin(angle)
            points.append((x, y, center[2], 1.0))
        
        # Set the points
        spline.points.add(segments)  # segments points (0 to segments-1)
        for i, point in enumerate(points):
            spline.points[i].co = point
        
        # Create object
        obj = self.create_object(
            curve_data,
            f"Arc_{self.entity.dxf.handle}",
            collection,
            parent=parent,
            **self.get_object_attributes()
        )
        
        return [obj]
    
    def get_object_attributes(self) -> Dict[str, Any]:
        """Get attributes for the Blender object."""
        return {
            'dxf_type': 'ARC',
            'dxf_handle': self.entity.dxf.handle,
            'dxf_layer': self.entity.dxf.layer,
            'dxf_radius': self.entity.dxf.radius,
            'dxf_start_angle': self.entity.dxf.start_angle,
            'dxf_end_angle': self.entity.dxf.end_angle,
        }
